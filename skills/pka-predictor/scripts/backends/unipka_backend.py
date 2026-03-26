#!/usr/bin/env python3
"""
Uni-pKa 单文件权重后端（正式版）

基于 Bohrium notebook 的 single-weight pipeline，而不是 GitHub 仓库中的 infer_pka.sh 5-fold 流程。
"""

import os
import sys
import math
import logging
import warnings
import argparse
from collections import OrderedDict, defaultdict
from typing import Dict, List, Optional, Any, Tuple, Union, Callable

import numpy as np
import pandas as pd
from scipy.spatial import distance_matrix

import torch
from torch import nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader

from rdkit import Chem
from rdkit import RDLogger
from rdkit.Chem import (
    Mol,
    RWMol,
    AddHs,
    RemoveHs,
    SanitizeMol,
    MolToSmiles,
    MolFromSmiles,
    MolFromSmarts,
    CanonSmiles,
    GetFormalCharge,
    AllChem,
)

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.dirname(CURRENT_DIR)
SKILL_ROOT = os.path.dirname(SCRIPTS_DIR)
UNIPKA_ROOT = os.path.join(SKILL_ROOT, "assets", "Uni-pKa")

sys.path.insert(0, UNIPKA_ROOT)
sys.path.insert(0, os.path.join(UNIPKA_ROOT, "unimol"))
sys.path.insert(0, os.path.join(UNIPKA_ROOT, "unimol", "models"))

from transformer_encoder_with_pair import TransformerEncoderWithPair  # noqa: E402
from utils.mol_utils import smiles_to_mol, calculate_descriptors  # noqa: E402

RDLogger.DisableLog("rdApp.*")
warnings.filterwarnings(action="ignore")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=os.environ.get("LOGLEVEL", "INFO").upper(),
    stream=sys.stdout,
)
logger = logging.getLogger("unipka_single_weight.inference")
logging.disable(50)

LN10 = math.log(10)
TRANSLATE_PH = 6.504894871171601

DICT = """[PAD]
[CLS]
[SEP]
[UNK]
C
N
O
S
H
Cl
F
Br
I
Si
P
B
Na
K
Al
Ca
Sn
As
Hg
Fe
Zn
Cr
Se
Gd
Au
Li"""

DICT_CHARGE = """[PAD]
[CLS]
[SEP]
[UNK]
1
0
-1"""


class Dictionary:
    def __init__(self, *, bos="[CLS]", pad="[PAD]", eos="[SEP]", unk="[UNK]", extra_special_symbols=None):
        self.bos_word, self.unk_word, self.pad_word, self.eos_word = bos, unk, pad, eos
        self.symbols = []
        self.count = []
        self.indices = {}
        self.specials = set()
        self.specials.add(bos)
        self.specials.add(unk)
        self.specials.add(pad)
        self.specials.add(eos)

    def __getitem__(self, idx):
        if idx < len(self.symbols):
            return self.symbols[idx]
        return self.unk_word

    def __len__(self):
        return len(self.symbols)

    def __contains__(self, sym):
        return sym in self.indices

    def index(self, sym):
        assert isinstance(sym, str)
        if sym in self.indices:
            return self.indices[sym]
        return self.indices[self.unk_word]

    def add_symbol(self, word, n=1, overwrite=False, is_special=False):
        if is_special:
            self.specials.add(word)
        if word in self.indices and not overwrite:
            idx = self.indices[word]
            self.count[idx] = self.count[idx] + n
            return idx
        else:
            idx = len(self.symbols)
            self.indices[word] = idx
            self.symbols.append(word)
            self.count.append(n)
            return idx

    def bos(self):
        return self.index(self.bos_word)

    def pad(self):
        return self.index(self.pad_word)

    def eos(self):
        return self.index(self.eos_word)

    @classmethod
    def load_from_str(cls, s):
        d = cls()
        d.add_from_lines(s.split("\n"))
        return d

    def add_from_lines(self, lines):
        for line_idx, line in enumerate(lines):
            if not line.strip():
                continue
            splits = line.rstrip().rsplit(" ", 1)
            line = splits[0]
            field = splits[1] if len(splits) > 1 else str(len(lines) - line_idx)
            overwrite = False if field != "#overwrite" else True
            if overwrite:
                line, field = line.rsplit(" ", 1)
            count = int(field)
            self.add_symbol(line, n=count, overwrite=overwrite)


BACKBONE = {"transformer": TransformerEncoderWithPair}


def molecule_architecture():
    args = argparse.Namespace()
    args.encoder_layers = 15
    args.encoder_embed_dim = 512
    args.encoder_ffn_embed_dim = 2048
    args.encoder_attention_heads = 64
    args.dropout = 0.1
    args.emb_dropout = 0.1
    args.attention_dropout = 0.1
    args.activation_dropout = 0.0
    args.pooler_dropout = 0.0
    args.max_seq_len = 512
    args.activation_fn = "gelu"
    args.pooler_activation_fn = "tanh"
    args.post_ln = False
    args.backbone = "transformer"
    args.kernel = "gaussian"
    args.delta_pair_repr_norm_loss = -1.0
    return args


