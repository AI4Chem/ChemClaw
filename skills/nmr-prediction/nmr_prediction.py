#!/usr/bin/env python3
"""
NMRNet 液相 NMR 化学位移预测
输入: SMILES 字符串
输出: ¹H 和/或 ¹³C NMR 谱图 PNG + 化学位移列表 (ppm)

前置条件 (首次运行请先执行以下步骤，详见 SKILL.md):
  1. git clone https://github.com/Colin-Jay/NMRNet ~/Desktop/NMRNet
  2. cd ~/Desktop/Uni-Core && python setup.py install
  3. pip install -r requirements.txt
  4. 已通过 remotezip 下载 H/C 模型权重到 ~/Desktop/weights/
  5. python nmr_prediction.py --setup    # 下载 target_scaler.ss

用法:
  python nmr_prediction.py "CCO"                   # 预测乙醇的 1H+13C 谱
  python nmr_prediction.py "CCO" --nucleus H       # 只预测 1H 谱
  python nmr_prediction.py "c1ccccc1" --nucleus C  # 苯的 13C 谱
  python nmr_prediction.py --setup                 # 首次下载 scaler 文件
"""

import os
import sys
import argparse
import numpy as np

# ─── 路径配置 ──────────────────────────────────────────────────────────────────
_SKILL_DIR  = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR  = "/tmp/chemclaw"
ASSETS_DIR  = os.path.join(_SKILL_DIR, "assets")
NMRNET_DIR  = os.path.join(ASSETS_DIR, "NMRNet")       # assets/NMRNet/

_LIQ_BASE   = "/tmp/weights/finetune/liquid"
H_MODEL_DIR = os.path.join(
    _LIQ_BASE,
    "H_mol_pre_all_h_220816_global_0_kener_gauss_atomdes_0_unimol_large_atom_regloss_mae_lr_5e-3_bs_16_0.06_400",
)
C_MODEL_DIR = os.path.join(
    _LIQ_BASE,
    "C_mol_pre_all_h_220816_global_0_kener_gauss_atomdes_0_unimol_large_atom_regloss_mae_lr_1e-3_bs_16_0.06_200",
)
CHECKPOINT_REL = "cv_seed_42_fold_0/checkpoint_best.pt"

ZENODO_URL  = "https://zenodo.org/records/19142375/files/weights.zip?download=1"
_ZIP_LIQUID = "weights/finetune/liquid"
# H 和 C 的 scaler 均来自 Zenodo（demo/notebook/scaler 里的是固态 NMR scaler，不适用）
H_SCALER_ZIP = (
    f"{_ZIP_LIQUID}/H_mol_pre_all_h_220816_global_0_kener_gauss_atomdes_0"
    "_unimol_large_atom_regloss_mae_lr_5e-3_bs_16_0.06_400/target_scaler.ss"
)
C_SCALER_ZIP = (
    f"{_ZIP_LIQUID}/C_mol_pre_all_h_220816_global_0_kener_gauss_atomdes_0"
    "_unimol_large_atom_regloss_mae_lr_1e-3_bs_16_0.06_200/target_scaler.ss"
)


# ─── 环境检查 ──────────────────────────────────────────────────────────────────
def _ensure_nmrnet_in_path() -> None:
    if not os.path.isdir(NMRNET_DIR):
        raise RuntimeError(
            f"NMRNet 代码目录不存在: {NMRNET_DIR}\n"
            "请先将 NMRNet 放到 assets/ 目录:\n"
            f"  cp -r ~/Downloads/NMRNet-main {NMRNET_DIR}\n"
            f"  # 或: git clone https://github.com/Colin-Jay/NMRNet {NMRNET_DIR}"
        )
    if NMRNET_DIR not in sys.path:
        sys.path.insert(0, NMRNET_DIR)


