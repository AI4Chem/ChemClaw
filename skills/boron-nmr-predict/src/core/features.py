import torch
import numpy as np
import pandas as pd
from rdkit import Chem
from rdkit.Chem import AllChem, rdchem
from torch_geometric.data import Data

# ==========================================
# 1. 全局配置：原子列表与指纹参数
# ==========================================

# 根据你的统计数据更新的允许原子列表
# 包含：常见的有机非金属 + 卤素 + 你数据中出现的金属/半金属
ALLOWED_ATOMS = [
    # --- 核心有机元素 & 卤素 ---
    'B', 'C', 'N', 'O', 'H', 'F', 'Cl', 'Br', 'I', 'P', 'S', 'Si',
    # --- 你提供的统计图中的其他元素 (按字母序) ---
    'Al', 'As', 'Au', 'Bi', 'Cd', 'Co', 'Cr', 'Cs', 'Cu', 
    'Fe', 'Ga', 'Ge', 'In', 'K', 'Li', 'Mg', 'Mn', 'Na', 
    'Pb', 'Re', 'Sb', 'Se', 'Sn', 'Te', 'W'
]

# 溶剂特征提取参数 (Morgan Fingerprint)
SOLVENT_FP_SIZE = 1024 
SOLVENT_RADIUS = 2  # 相当于 ECFP4

# ==========================================
# 2. 辅助工具函数
# ==========================================

def one_hot_encoding(x, permitted_list):
    """
    独热编码辅助函数
    将输入的 x 转换为 [0, 1, 0, ...] 的向量
    如果 x 不在列表中，则标记为列表的最后一位 (Unknown)
    """
    if x not in permitted_list:
        x = permitted_list[-1]
    return [int(x == possible) for possible in permitted_list]

# ==========================================
# 3. 核心特征提取函数 (含详细注释)
# ==========================================

def get_atom_features(atom):
    """
    提取单个原子的特征向量。
    
    输入: rdkit.Chem.rdchem.Atom 对象
    输出: torch.Tensor (一维向量)
    """
    features = []
    
    # ---------------------------------------------------------
    #特征 1: 原子类型 (Atom Symbol)
    # [化学意义]: 决定了原子的核心电子结构、电负性和核外电子排布。
    # 这是最基础的特征，区分是 硼(B)、碳(C) 还是 氧(O)。
    # ---------------------------------------------------------
    features += one_hot_encoding(atom.GetSymbol(), ALLOWED_ATOMS)
    
    # ---------------------------------------------------------
    # 特征 2: 原子连接度 (Degree)
    # [提取范围]: 0 到 5+ (One-Hot)
    # [化学意义]: 描述位阻效应 (Steric Hindrance)。
    # 例如，伯碳、仲碳、叔碳的连接数不同，其周围电子环境差异很大。
    # ---------------------------------------------------------
    features += one_hot_encoding(atom.GetDegree(), [0, 1, 2, 3, 4, 5])
    
    # ---------------------------------------------------------
    # 特征 3: 连接氢的数量 (Total Num Hs)
    # [提取范围]: 0 到 4+ (One-Hot)
    # [化学意义]: 对于 NMR 极其重要。
    # 氢原子会通过超共轭效应或直接的电性作用影响中心原子的屏蔽常数。
    # ---------------------------------------------------------
    features += one_hot_encoding(atom.GetTotalNumHs(), [0, 1, 2, 3, 4])
    
    # ---------------------------------------------------------
    # 特征 4: 杂化方式 (Hybridization)
    # [提取范围]: sp, sp2, sp3, sp3d, sp3d2 (One-Hot)
    # [化学意义]: 决定了轨道的 s-character (s轨道成分)。
    # s 轨道成分越高，电子越靠近原子核，去屏蔽效应越明显。
    # 例如：sp2 硼 (平面) 和 sp3 硼 (四面体) 的化学位移通常相差几十 ppm。
    # ---------------------------------------------------------
    features += one_hot_encoding(
        atom.GetHybridization(), 
        [
            rdchem.HybridizationType.SP, 
            rdchem.HybridizationType.SP2, 
            rdchem.HybridizationType.SP3, 
            rdchem.HybridizationType.SP3D, 
            rdchem.HybridizationType.SP3D2
        ]
    )
    
    # ---------------------------------------------------------
    # 特征 5: 芳香性 (Is Aromatic)
    # [提取类型]: 布尔值 (0 或 1)
    # [化学意义]: 芳香环会产生“环电流效应” (Ring Current Effect)。
    # 如果硼原子在苯环平面上方或连接在苯环上，位移会受到显著的各向异性影响。
    # ---------------------------------------------------------
    features.append(1 if atom.GetIsAromatic() else 0)
    
    # ---------------------------------------------------------
    # 特征 6: 形式电荷 (Formal Charge)
    # [提取类型]: 整数数值 (如 -1, 0, +1)
    # [化学意义]: 直接影响电子云密度。
    # 带正电 (少电子) -> 去屏蔽 -> 低场位移 (大数值)
    # 带负电 (多电子) -> 屏蔽 -> 高场位移 (小数值)
    # ---------------------------------------------------------
    features.append(atom.GetFormalCharge())
    
    # ---------------------------------------------------------
    # 特征 7: 是否在环中 (Is In Ring)
    # [提取类型]: 布尔值
    # [化学意义]: 环结构会限制键角，产生环张力，进而改变杂化轨道的成分。
    # ---------------------------------------------------------
    features.append(1 if atom.IsInRing() else 0)
    
    # ---------------------------------------------------------
    # 特征 8: 手性标记 (Chirality)
    # [提取类型]: 布尔值 (是否有手性中心)
    # [化学意义]: 区分 R/S 构型。
    # 虽然 2D 图对立体化学捕捉有限，但在非对映异构体中，手性环境会导致位移不同。
    # ---------------------------------------------------------
    features.append(1 if atom.GetChiralTag() != rdchem.ChiralType.CHI_UNSPECIFIED else 0)
    
    
    # ---------------------------------------------------------
    # 【新增】特征 9: Gasteiger Partial Charge (电子密度)
    # ---------------------------------------------------------
    try:
        # 尝试获取计算好的电荷 (需要在处理分子时先计算)
        # 如果获取失败，默认为 0.0
        charge = float(atom.GetProp('_GasteigerCharge'))
        
        # 归一化技巧：电荷通常在 -0.5 到 +0.5 之间
        # 我们可以直接用，或者检查是否有极端值 (NaN/Inf)
        if np.isnan(charge) or np.isinf(charge):
            charge = 0.0
    except:
        charge = 0.0
        
    features.append(charge)
    
    return torch.tensor(features, dtype=torch.float)

