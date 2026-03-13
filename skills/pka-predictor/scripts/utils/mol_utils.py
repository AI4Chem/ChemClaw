#!/usr/bin/env python3
"""
分子工具函数
提供分子处理、SMILES 解析、官能团识别等功能
"""

from typing import List, Dict, Optional, Tuple

try:
    from rdkit import Chem
    from rdkit.Chem import Descriptors, rdMolDescriptors
    RDKit_AVAILABLE = True
except ImportError:
    RDKit_AVAILABLE = False


# 使用 SMARTS，而不是简单字符串匹配
ACIDIC_GROUPS = {
    "carboxylic_acid": {
        "smarts": "[CX3](=O)[OX2H1]",
        "pka_range": (3.0, 5.0),
        "name": "羧酸",
    },
    "phenol": {
        "smarts": "[c][OX2H]",
        "pka_range": (9.0, 11.0),
        "name": "酚",
    },
    "alcohol": {
        "smarts": "[CX4][OX2H]",
        "pka_range": (15.0, 18.0),
        "name": "醇",
    },
    "thiol": {
        "smarts": "[CX4][SX2H]",
        "pka_range": (8.0, 11.0),
        "name": "硫醇",
    },
    "sulfonic_acid": {
        "smarts": "[SX4](=[OX1])(=[OX1])[OX2H]",
        "pka_range": (-2.0, 2.0),
        "name": "磺酸",
    },
    "phosphoric_acid": {
        "smarts": "P(=O)(O)O",
        "pka_range": (2.0, 7.0),
        "name": "磷酸",
    },
    "imide": {
        "smarts": "[NX3H]([CX3](=[OX1]))[CX3](=[OX1])",
        "pka_range": (8.0, 10.0),
        "name": "酰亚胺",
    },
}

BASIC_GROUPS = {
    "primary_amine": {
        "smarts": "[NX3;H2][CX4]",
        "pka_range": (9.0, 11.0),
        "name": "伯胺",
    },
    "secondary_amine": {
        "smarts": "[NX3;H1]([CX4])[CX4]",
        "pka_range": (10.0, 12.0),
        "name": "仲胺",
    },
    "tertiary_amine": {
        "smarts": "[NX3]([CX4])([CX4])[CX4]",
        "pka_range": (9.0, 11.0),
        "name": "叔胺",
    },
    "aromatic_amine": {
        "smarts": "[NX3;H2,H1,H0][c]",
        "pka_range": (4.0, 6.0),
        "name": "芳香胺",
    },
    "pyridine": {
        "smarts": "n1ccccc1",
        "pka_range": (5.0, 6.0),
        "name": "吡啶",
    },
    "imidazole": {
        "smarts": "n1cc[nH]c1",
        "pka_range": (6.0, 7.0),
        "name": "咪唑",
    },
}


def check_rdkit():
    """检查 RDKit 是否可用"""
    if not RDKit_AVAILABLE:
        raise ImportError("需要安装 RDKit。建议使用 conda 安装：conda install -c conda-forge rdkit")


def smiles_to_mol(smiles: str) -> Optional[object]:
    """
    将 SMILES 字符串转换为 RDKit Mol 对象
    """
    check_rdkit()
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol
    except Exception:
        return None


def mol_to_smiles(mol: object, canonical: bool = True) -> Optional[str]:
    """
    将 RDKit Mol 对象转换为 SMILES 字符串
    """
    check_rdkit()
    try:
        return Chem.MolToSmiles(mol, canonical=canonical)
    except Exception:
        return None


def canonicalize_smiles(smiles: str) -> Optional[str]:
    """
    规范化 SMILES
    """
    mol = smiles_to_mol(smiles)
    if mol is None:
        return None
    return mol_to_smiles(mol, canonical=True)


def get_molecular_weight(smiles: str) -> Optional[float]:
    mol = smiles_to_mol(smiles)
    if mol:
        return Descriptors.MolWt(mol)
    return None


def get_molecular_formula(smiles: str) -> Optional[str]:
    mol = smiles_to_mol(smiles)
    if mol:
        return rdMolDescriptors.CalcMolFormula(mol)
    return None


def _match_smarts_groups(smiles: str, group_defs: Dict[str, Dict]) -> List[Dict]:
    mol = smiles_to_mol(smiles)
    if not mol:
        return []

    found_groups = []
    for group_id, group_info in group_defs.items():
        try:
            patt = Chem.MolFromSmarts(group_info["smarts"])
            if patt is None:
                continue
            matches = mol.GetSubstructMatches(patt)
            if matches:
                found_groups.append({
                    "id": group_id,
                    "name": group_info["name"],
                    "smarts": group_info["smarts"],
                    "pka_range": group_info["pka_range"],
                    "match_count": len(matches),
                    "atom_indices": [list(m) for m in matches],
                })
        except Exception:
            continue

    return found_groups


def identify_acidic_groups(smiles: str) -> List[Dict]:
    """
    识别分子中的酸性官能团
    """
    return _match_smarts_groups(smiles, ACIDIC_GROUPS)


def identify_basic_groups(smiles: str) -> List[Dict]:
    """
    识别分子中的碱性官能团
    """
    return _match_smarts_groups(smiles, BASIC_GROUPS)


def get_hydrogen_bond_donors(smiles: str) -> int:
    mol = smiles_to_mol(smiles)
    if mol:
        return rdMolDescriptors.CalcNumHBD(mol)
    return 0


def get_hydrogen_bond_acceptors(smiles: str) -> int:
    mol = smiles_to_mol(smiles)
    if mol:
        return rdMolDescriptors.CalcNumHBA(mol)
    return 0


def get_rotatable_bonds(smiles: str) -> int:
    mol = smiles_to_mol(smiles)
    if mol:
        return rdMolDescriptors.CalcNumRotatableBonds(mol)
    return 0


def get_logp(smiles: str) -> Optional[float]:
    mol = smiles_to_mol(smiles)
    if mol:
        return Descriptors.MolLogP(mol)
    return None


def get_tpsa(smiles: str) -> Optional[float]:
    mol = smiles_to_mol(smiles)
    if mol:
        return rdMolDescriptors.CalcTPSA(mol)
    return 0


def calculate_descriptors(smiles: str) -> Dict:
    """
    计算分子的多种描述符
    """
    mol = smiles_to_mol(smiles)
    if not mol:
        return {}

    return {
        "molecular_weight": round(Descriptors.MolWt(mol), 4),
        "logp": round(Descriptors.MolLogP(mol), 4),
        "hbd": int(rdMolDescriptors.CalcNumHBD(mol)),
        "hba": int(rdMolDescriptors.CalcNumHBA(mol)),
        "rotatable_bonds": int(rdMolDescriptors.CalcNumRotatableBonds(mol)),
        "tpsa": round(rdMolDescriptors.CalcTPSA(mol), 4),
        "formula": rdMolDescriptors.CalcMolFormula(mol),
    }