# ─── 下载 scaler 文件 ──────────────────────────────────────────────────────────
def download_weights_and_scalers() -> None:
    """
    使用 remotezip 从 Zenodo ZIP 按需提取：
      - H/C checkpoint_best.pt（各 ~560 MB）→ /tmp/weights/
      - H/C target_scaler.ss（各 623 B）    → /tmp/weights/
    """
    try:
        from remotezip import RemoteZip
    except ImportError:
        print("[错误] 请先安装 remotezip: pip install remotezip")
        sys.exit(1)

    _LIQ_ZIP = "weights/finetune/liquid"
    targets = [
        # checkpoints
        (
            f"{_LIQ_ZIP}/H_mol_pre_all_h_220816_global_0_kener_gauss_atomdes_0_unimol_large_atom_regloss_mae_lr_5e-3_bs_16_0.06_400/cv_seed_42_fold_0/checkpoint_best.pt",
            os.path.join(H_MODEL_DIR, CHECKPOINT_REL),
        ),
        (
            f"{_LIQ_ZIP}/C_mol_pre_all_h_220816_global_0_kener_gauss_atomdes_0_unimol_large_atom_regloss_mae_lr_1e-3_bs_16_0.06_200/cv_seed_42_fold_0/checkpoint_best.pt",
            os.path.join(C_MODEL_DIR, CHECKPOINT_REL),
        ),
        # scalers
        (H_SCALER_ZIP, os.path.join(H_MODEL_DIR, "target_scaler.ss")),
        (C_SCALER_ZIP, os.path.join(C_MODEL_DIR, "target_scaler.ss")),
    ]

    need = [(zp, lp) for zp, lp in targets if not os.path.exists(lp)]
    if not need:
        print("✓ 所有权重和 scaler 文件均已就绪")
        return

    print(f"连接到 Zenodo: {ZENODO_URL}")
    with RemoteZip(ZENODO_URL) as zf:
        for zip_path, local_path in need:
            size_hint = "~560 MB" if zip_path.endswith(".pt") else "< 1 KB"
            print(f"  [下载] {os.path.basename(os.path.dirname(zip_path))}/.../{os.path.basename(zip_path)} ({size_hint})")
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(zf.read(zip_path))
            print(f"  [完成] → {local_path}")
    print("✓ 下载完毕")


# ─── SMILES → 数据记录 ──────────────────────────────────────────────────────────
def smiles_to_data(smiles: str, target_element: str) -> dict:
    """
    SMILES → 含显式 H 的 3D 分子 → NMRNet 格式数据记录。
    target_element: 'H' 或 'C'
    """
    from rdkit import Chem
    from rdkit.Chem import AllChem

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"无效的 SMILES: {smiles!r}")

    mol = Chem.AddHs(mol)
    res = AllChem.EmbedMolecule(mol, randomSeed=42)
    if res != 0:
        # 尝试 ETKDG 方法
        params = AllChem.ETKDGv3()
        params.randomSeed = 42
        res = AllChem.EmbedMolecule(mol, params)
    if res != 0:
        raise RuntimeError(f"SMILES {smiles!r} 的 3D 构象生成失败")

    try:
        AllChem.MMFFOptimizeMolecule(mol)
    except Exception:
        pass  # 优化失败时使用未优化构象

    atoms = [atom.GetSymbol() for atom in mol.GetAtoms()]
    coords = np.array(mol.GetConformer().GetPositions(), dtype=np.float32)

    atoms_target_mask = np.array(
        [1 if a == target_element else 0 for a in atoms], dtype=np.int32
    )
    atoms_target = np.zeros(len(atoms), dtype=np.float32)

    return {
        "atoms": atoms,
        "coordinates": coords,
        "atoms_target": atoms_target,
        "atoms_target_mask": atoms_target_mask,
    }


# ─── 模型参数 ──────────────────────────────────────────────────────────────────
def _make_model_args(selected_atom: str, model_dir: str) -> argparse.Namespace:
    """返回 UniMatModel 所需的参数 Namespace（对应 unimol_large 架构）。"""
    args = argparse.Namespace()
    # 模型结构 —— unimol_large
    args.encoder_layers          = 15
    args.encoder_embed_dim       = 512
    args.encoder_ffn_embed_dim   = 2048
    args.encoder_attention_heads = 64
    args.dropout                 = 0.1
    args.emb_dropout             = 0.1
    args.attention_dropout       = 0.1
    args.activation_dropout      = 0.0
    args.pooler_dropout          = 0.0
    args.activation_fn           = "gelu"
    args.pooler_activation_fn    = "tanh"
    args.post_ln                 = False
    # 未使用的预训练损失标志（置 -1 表示禁用）
    args.masked_token_loss            = -1.0
    args.masked_coord_loss            = -1.0
    args.masked_dist_loss             = -1.0
    args.x_norm_loss                  = -1.0
    args.delta_pair_repr_norm_loss    = -1.0
    args.lattice_loss                 = -1.0
    # 任务参数
    args.selected_atom            = selected_atom
    args.num_classes              = 1
    args.atom_descriptor          = 0
    args.classification_head_name = "nmr_head"
    args.model_path               = os.path.join(model_dir, CHECKPOINT_REL)
    args.dict_path                = os.path.join(NMRNET_DIR, "oc_limit_dict.txt")
    args.global_distance          = False
    args.gaussian_kernel          = True
    args.saved_dir = model_dir   # target_scaler.ss 在各自的模型目录里
    args.max_atoms                = 512
    args.max_seq_len              = 1024
    args.seed                     = 1
    args.batch_size               = 16
    return args