def get_bond_features(bond):
    """
    提取化学键的特征向量。
    """
    bond_type = bond.GetBondType()
    
    # ---------------------------------------------------------
    # 特征 1: 键级类型 (Bond Type)
    # [提取范围]: 单键, 双键, 三键, 芳香键 (One-Hot)
    # [化学意义]: 决定了连接的紧密程度和π电子的参与度。
    # ---------------------------------------------------------
    features = [
        int(bond_type == rdchem.BondType.SINGLE),
        int(bond_type == rdchem.BondType.DOUBLE),
        int(bond_type == rdchem.BondType.TRIPLE),
        int(bond_type == rdchem.BondType.AROMATIC)
    ]
    
    # ---------------------------------------------------------
    # 特征 2: 是否共轭 (Is Conjugated)
    # [提取类型]: 布尔值
    # [化学意义]: 共轭体系允许电子离域 (Delocalization)。
    # 这意味着远处的吸电子基团可以通过共轭链直接影响硼原子的电子密度。
    # ---------------------------------------------------------
    features.append(int(bond.GetIsConjugated()))
    
    # ---------------------------------------------------------
    # 特征 3: 是否在环中 (Is In Ring)
    # [提取类型]: 布尔值
    # ---------------------------------------------------------
    features.append(int(bond.IsInRing()))
    
    # ---------------------------------------------------------
    # 特征 4: 立体化学 (Stereo)
    # [提取类型]: One-Hot (无, Z/Cis, E/Trans, 任意)
    # [化学意义]: 顺反异构 (Cis/Trans) 对空间环境影响巨大。
    # 例如，顺式结构可能导致空间位阻，从而改变化学位移。
    # ---------------------------------------------------------
    stereo = bond.GetStereo()
    features.append(1 if stereo == rdchem.BondStereo.STEREONONE else 0)
    features.append(1 if stereo == rdchem.BondStereo.STEREOANY else 0)
    features.append(1 if stereo == rdchem.BondStereo.STEREOZ else 0)
    features.append(1 if stereo == rdchem.BondStereo.STEREOE else 0)
    
    return torch.tensor(features, dtype=torch.float)

