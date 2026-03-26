"""
ML Global Features for GNN Fusion
==================================
Compute Top-20 SHAP features (from XGBoost SHAP analysis) for each molecule.
Uses the same computation method as the original Chemia ML training pipeline
(utils/mol_fp_features.py: Descriptors._descList + rdFingerprintGenerator).

Features:
  - 16 RDKit molecular descriptors (compound-level)
  - 4 Morgan fingerprint bits (radius=2, 1024 bits)

NaN handling: median imputation + StandardScaler normalization
"""

import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors
from sklearn.preprocessing import StandardScaler
import pickle
import os

# ==========================================
# Morgan fingerprint API (与 Chemia 保持一致)
# ==========================================
try:
    from rdkit.Chem import rdFingerprintGenerator
    HAS_NEW_FP_GENERATOR = True
except ImportError:
    from rdkit.Chem import AllChem
    HAS_NEW_FP_GENERATOR = False

# ==========================================
# Top-20 SHAP Features Definition
# (from feature_importance_ranking.csv)
# ==========================================

# 16 RDKit descriptors (ordered by SHAP importance)
TOP_RDKIT_DESCRIPTORS = [
    'BCUT2D_MRLOW',               # #1  SHAP=4.376
    'SlogP_VSA7',                 # #4  SHAP=1.294
    'MaxPartialCharge',           # #5  SHAP=1.228
    'BCUT2D_MWLOW',               # #7  SHAP=0.934
    'MinPartialCharge',           # #8  SHAP=0.664
    'MaxAbsPartialCharge',        # #9  SHAP=0.661
    'NOCount',                    # #10 SHAP=0.493
    'BCUT2D_LOGPHI',              # #11 SHAP=0.448
    'MinEStateIndex',             # #12 SHAP=0.437
    'MinAbsPartialCharge',        # #13 SHAP=0.411
    'fr_quatN',                   # #14 SHAP=0.383
    'VSA_EState8',                # #15 SHAP=0.367
    'NumAliphaticHeterocycles',   # #16 SHAP=0.340
    'PEOE_VSA3',                  # #17 SHAP=0.335
    'NumAliphaticRings',          # #19 SHAP=0.270
    'MolLogP',                    # #20 SHAP=0.270
]

# 4 Morgan fingerprint bit indices (0-indexed, radius=2, 1024 bits)
TOP_MORGAN_BITS = [690, 271, 390, 656]

# Total
N_ML_FEATURES = len(TOP_RDKIT_DESCRIPTORS) + len(TOP_MORGAN_BITS)  # 20

# Build descriptor function lookup from Descriptors._descList
# (与 Chemia mol_fp_features.py 一致)
_RDKIT_DESC_FUNCS = {}
for _name, _func in Descriptors._descList:
    if _name in TOP_RDKIT_DESCRIPTORS:
        _RDKIT_DESC_FUNCS[_name] = _func

# 检查是否所有描述符都找到了
_missing = set(TOP_RDKIT_DESCRIPTORS) - set(_RDKIT_DESC_FUNCS.keys())
if _missing:
    print(f"[WARNING] 以下 RDKit 描述符未在 Descriptors._descList 中找到: {_missing}")


def compute_single(smiles: str) -> np.ndarray:
    """
    计算单个分子的 Top-20 ML 特征

    Args:
        smiles: SMILES 字符串

    Returns:
        np.ndarray of shape (20,) — 原始值，可能含 NaN
    """
    features = np.full(N_ML_FEATURES, np.nan)

    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return features

    # --- Part 1: 16 RDKit descriptors ---
    for i, desc_name in enumerate(TOP_RDKIT_DESCRIPTORS):
        func = _RDKIT_DESC_FUNCS.get(desc_name)
        if func is None:
            continue
        try:
            val = func(mol)
            if val is not None:
                val = float(val)
                if not (np.isnan(val) or np.isinf(val)):
                    features[i] = val
        except Exception:
            pass

    # --- Part 2: 4 Morgan fingerprint bits ---
    offset = len(TOP_RDKIT_DESCRIPTORS)
    try:
        if HAS_NEW_FP_GENERATOR:
            gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=1024)
            fp = gen.GetFingerprint(mol)
            fp_array = np.array(fp)
        else:
            fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=1024)
            fp_array = np.array(fp)

        for j, bit_idx in enumerate(TOP_MORGAN_BITS):
            features[offset + j] = float(fp_array[bit_idx])
    except Exception:
        pass

    return features


def load_scaler(scaler_path: str):
    """
    加载训练时保存的 scaler 和 medians

    Args:
        scaler_path: ml_feature_scaler.pkl 文件路径

    Returns:
        tuple: (scaler, medians)
    """
    with open(scaler_path, 'rb') as f:
        data = pickle.load(f)
    return data['scaler'], data['medians']


def compute_and_normalize(smiles: str, scaler, medians) -> np.ndarray:
    """
    计算单个分子的 ML 特征并用训练时的 scaler 标准化

    Args:
        smiles: SMILES 字符串
        scaler: 训练时拟合的 StandardScaler
        medians: 训练时计算的中位数 (用于 NaN 填充)

    Returns:
        np.ndarray of shape (20,) — 标准化后的特征
    """
    raw = compute_single(smiles)

    # NaN → 中位数填充
    for j in range(N_ML_FEATURES):
        if np.isnan(raw[j]):
            raw[j] = medians[j]

    # StandardScaler 标准化
    scaled = scaler.transform(raw.reshape(1, -1)).flatten()
    return scaled