# ─── 模型加载 ──────────────────────────────────────────────────────────────────
def _load_model(args, dictionary):
    import torch
    from unicore import checkpoint_utils
    from uninmr.models import UniMatModel

    state = checkpoint_utils.load_checkpoint_to_cpu(args.model_path)
    # 兼容旧版键名
    state["model"] = {
        (k.replace("classification_heads", "node_classification_heads")
         if k.startswith("classification_heads") else k): v
        for k, v in state["model"].items()
    }
    model = UniMatModel(args, dictionary)
    model.register_node_classification_head(
        args.classification_head_name,
        num_classes=args.num_classes,
        extra_dim=args.atom_descriptor,
    )
    model.load_state_dict(state["model"], strict=False)
    model.float()   # CPU 推理；有 GPU 可改 model.half().cuda()
    model.eval()
    return model


# ─── 数据集构建 ────────────────────────────────────────────────────────────────
def _build_dataset(record: dict, args, dictionary, target_scaler):
    """
    将单条数据记录构建成 NestedDictionaryDataset，
    对应 uninmr.py UniNMRTask.load_dataset 的液态分支。
    """
    import torch
    from torch.utils.data import Dataset
    from unicore.data import (
        AppendTokenDataset, PrependTokenDataset,
        RightPadDataset, TokenizeDataset,
        RightPadDataset2D, NestedDictionaryDataset,
    )
    from uninmr.data import (
        KeyDataset, IndexDataset, ToTorchDataset,
        DistanceDataset, EdgeTypeDataset,
        PrependAndAppend2DDataset, RightPadDataset2D0,
        CroppingDataset, NormalizeDataset, TargetScalerDataset,
        SelectTokenDataset, FilterDataset,
    )
    from uninmr.utils import parse_select_atom

    class _SingleDataset(Dataset):
        def __init__(self, item):
            self._item = item
        def __len__(self):
            return 1
        def __getitem__(self, idx):
            return self._item

    def _pa(ds, pre, app):
        return AppendTokenDataset(PrependTokenDataset(ds, pre), app)

    dataset       = _SingleDataset(record)
    matid_dataset = IndexDataset(dataset)

    dataset = CroppingDataset(dataset, args.seed, "atoms", "coordinates", args.max_atoms)
    dataset = NormalizeDataset(dataset, "coordinates")

    token_dataset = TokenizeDataset(
        KeyDataset(dataset, "atoms"), dictionary, max_seq_len=args.max_seq_len
    )
    selected_token = parse_select_atom(dictionary, args.selected_atom)
    select_atom_dataset = SelectTokenDataset(
        token_dataset=token_dataset,
        token_mask_dataset=KeyDataset(dataset, "atoms_target_mask"),
        selected_token=selected_token,
    )

    # 过滤无目标原子的记录（对单分子推理基本不会触发）
    keep = [0 if torch.all(select_atom_dataset[i] == 0) else 1
            for i in range(len(select_atom_dataset))]
    if sum(keep) == 0:
        raise ValueError(
            f"分子中未找到 {args.selected_atom} 原子，无法预测"
        )
    dataset           = FilterDataset(dataset, keep)
    matid_dataset     = FilterDataset(matid_dataset, keep)
    token_dataset     = FilterDataset(token_dataset, keep)
    select_atom_dataset = FilterDataset(select_atom_dataset, keep)

    token_dataset       = _pa(token_dataset, dictionary.bos(), dictionary.eos())
    select_atom_dataset = _pa(select_atom_dataset, dictionary.pad(), dictionary.pad())

    coord_dataset    = ToTorchDataset(KeyDataset(dataset, "coordinates"), "float32")
    distance_dataset = PrependAndAppend2DDataset(DistanceDataset(coord_dataset), 0.0)
    distance_dataset = RightPadDataset2D(distance_dataset, pad_idx=0)
    coord_dataset    = _pa(coord_dataset, 0.0, 0.0)
    edge_type        = EdgeTypeDataset(token_dataset, len(dictionary))

    tgt_dataset = TargetScalerDataset(
        ToTorchDataset(KeyDataset(dataset, "atoms_target"), "float32"),
        target_scaler, args.num_classes,
    )
    tgt_dataset = _pa(
        ToTorchDataset(tgt_dataset, dtype="float32"),
        dictionary.pad(), dictionary.pad(),
    )

    return NestedDictionaryDataset(
        {
            "net_input": {
                "select_atom": RightPadDataset(select_atom_dataset, pad_idx=dictionary.pad()),
                "src_tokens":  RightPadDataset(token_dataset,       pad_idx=dictionary.pad()),
                "src_coord":   RightPadDataset2D0(coord_dataset,    pad_idx=0),
                "src_distance": distance_dataset,
                "src_edge_type": RightPadDataset2D(edge_type,       pad_idx=0),
            },
            "target": {
                "finetune_target": RightPadDataset(tgt_dataset, pad_idx=0),
            },
            "matid": matid_dataset,
        }
    )