def pad_1d_tokens(values, pad_idx, left_pad=False, pad_to_length=None, pad_to_multiple=1):
    size = max(v.size(0) for v in values)
    size = size if pad_to_length is None else max(size, pad_to_length)
    if pad_to_multiple != 1 and size % pad_to_multiple != 0:
        size = int(((size - 0.1) // pad_to_multiple + 1) * pad_to_multiple)
    res = values[0].new(len(values), size).fill_(pad_idx)

    for i, v in enumerate(values):
        res[i][size - len(v):] if left_pad else res[i][:len(v)]
        dst = res[i][size - len(v):] if left_pad else res[i][:len(v)]
        dst.copy_(v)
    return res


def pad_2d(values, pad_idx, left_pad=False, pad_to_length=None, pad_to_multiple=1):
    size = max(v.size(0) for v in values)
    size = size if pad_to_length is None else max(size, pad_to_length)
    if pad_to_multiple != 1 and size % pad_to_multiple != 0:
        size = int(((size - 0.1) // pad_to_multiple + 1) * pad_to_multiple)
    res = values[0].new(len(values), size, size).fill_(pad_idx)

    for i, v in enumerate(values):
        dst = res[i][size - len(v):, size - len(v):] if left_pad else res[i][:len(v), :len(v)]
        dst.copy_(v)
    return res


def pad_coords(values, pad_idx, left_pad=False, pad_to_length=None, pad_to_multiple=1):
    size = max(v.size(0) for v in values)
    size = size if pad_to_length is None else max(size, pad_to_length)
    if pad_to_multiple != 1 and size % pad_to_multiple != 0:
        size = int(((size - 0.1) // pad_to_multiple + 1) * pad_to_multiple)
    res = values[0].new(len(values), size, 3).fill_(pad_idx)

    for i, v in enumerate(values):
        dst = res[i][size - len(v):, :] if left_pad else res[i][:len(v), :]
        dst.copy_(v)
    return res


def get_activation_fn(activation):
    if activation == "relu":
        return F.relu
    elif activation == "gelu":
        return F.gelu
    elif activation == "tanh":
        return torch.tanh
    elif activation == "linear":
        return lambda x: x
    raise RuntimeError(f"--activation-fn {activation} not supported")


@torch.jit.script
def gaussian(x, mean, std):
    pi = 3.14159
    a = (2 * pi) ** 0.5
    return torch.exp(-0.5 * (((x - mean) / std) ** 2)) / (a * std)


class NonLinearHead(nn.Module):
    def __init__(self, input_dim, out_dim, activation_fn, hidden=None):
        super().__init__()
        hidden = input_dim if not hidden else hidden
        self.linear1 = nn.Linear(input_dim, hidden)
        self.linear2 = nn.Linear(hidden, out_dim)
        self.activation_fn = get_activation_fn(activation_fn)

    def forward(self, x):
        x = self.linear1(x)
        x = self.activation_fn(x)
        x = self.linear2(x)
        return x


class GaussianLayer(nn.Module):
    def __init__(self, K=128, edge_types=1024):
        super().__init__()
        self.K = K
        self.means = nn.Embedding(1, K)
        self.stds = nn.Embedding(1, K)
        self.mul = nn.Embedding(edge_types, 1)
        self.bias = nn.Embedding(edge_types, 1)
        nn.init.uniform_(self.means.weight, 0, 3)
        nn.init.uniform_(self.stds.weight, 0, 3)
        nn.init.constant_(self.bias.weight, 0)
        nn.init.constant_(self.mul.weight, 1)

    def forward(self, x, edge_type):
        mul = self.mul(edge_type).type_as(x)
        bias = self.bias(edge_type).type_as(x)
        x = mul * x.unsqueeze(-1) + bias
        x = x.expand(-1, -1, -1, self.K)
        mean = self.means.weight.float().view(-1)
        std = self.stds.weight.float().view(-1).abs() + 1e-5
        return gaussian(x.float(), mean, std).type_as(self.means.weight)


class ClassificationHead(nn.Module):
    def __init__(self, input_dim, inner_dim, num_classes, activation_fn, pooler_dropout):
        super().__init__()
        self.dense = nn.Linear(input_dim, inner_dim)
        self.activation_fn = get_activation_fn(activation_fn)
        self.dropout = nn.Dropout(p=pooler_dropout)
        self.out_proj = nn.Linear(inner_dim, num_classes)

    def forward(self, features, **kwargs):
        x = features
        x = self.dropout(x)
        x = self.dense(x)
        x = self.activation_fn(x)
        x = self.dropout(x)
        x = self.out_proj(x)
        return x


class UniMolModel(nn.Module):
    def __init__(self, model_path, output_dim=2, **params):
        super().__init__()
        self.args = molecule_architecture()
        self.output_dim = output_dim
        self.remove_hs = params.get("remove_hs", False)
        self.pretrain_path = model_path
        self.head_name = params.get("head_name", "chembl_all")

        self.dictionary = Dictionary.load_from_str(DICT)
        self.mask_idx = self.dictionary.add_symbol("[MASK]", is_special=True)
        self.padding_idx = self.dictionary.pad()
        self.embed_tokens = nn.Embedding(len(self.dictionary), self.args.encoder_embed_dim, self.padding_idx)

        self.charge_dictionary = Dictionary.load_from_str(DICT_CHARGE)
        self.charge_mask_idx = self.charge_dictionary.add_symbol("[MASK]", is_special=True)
        self.charge_padding_idx = self.charge_dictionary.pad()
        self.embed_charges = nn.Embedding(len(self.charge_dictionary), self.args.encoder_embed_dim, self.charge_padding_idx)

        self.encoder = BACKBONE[self.args.backbone](
            encoder_layers=self.args.encoder_layers,
            embed_dim=self.args.encoder_embed_dim,
            ffn_embed_dim=self.args.encoder_ffn_embed_dim,
            attention_heads=self.args.encoder_attention_heads,
            emb_dropout=self.args.emb_dropout,
            dropout=self.args.dropout,
            attention_dropout=self.args.attention_dropout,
            activation_dropout=self.args.activation_dropout,
            max_seq_len=self.args.max_seq_len,
            activation_fn=self.args.activation_fn,
            no_final_head_layer_norm=self.args.delta_pair_repr_norm_loss < 0,
        )

        K = 128
        n_edge_type = len(self.dictionary) * len(self.dictionary)
        self.gbf_proj = NonLinearHead(K, self.args.encoder_attention_heads, self.args.activation_fn)
        self.gbf = GaussianLayer(K, n_edge_type)

        self.classification_heads = nn.ModuleDict()
        self.classification_heads[self.head_name] = ClassificationHead(
            input_dim=self.args.encoder_embed_dim,
            inner_dim=self.args.encoder_embed_dim,
            num_classes=self.output_dim,
            activation_fn=self.args.pooler_activation_fn,
            pooler_dropout=self.args.pooler_dropout,
        )

        self.load_pretrained_weights(path=self.pretrain_path)

    def load_pretrained_weights(self, path):
        if path is not None:
            logger.info(f"Loading pretrained weights from {path}")
            try:
                state_dict = torch.load(path, map_location="cpu", weights_only=False)
            except TypeError:
                state_dict = torch.load(path, map_location="cpu")

            if isinstance(state_dict, dict) and "model" in state_dict:
                errors = self.load_state_dict(state_dict["model"], strict=True)
                if getattr(errors, "missing_keys", None):
                    logger.warning(f"missing_keys: {errors.missing_keys}")
                if getattr(errors, "unexpected_keys", None):
                    logger.warning(f"unexpected_keys: {errors.unexpected_keys}")
            else:
                raise ValueError("checkpoint 不包含 'model' 键，无法按 notebook 方式加载")

    def forward(self, src_tokens, src_charges, src_distance, src_coord, src_edge_type, **kwargs):
        padding_mask = src_tokens.eq(self.padding_idx)
        if not padding_mask.any():
            padding_mask = None

        x = self.embed_tokens(src_tokens)

        charge_padding_mask = src_charges.eq(self.charge_padding_idx)
        if not charge_padding_mask.any():
            padding_mask = None

        charges_emb = self.embed_charges(src_charges)
        x += charges_emb

        def get_dist_features(dist, et):
            n_node = dist.size(-1)
            gbf_feature = self.gbf(dist, et)
            gbf_result = self.gbf_proj(gbf_feature)
            graph_attn_bias = gbf_result.permute(0, 3, 1, 2).contiguous()
            graph_attn_bias = graph_attn_bias.view(-1, n_node, n_node)
            return graph_attn_bias

        graph_attn_bias = get_dist_features(src_distance, src_edge_type)
        encoder_rep, _, _, _, _ = self.encoder(x, padding_mask=padding_mask, attn_mask=graph_attn_bias)

        cls_repr = encoder_rep[:, 0, :]
        logits = self.classification_heads[self.head_name](cls_repr)
        return logits

    def batch_collate_fn(self, samples):
        batch = {}
        for k in samples[0][0].keys():
            if k == "src_coord":
                v = pad_coords([torch.tensor(s[0][k]).float() for s in samples], pad_idx=0.0)
            elif k == "src_edge_type":
                v = pad_2d([torch.tensor(s[0][k]).long() for s in samples], pad_idx=self.padding_idx)
            elif k == "src_distance":
                v = pad_2d([torch.tensor(s[0][k]).float() for s in samples], pad_idx=0.0)
            elif k == "src_tokens":
                v = pad_1d_tokens([torch.tensor(s[0][k]).long() for s in samples], pad_idx=self.padding_idx)
            elif k == "src_charges":
                v = pad_1d_tokens([torch.tensor(s[0][k]).long() for s in samples], pad_idx=self.charge_padding_idx)
            else:
                continue
            batch[k] = v

        try:
            label = torch.tensor([s[1] for s in samples])
        except Exception:
            label = None
        return batch, label


class MolDataset(Dataset):
    def __init__(self, data, label=None):
        self.data = data
        self.label = label if label is not None else np.zeros((len(data), 1))

    def __getitem__(self, idx):
        return self.data[idx], self.label[idx]

    def __len__(self):
        return len(self.data)


def inner_smi2coords(smi, seed=42, mode="fast", remove_hs=True):
    mol = Chem.MolFromSmiles(smi)
    mol = AllChem.AddHs(mol)
    atoms, charges = [], []
    for atom in mol.GetAtoms():
        atoms.append(atom.GetSymbol())
        charges.append(atom.GetFormalCharge())
    assert len(atoms) > 0, f"No atoms in molecule: {smi}"

    try:
        res = AllChem.EmbedMolecule(mol, randomSeed=seed)
        if res == 0:
            try:
                AllChem.MMFFOptimizeMolecule(mol)
                coordinates = mol.GetConformer().GetPositions().astype(np.float32)
            except Exception:
                coordinates = mol.GetConformer().GetPositions().astype(np.float32)
        elif res == -1 and mode == "heavy":
            AllChem.EmbedMolecule(mol, maxAttempts=5000, randomSeed=seed)
            try:
                AllChem.MMFFOptimizeMolecule(mol)
                coordinates = mol.GetConformer().GetPositions().astype(np.float32)
            except Exception:
                AllChem.Compute2DCoords(mol)
                coordinates = mol.GetConformer().GetPositions().astype(np.float32)
        else:
            AllChem.Compute2DCoords(mol)
            coordinates = mol.GetConformer().GetPositions().astype(np.float32)
    except Exception:
        coordinates = np.zeros((len(atoms), 3))

    assert len(atoms) == len(coordinates), f"coordinates shape is not align with {smi}"

    if remove_hs:
        idx = [i for i, atom in enumerate(atoms) if atom != "H"]
        atoms_no_h = [atom for atom in atoms if atom != "H"]
        coordinates_no_h = coordinates[idx]
        charges_no_h = [charges[i] for i in idx]
        return atoms_no_h, coordinates_no_h, charges_no_h
    else:
        return atoms, coordinates, charges


def inner_coords(atoms, coordinates, charges, remove_hs=True):
    assert len(atoms) == len(coordinates), "coordinates shape is not align atoms"
    coordinates = np.array(coordinates).astype(np.float32)
    if remove_hs:
        idx = [i for i, atom in enumerate(atoms) if atom != "H"]
        atoms_no_h = [atom for atom in atoms if atom != "H"]
        coordinates_no_h = coordinates[idx]
        charges_no_h = [charges[i] for i in idx]
        return atoms_no_h, coordinates_no_h, charges_no_h
    else:
        return atoms, coordinates, charges


def coords2unimol(atoms, coordinates, charges, dictionary, charge_dictionary, max_atoms=256, remove_hs=True):
    atoms, coordinates, charges = inner_coords(atoms, coordinates, charges, remove_hs=remove_hs)
    atoms = np.array(atoms)
    coordinates = np.array(coordinates).astype(np.float32)
    charges = np.array(charges).astype(str)

    if len(atoms) > max_atoms:
        idx = np.random.choice(len(atoms), max_atoms, replace=False)
        atoms = atoms[idx]
        coordinates = coordinates[idx]
        charges = charges[idx]

    src_tokens = np.array([dictionary.bos()] + [dictionary.index(atom) for atom in atoms] + [dictionary.eos()])
    src_charges = np.array([charge_dictionary.bos()] + [charge_dictionary.index(charge) for charge in charges] + [charge_dictionary.eos()])

    src_coord = coordinates - coordinates.mean(axis=0)
    src_coord = np.concatenate([np.zeros((1, 3)), src_coord, np.zeros((1, 3))], axis=0)
    src_distance = distance_matrix(src_coord, src_coord)
    src_edge_type = src_tokens.reshape(-1, 1) * len(dictionary) + src_tokens.reshape(1, -1)

    return {
        "src_tokens": src_tokens.astype(int),
        "src_charges": src_charges.astype(int),
        "src_distance": src_distance.astype(np.float32),
        "src_coord": src_coord.astype(np.float32),
        "src_edge_type": src_edge_type.astype(int),
    }


class ConformerGen(object):
    def __init__(self, **params):
        self.seed = params.get("seed", 42)
        self.max_atoms = params.get("max_atoms", 256)
        self.method = params.get("method", "rdkit_random")
        self.mode = params.get("mode", "fast")
        self.remove_hs = params.get("remove_hs", False)
        self.dictionary = Dictionary.load_from_str(DICT)
        self.dictionary.add_symbol("[MASK]", is_special=True)
        self.charge_dictionary = Dictionary.load_from_str(DICT_CHARGE)
        self.charge_dictionary.add_symbol("[MASK]", is_special=True)

    def single_process(self, smiles):
        if self.method != "rdkit_random":
            raise ValueError(f"Unknown conformer generation method: {self.method}")

        atoms, coordinates, charges = inner_smi2coords(
            smiles, seed=self.seed, mode=self.mode, remove_hs=self.remove_hs
        )
        return coords2unimol(
            atoms, coordinates, charges,
            self.dictionary, self.charge_dictionary,
            self.max_atoms, remove_hs=self.remove_hs,
        )

    def transform(self, smiles_list):
        return [self.single_process(item) for item in smiles_list]


class FreeEnergyPredictor(object):
    def __init__(self, model_path, batch_size=32, remove_hs=False, use_gpu=True, head_name="chembl_all"):
        self.device = torch.device("cuda:0" if torch.cuda.is_available() and use_gpu else "cpu")
        self.model = UniMolModel(
            model_path,
            output_dim=1,
            remove_hs=remove_hs,
            head_name=head_name,
        ).to(self.device)
        self.model.eval()
        self.batch_size = batch_size
        self.params = {"remove_hs": remove_hs}
        self.conformer_gen = ConformerGen(**self.params)

    def preprocess_data(self, smiles_list):
        return self.conformer_gen.transform(smiles_list)

    def decorate_torch_batch(self, batch):
        net_input, net_target = batch
        if isinstance(net_input, dict):
            net_input = {k: v.to(self.device) for k, v in net_input.items()}
            if net_target is not None:
                net_target = net_target.to(self.device)
        else:
            net_input = {"net_input": net_input.to(self.device)}
            if net_target is not None:
                net_target = net_target.to(self.device)
        net_target = None
        return net_input, net_target

    def predict(self, smiles_list):
        unimol_input = self.preprocess_data(smiles_list)
        dataset = MolDataset(unimol_input)
        dataloader = DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=False,
            collate_fn=self.model.batch_collate_fn,
        )

        results = {}
        idx_offset = 0
        for batch in dataloader:
            net_input, _ = self.decorate_torch_batch(batch)
            with torch.no_grad():
                predictions = self.model(**net_input)
                bs = predictions.shape[0]
                batch_smiles = smiles_list[idx_offset: idx_offset + bs]
                for smiles, energy in zip(batch_smiles, predictions):
                    results[smiles] = float(energy.item())
                idx_offset += bs
        return results


FILTER_PATTERNS = list(map(MolFromSmarts, [
    "[#6X5]",
    "[#7X5]",
    "[#8X4]",
    "[*r]=[*r]=[*r]",
    "[#1]-[*+1]~[*-1]",
    "[#1]-[*+1]=,:[*]-,:[*-1]",
    "[#1]-[*+1]-,:[*]=,:[*-1]",
    "[*+2]",
    "[*-2]",
    "[#1]-[#8+1].[#8-1,#7-1,#6-1]",
    "[#1]-[#7+1,#8+1].[#7-1,#6-1]",
    "[#1]-[#8+1].[#8-1,#6-1]",
    "[#1]-[#7+1].[#8-1]-[C](-[C,#1])(-[C,#1])",
    "[OX1]=[C]-[OH2+1]",
    "[NX1,NX2H1,NX3H2]=[C]-[O]-[H]",
    "[#6-1]=[*]-[*]",
    "[cX2-1]",
    "[N+1](=O)-[O]-[H]",
]))


def sanitize_checker(smi: str, filter_patterns: List[Mol] = FILTER_PATTERNS) -> bool:
    try:
        mol = MolFromSmiles(smi)
        if mol is None:
            return False
        for patt in filter_patterns:
            if patt is not None and mol.HasSubstructMatch(patt):
                return False
        return True
    except Exception:
        return False


def sanitize_filter(smis: List[str], filter_patterns: List[Mol] = FILTER_PATTERNS) -> List[str]:
    return list(filter(lambda smi: sanitize_checker(smi, filter_patterns), smis))


def cnt_stereo_atom(smi: str) -> int:
    mol = MolFromSmiles(smi)
    return sum([str(atom.GetChiralTag()) != "CHI_UNSPECIFIED" for atom in mol.GetAtoms()])


def stereo_filter(smis: List[str]) -> List[str]:
    filtered_smi_dict = {}
    for smi in smis:
        nonstereo_smi = CanonSmiles(smi, useChiral=0)
        stereo_cnt = cnt_stereo_atom(smi)
        if nonstereo_smi not in filtered_smi_dict:
            filtered_smi_dict[nonstereo_smi] = (smi, stereo_cnt)
        else:
            if stereo_cnt > filtered_smi_dict[nonstereo_smi][1]:
                filtered_smi_dict[nonstereo_smi] = (smi, stereo_cnt)
    return [value[0] for value in filtered_smi_dict.values()]


def make_filter(filter_param: OrderedDict) -> Callable:
    def seq_filter(smis):
        for single_filter, param in filter_param.items():
            smis = single_filter(smis, **param)
        return smis
    return seq_filter


def prot(mol: Mol, idx: int, mode: str) -> Mol:
    mw = RWMol(mol)
    if mode == "a2b":
        atom_H = mw.GetAtomWithIdx(idx)
        if atom_H.GetAtomicNum() == 1:
            atom_A = atom_H.GetNeighbors()[0]
            atom_A.SetFormalCharge(atom_A.GetFormalCharge() - 1)
            mw.RemoveAtom(idx)
            mol_prot = mw.GetMol()
        else:
            atom_H.SetFormalCharge(atom_H.GetFormalCharge() - 1)
            atom_H.SetNumExplicitHs(atom_H.GetTotalNumHs() - 1)
            atom_H.UpdatePropertyCache()
            mol_prot = AddHs(mw)
    elif mode == "b2a":
        atom_B = mw.GetAtomWithIdx(idx)
        atom_B.SetFormalCharge(atom_B.GetFormalCharge() + 1)
        atom_B.SetNumExplicitHs(atom_B.GetNumExplicitHs() + 1)
        mol_prot = AddHs(mw)
    else:
        raise ValueError(f"Unknown mode: {mode}")

    SanitizeMol(mol_prot)
    mol_prot = MolFromSmiles(MolToSmiles(mol_prot, canonical=False))
    mol_prot = AddHs(mol_prot)
    return mol_prot


def match_template(template: pd.DataFrame, mol: Mol, verbose: bool = False) -> list:
    mol = AddHs(mol)
    matches = []
    for idx, name, smarts, index, acid_base in template.itertuples():
        pattern = MolFromSmarts(smarts)
        match = mol.GetSubstructMatches(pattern)
        if len(match) == 0:
            continue
        index = int(index)
        for m in match:
            matches.append(m[index])
            if verbose:
                print(f"find index {m[index]} in pattern {name} smarts {smarts}")
    return list(set(matches))


def prot_template(template: pd.DataFrame, smi: str, mode: str) -> Tuple[List[int], List[str]]:
    mol = MolFromSmiles(smi)
    sites = match_template(template, mol)
    smis = []
    for site in sites:
        smis.append(CanonSmiles(MolToSmiles(RemoveHs(prot(mol, site, mode)))))
    return sites, list(set(smis))


def read_template(template_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    template = pd.read_csv(template_file, sep="\t")
    template_a2b = template[template.Acid_or_base == "A"]
    template_b2a = template[template.Acid_or_base == "B"]
    return template_a2b, template_b2a


def enumerate_template(
    smi: Union[str, List[str]],
    template_a2b: pd.DataFrame,
    template_b2a: pd.DataFrame,
    mode: str = "A",
    maxiter: int = 10,
    filter_patterns: List[Mol] = FILTER_PATTERNS,
) -> Tuple[List[str], List[str]]:
    smis = [smi] if isinstance(smi, str) else list(smi)
    enum_func = lambda x: [x]

    if mode == "a2b":
        smis_A_pool, smis_B_pool = smis, []
    elif mode == "b2a":
        smis_A_pool, smis_B_pool = [], smis
    else:
        raise ValueError(f"Unknown mode: {mode}")

    filters = make_filter(OrderedDict({
        sanitize_filter: {"filter_patterns": filter_patterns},
        stereo_filter: {},
    }))

    pool_length_A = -1
    pool_length_B = -1
    i = 0

    while (len(smis_A_pool) != pool_length_A or len(smis_B_pool) != pool_length_B) and i < maxiter:
        pool_length_A, pool_length_B = len(smis_A_pool), len(smis_B_pool)

        if (mode == "a2b" and (i + 1) % 2) or (mode == "b2a" and i % 2):
            smis_A_tmp_pool = []
            for smi_item in smis_A_pool:
                smis_B_pool += filters(prot_template(template_a2b, smi_item, "a2b")[1])
                smis_A_tmp_pool += filters([CanonSmiles(MolToSmiles(mol)) for mol in enum_func(MolFromSmiles(smi_item))])
            smis_A_pool += smis_A_tmp_pool

        elif (mode == "b2a" and (i + 1) % 2) or (mode == "a2b" and i % 2):
            smis_B_tmp_pool = []
            for smi_item in smis_B_pool:
                smis_A_pool += filters(prot_template(template_b2a, smi_item, "b2a")[1])
                smis_B_tmp_pool += filters([CanonSmiles(MolToSmiles(mol)) for mol in enum_func(MolFromSmiles(smi_item))])
            smis_B_pool += smis_B_tmp_pool

        smis_A_pool = list(set(filters(smis_A_pool)))
        smis_B_pool = list(set(filters(smis_B_pool)))
        i += 1

    smis_A_pool = list(map(CanonSmiles, smis_A_pool))
    smis_B_pool = list(map(CanonSmiles, smis_B_pool))
    return smis_A_pool, smis_B_pool


def get_ensemble(
    smi: str,
    template_a2b: pd.DataFrame,
    template_b2a: pd.DataFrame,
    maxiter: int = 10,
) -> Dict[int, List[str]]:
    """
    安全收缩版：
    仅保留当前电荷态及其相邻电荷态，避免复杂分子在模板枚举时状态爆炸。
    """
    ensemble = {}
    q0 = GetFormalCharge(MolFromSmiles(smi))
    smi0 = CanonSmiles(smi)

    ensemble[q0] = [smi0]

    # 去质子化一步：q0 -> q0-1
    _, smis_b1 = enumerate_template(
        [smi0],
        template_a2b,
        template_b2a,
        maxiter=maxiter,
        mode="a2b"
    )
    if smis_b1:
        ensemble[q0 - 1] = list(set(map(CanonSmiles, smis_b1)))

    # 质子化一步：q0 -> q0+1
    smis_a1, _ = enumerate_template(
        [smi0],
        template_a2b,
        template_b2a,
        maxiter=maxiter,
        mode="b2a"
    )
    if smis_a1:
        ensemble[q0 + 1] = list(set(map(CanonSmiles, smis_a1)))

    return ensemble


def predict_ensemble_free_energy(smi: str, predictor: FreeEnergyPredictor, template_a2b: pd.DataFrame, template_b2a: pd.DataFrame) -> Dict[int, List[Tuple[str, float]]]:
    ensemble = get_ensemble(smi, template_a2b, template_b2a)
    ensemble_free_energy = {}
    for q, macrostate in ensemble.items():
        prediction = predictor.predict(macrostate)
        ensemble_free_energy[q] = [(microstate, prediction[microstate]) for microstate in macrostate]
    return ensemble_free_energy


def calc_distribution(ensemble_free_energy: Dict[int, List[Tuple[str, float]]], pH: float) -> Dict[int, List[Tuple[str, float]]]:
    ensemble_boltzmann_factor = defaultdict(list)
    partition_function = 0.0
    for q, macrostate_free_energy in ensemble_free_energy.items():
        for microstate, DfGm in macrostate_free_energy:
            boltzmann_factor = math.exp(-DfGm - q * LN10 * (pH - TRANSLATE_PH))
            partition_function += boltzmann_factor
            ensemble_boltzmann_factor[q].append((microstate, boltzmann_factor))

    return {
        q: [(microstate, boltzmann_factor / partition_function) for microstate, boltzmann_factor in macrostate_boltzmann_factor]
        for q, macrostate_boltzmann_factor in ensemble_boltzmann_factor.items()
    }


def log_sum_exp(DfGm: List[float]) -> float:
    return math.log10(sum([math.exp(-g) for g in DfGm]))


def predict_macro_pKa_from_macrostate(predictor: FreeEnergyPredictor, macrostate_A: List[str], macrostate_B: List[str]) -> float:
    DfGm_A = predictor.predict(macrostate_A)
    DfGm_B = predictor.predict(macrostate_B)
    return log_sum_exp(list(DfGm_A.values())) - log_sum_exp(list(DfGm_B.values())) + TRANSLATE_PH


def infer_transition_direction(from_charge: int, to_charge: int) -> str:
    if to_charge < from_charge:
        return "deprotonation"
    elif to_charge > from_charge:
        return "protonation"
    return "unknown"


class UniPKABackend:
    """
    Uni-pKa 单文件权重正式版后端
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        template_file: Optional[str] = None,
        batch_size: int = 32,
        remove_hs: bool = False,
        use_gpu: bool = True,
        head_name: str = "chembl_all",
        maxiter: int = 10,
    ):
        self.model_path = model_path or os.path.join(UNIPKA_ROOT, "uni-pka-ckpt_v2", "t_dwar_v_novartis_a_b.pt")
        self.template_file = template_file or os.path.join(UNIPKA_ROOT, "uni-pka-ckpt_v2", "simple_smarts_pattern.tsv")
        self.batch_size = batch_size
        self.remove_hs = remove_hs
        self.use_gpu = use_gpu
        self.head_name = head_name
        self.maxiter = maxiter

        self._validate_files()

        self.predictor = FreeEnergyPredictor(
            model_path=self.model_path,
            batch_size=self.batch_size,
            remove_hs=self.remove_hs,
            use_gpu=self.use_gpu,
            head_name=self.head_name,
        )
        self.template_a2b, self.template_b2a = read_template(self.template_file)

    def _validate_files(self):
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Uni-pKa 单文件权重不存在：{self.model_path}")
        if not os.path.exists(self.template_file):
            raise FileNotFoundError(f"Uni-pKa 模板文件不存在：{self.template_file}")

    def predict(self, smiles: str, name: str = "Unknown") -> Dict[str, Any]:
        mol = smiles_to_mol(smiles)
        if not mol:
            return {
                "name": name,
                "smiles": smiles,
                "status": "error",
                "backend_used": "unipka_single_weight",
                "error": "无效的 SMILES 格式",
            }

        try:
            #print("DEBUG: start canonicalization")
            smiles = CanonSmiles(smiles)
            descriptors = calculate_descriptors(smiles)
            #print("DEBUG: start get_ensemble")
            ensemble = get_ensemble(
                smi=smiles,
                template_a2b=self.template_a2b,
                template_b2a=self.template_b2a,
                maxiter=self.maxiter,
            )
            #print("DEBUG: ensemble done")
            #print("DEBUG: start predict_ensemble_free_energy")
            ensemble_free_energy = predict_ensemble_free_energy(
                smi=smiles,
                predictor=self.predictor,
                template_a2b=self.template_a2b,
                template_b2a=self.template_b2a,
            )
            #print("DEBUG: free energy done")
            
            charges_sorted = sorted(ensemble.keys(), reverse=True)
            all_macro_predictions = []

            for from_q, to_q in zip(charges_sorted[:-1], charges_sorted[1:]):
                macrostate_A = ensemble[from_q]
                macrostate_B = ensemble[to_q]
                #print("DEBUG: start macro pKa aggregation")
                macro_pka = predict_macro_pKa_from_macrostate(
                    predictor=self.predictor,
                    macrostate_A=macrostate_A,
                    macrostate_B=macrostate_B,
                )

                direction = infer_transition_direction(from_q, to_q)
                label = f"{from_q}->{to_q}"

                all_macro_predictions.append({
                    "from_charge": from_q,
                    "to_charge": to_q,
                    "label": label,
                    "direction": direction,
                    "site_type": "macro",
                    "pka": round(float(macro_pka), 4),
                    "confidence": None,
                    "macrostate_A_size": len(macrostate_A),
                    "macrostate_B_size": len(macrostate_B),
                })

            # 先找最常见、最易解释的主步骤：
            # 去质子化优先 0 -> -1
            # 质子化优先 0 -> +1

            dominant_cation_to_neutral_pka = None
            dominant_neutral_to_anion_pka = None

            cation_to_neutral = None
            neutral_to_anion = None

            for item in all_macro_predictions:
                pka_val = item.get("pka")
                if pka_val is None:
                    continue

                from_q = item["from_charge"]
                to_q = item["to_charge"]

                if from_q == 1 and to_q == 0:
                    cation_to_neutral = pka_val

                if from_q == 0 and to_q == -1:
                    neutral_to_anion = pka_val

            dominant_cation_to_neutral_pka = cation_to_neutral
            dominant_neutral_to_anion_pka = neutral_to_anion

            energy_summary = {
                int(q): [
                    {"smiles": micro, "free_energy": float(energy)}
                    for micro, energy in macrostate_list
                ]
                for q, macrostate_list in ensemble_free_energy.items()
            }

            return {
                "name": name,
                "smiles": smiles,
                "status": "success",
                "backend_used": "unipka_single_weight",
                "method": "Uni-pKa Bohrium single-weight pipeline",
                "results": {
                    "dominant_cation_to_neutral_pka": round(float(dominant_cation_to_neutral_pka), 4) if dominant_cation_to_neutral_pka is not None else None,
                    "dominant_neutral_to_anion_pka": round(float(dominant_neutral_to_anion_pka), 4) if dominant_neutral_to_anion_pka is not None else None,
                    "all_predictions": all_macro_predictions,
                },
                "functional_groups": None,
                "descriptors": descriptors,
                "metadata": {
                    "model_path": self.model_path,
                    "template_file": self.template_file,
                    "head_name": self.head_name,
                    "maxiter": self.maxiter,
                    "charge_states": sorted(list(ensemble.keys())),
                    "ensemble_sizes": {int(q): len(v) for q, v in ensemble.items()},
                    "ensemble_free_energy": energy_summary,
                },
            }

        except Exception as e:
            return {
                "name": name,
                "smiles": smiles,
                "status": "error",
                "backend_used": "unipka_single_weight",
                "method": "Uni-pKa Bohrium single-weight pipeline",
                "error": str(e),
            }

    def batch_predict(self, compounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for compound in compounds:
            smiles = compound.get("smiles", "")
            name = compound.get("name", "Unknown")
            results.append(self.predict(smiles, name))
        return results


def predict_pka_unipka(
    smiles: str,
    name: str = "Unknown",
    model_path: Optional[str] = None,
    template_file: Optional[str] = None,
    batch_size: int = 32,
    remove_hs: bool = False,
    use_gpu: bool = True,
    head_name: str = "chembl_all",
    maxiter: int = 10,
) -> Dict[str, Any]:
    backend = UniPKABackend(
        model_path=model_path,
        template_file=template_file,
        batch_size=batch_size,
        remove_hs=remove_hs,
        use_gpu=use_gpu,
        head_name=head_name,
        maxiter=maxiter,
    )
    return backend.predict(smiles, name)