def get_solvent_features(solvent_smiles):
    """
    提取溶剂特征: Morgan Fingerprint (ECFP)
    """
    mol = Chem.MolFromSmiles(solvent_smiles)
    if mol is None:
        # 如果解析失败，返回全0向量 (作为未知溶剂处理)
        return torch.zeros(SOLVENT_FP_SIZE, dtype=torch.float)
    
    # 生成指纹 (Radius=2, 1024 bits)
    # 这能够捕捉溶剂的官能团信息（如是否有羟基、苯环、氯原子等）
    fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=SOLVENT_RADIUS, nBits=SOLVENT_FP_SIZE)
    
    array = np.zeros((0,), dtype=np.float32)
    AllChem.DataStructs.ConvertToNumpyArray(fp, array)
    
    return torch.tensor(array, dtype=torch.float)

# ==========================================
# 4. 主处理入口 (Process Entry)
# ==========================================

def process_entry(row):
    """
    处理单行数据，将 Pandas Row 转换为 PyG Data 对象
    """
    mol_smiles = row['Smiles']          # 分子 SMILES
    solv_smiles = row['solvent_smiles'] # 溶剂 SMILES
    ppm_str = str(row['ppm_values'])    # 位移值字符串
    
    # --- A. 构建主分子图 ---
    mol = Chem.MolFromSmiles(mol_smiles)
    if mol is None: return None
    
    atom_feats = []
    boron_mask = []
    
    for atom in mol.GetAtoms():
        # 提取详细原子特征
        atom_feats.append(get_atom_features(atom))
        # 标记是否为硼原子
        boron_mask.append(atom.GetSymbol() == 'B')
        
    x = torch.stack(atom_feats)
    mask_b = torch.tensor(boron_mask, dtype=torch.bool)
    
    # 校验: 必须含有硼原子
    num_b = mask_b.sum().item()
    if num_b == 0: return None
    
    # 构建边 (Edge Index & Features)
    edge_indices = []
    edge_attrs = []
    for bond in mol.GetBonds():
        i = bond.GetBeginAtomIdx()
        j = bond.GetEndAtomIdx()
        
        # 无向图: 添加 (i, j) 和 (j, i)
        edge_indices.append([i, j])
        edge_indices.append([j, i])
        
        # 提取详细键特征
        b_feat = get_bond_features(bond)
        edge_attrs.append(b_feat)
        edge_attrs.append(b_feat)
        
    if not edge_indices:
        # 处理单原子分子的情况 (虽然很少见)
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr_dim = len(get_bond_features(mol.GetBonds()[0])) if mol.GetNumBonds() > 0 else 10 # 预估维度
        edge_attr = torch.empty((0, edge_attr_dim), dtype=torch.float)
    else:
        edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
        edge_attr = torch.stack(edge_attrs)

    # --- B. 提取溶剂特征 ---
    # 输出形状: [1, 1024]
    solvent_feat = get_solvent_features(solv_smiles).unsqueeze(0)

    # --- C. 解析标签 (Labels) ---
    try:
        shifts = [float(s) for s in ppm_str.replace(';', ',').split(',') if s.strip()]
    except:
        return None
        
    # 处理 "多硼单值" (对称) 和 "多硼多值" (非对称) 的情况
    if len(shifts) == 1 and num_b > 1:
        shifts = shifts * num_b # 广播
    elif len(shifts) != num_b:
        # 数据对不上，跳过
        return None
        
    y_b = torch.tensor(shifts, dtype=torch.float)

    # --- D. 打包 Data 对象 ---
    data = Data(
        x=x,                 # 节点特征 [Num_Nodes, Feature_Dim]
        edge_index=edge_index, # 连接关系 [2, Num_Edges]
        edge_attr=edge_attr,   # 边特征 [Num_Edges, Edge_Feature_Dim]
        mask_b=mask_b,       # 硼原子掩码 [Num_Nodes]
        y_b=y_b,             # 真实位移值 [Num_Borons]
        solvent_x=solvent_feat # 溶剂指纹 [1, 1024]
    )
    
    return data

if __name__ == "__main__":
    # 假设 CSV 已经读取为 df
    # df = pd.read_csv('your_data.csv')
    # dataset = [process_entry(row) for _, row in df.iterrows() if process_entry(row) is not None]
    
    # 模拟测试
    test_row = {
        'Smiles': 'CN1CC(=O)OB(C(B2OC(C)(C)C(C)(C)O2)=C(B2OC(C)(C)C(C)(C)O2)B2OC(C)(C)C(C)(C)O2)OC(=O)C1', 
        'solvent_smiles': 'ClC(Cl)Cl', # 氯仿
        'ppm_values': '28.5'
    }
    data = process_entry(test_row)
    
    print("X Shape:", data.x.shape)          # [Num_Atoms, 50+]
    print("Solvent Shape:", data.solvent_x.shape) # [1, 1024]
    print("Target:", data.y_b)
    # print("edge_index:", data.edge_index)
    # print("edge_attr:", data.edge_attr)