# ─── 核心推理 ──────────────────────────────────────────────────────────────────
def predict_shifts(smiles: str, nucleus: str, model_dir: str) -> np.ndarray:
    """
    返回分子中所有目标元素原子的预测化学位移 (ppm)。
    nucleus: 'H' → ¹H；  'C' → ¹³C
    """
    import torch
    from torch.utils.data import DataLoader
    from unicore.data import Dictionary
    from uninmr.utils import TargetScaler

    scaler_dir  = model_dir
    scaler_path = os.path.join(scaler_dir, "target_scaler.ss")
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(
            f"缺少 scaler 文件: {scaler_path}\n"
            "请先运行: python nmr_prediction.py --setup"
        )

    args       = _make_model_args(nucleus, model_dir)
    dictionary = Dictionary.load(args.dict_path)
    dictionary.add_symbol("[MASK]", is_special=True)

    target_scaler = TargetScaler(scaler_dir)
    record        = smiles_to_data(smiles, nucleus)
    model         = _load_model(args, dictionary)
    nest_dataset  = _build_dataset(record, args, dictionary, target_scaler)

    loader = DataLoader(nest_dataset, batch_size=1, shuffle=False)
    all_preds = []
    with torch.no_grad():
        for batch in loader:
            net_input = {
                k[len("net_input."):]: v
                for k, v in batch.items()
                if k.startswith("net_input.")
            }
            out  = model(**net_input, features_only=True,
                         classification_head_name=args.classification_head_name)
            pred = target_scaler.inverse_transform(
                out[0].view(-1, args.num_classes).cpu().numpy()
            ).astype("float32")
            all_preds.append(pred)

    return np.concatenate(all_preds).reshape(-1)


# ─── 谱图绘制 ──────────────────────────────────────────────────────────────────
def plot_spectrum(shifts: np.ndarray, nucleus: str, smiles: str, save_path: str) -> None:
    """用 Lorentzian 峰叠加绘制 NMR 谱图（x 轴从高到低，符合 NMR 惯例）。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    gamma = 0.4 if nucleus == "H" else 2.0   # 线宽 (ppm)，C 谱峰更宽

    x_lo = -1.0  if nucleus == "H" else -20.0
    x_hi = max(float(shifts.max()) + 2.0, 12.0) if nucleus == "H" \
           else max(float(shifts.max()) + 20.0, 220.0)
    x = np.linspace(x_lo, x_hi, 10000)

    spectrum = np.sum(1.0 / (1.0 + ((x[:, None] - shifts) / gamma) ** 2), axis=1)
    spectrum /= spectrum.max()

    label = "¹H" if nucleus == "H" else "¹³C"
    color = "#2166ac" if nucleus == "H" else "#d6604d"

    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(x, spectrum, color=color, linewidth=1.8, label=f"NMRNet {label} prediction")
    ax.fill_between(x, spectrum, alpha=0.12, color=color)

    # 标注各峰位
    for s in shifts:
        ax.axvline(s, color=color, alpha=0.3, linewidth=0.7, linestyle="--")

    ax.set_xlim(x_hi, x_lo)   # 从右到左（高场在右）
    ax.set_ylim(-0.05, 1.2)
    ax.set_xlabel(f"Chemical Shift δ (ppm)", fontsize=13)
    ax.set_ylabel("Relative Intensity", fontsize=13)
    ax.set_title(f"Predicted {label} NMR  —  {smiles}", fontsize=13)
    ax.set_yticks([])
    ax.legend(fontsize=11, loc="upper left")
    for spine in ("top", "right", "left"):
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_linewidth(1.5)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"[输出] {save_path}")


# ─── 主函数 ────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="NMRNet 液相 NMR 化学位移预测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("smiles", nargs="?", help="输入 SMILES 字符串")
    parser.add_argument(
        "--nucleus", choices=["H", "C", "both"], default="both",
        help="预测核: H (¹H)、C (¹³C)、both (默认 both)",
    )
    parser.add_argument(
        "--setup", action="store_true",
        help="从 Zenodo 下载 target_scaler.ss 文件（仅首次需要）",
    )
    args = parser.parse_args()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.setup:
        print("=== 下载模型权重 + scaler (→ /tmp/weights/) ===")
        download_weights_and_scalers()
        return

    if not args.smiles:
        parser.error("请提供 SMILES 字符串，或使用 --setup 下载所需文件")

    _ensure_nmrnet_in_path()

    smiles    = args.smiles
    nuclei    = ["H", "C"] if args.nucleus == "both" else [args.nucleus]
    model_map = {"H": H_MODEL_DIR, "C": C_MODEL_DIR}
    label_map = {"H": "¹H", "C": "¹³C"}
    tag_map   = {"H": "1H", "C": "13C"}

    safe_name = smiles[:20].replace("/", "-").replace("\\", "-")
    results: dict[str, np.ndarray] = {}

    for nucleus in nuclei:
        try:
            shifts = predict_shifts(smiles, nucleus, model_map[nucleus])
            results[nucleus] = shifts
            out_path = os.path.join(OUTPUT_DIR, f"nmr_{tag_map[nucleus]}_{safe_name}.png")
            plot_spectrum(shifts, nucleus, smiles, out_path)
        except Exception as exc:
            print(f"\n[错误] {label_map[nucleus]} 预测失败: {exc}")

    # ── 输出汇总报告 ─────────────────────────────────────────────────────────
    report_path = os.path.join(OUTPUT_DIR, f"nmr_shifts_{safe_name}.md")
    lines = [
        f"# NMR Chemical Shifts — {smiles}",
        f"",
        f"> Predicted by NMRNet (liquid phase)",
        f"",
    ]

    if "H" in results:
        h_shifts = sorted(results["H"].tolist())
        lines += [
            f"## ¹H NMR ({len(h_shifts)} atoms)",
            f"",
            f"| # | δ (ppm) |",
            f"|---|---------|",
        ]
        for i, s in enumerate(h_shifts, 1):
            lines.append(f"| {i} | {s:.2f} |")
        lines.append("")

    if "C" in results:
        c_shifts = sorted(results["C"].tolist())
        lines += [
            f"## ¹³C NMR ({len(c_shifts)} atoms)",
            f"",
            f"| # | δ (ppm) |",
            f"|---|---------|",
        ]
        for i, s in enumerate(c_shifts, 1):
            lines.append(f"| {i} | {s:.2f} |")
        lines.append("")

    with open(report_path, "w") as f:
        f.write("\n".join(lines))

    # ── 终端打印汇总 ──────────────────────────────────────────────────────────
    print(f"\n{'='*50}")
    print(f"  NMR 预测结果  —  {smiles}")
    print(f"{'='*50}")

    if "H" in results:
        h_shifts = sorted(results["H"].tolist())
        print(f"\n  ¹H 化学位移 ({len(h_shifts)} 个原子):")
        for i, s in enumerate(h_shifts, 1):
            print(f"    {i:>3}.  {s:>7.2f} ppm")

    if "C" in results:
        c_shifts = sorted(results["C"].tolist())
        print(f"\n  ¹³C 化学位移 ({len(c_shifts)} 个原子):")
        for i, s in enumerate(c_shifts, 1):
            print(f"    {i:>3}.  {s:>7.2f} ppm")

    print(f"\n  输出文件:")
    for nucleus in results:
        print(f"    /tmp/chemclaw/nmr_{tag_map[nucleus]}_{safe_name}.png")
    print(f"    {report_path}")


if __name__ == "__main__":
    main()
