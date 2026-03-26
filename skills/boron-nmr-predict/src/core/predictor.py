"""硼核磁预测器 - 封装 V3 模型预测逻辑"""

import torch
import os
import uuid
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem, Draw
from torch_geometric.data import Data, Batch

from .model import BoronNMRNet_V3
from .features import get_atom_features, get_bond_features, SOLVENT_FP_SIZE
from .ml_features import compute_and_normalize, load_scaler, N_ML_FEATURES
from utils.exceptions import PredictionError

# 溶剂名称 → 溶剂ID 映射 (与训练时一致)
SOLVENT_NAME_TO_ID = {
    'CDCl3': 0,
    'C6D6': 1,
    'd6-DMSO': 2,
    'CD3COCD3': 3,
    'CD3CN': 4,
    'CD3OD': 5,
    'CD2Cl2': 6,
    'd8-THF': 7,
    'd8-Toluene': 8,
    'D2O': 9,
}
UNKNOWN_SOLVENT_ID = 10


class BoronNMRPredictor:
    """
    硼核磁预测器

    封装了 5 个 fold V3 模型的加载和集成预测逻辑
    """

    def __init__(self, model_dir, device='cpu', hidden_dim=256,
                 dropout=0.012558398103042557, solvent_dim=32,
                 ml_feature_dim=20, ml_hidden_dim=64):
        """
        初始化预测器

        Args:
            model_dir (str): 模型文件目录
            device (str): 计算设备（'cpu' 或 'cuda'）
            hidden_dim (int): GNN 隐藏层维度
            dropout (float): Dropout 概率
            solvent_dim (int): 溶剂 Embedding 维度
            ml_feature_dim (int): ML 全局特征维度
            ml_hidden_dim (int): ML 特征编码后维度
        """
        self.device = torch.device(device)
        self.hidden_dim = hidden_dim
        self.dropout = dropout
        self.solvent_dim = solvent_dim
        self.ml_feature_dim = ml_feature_dim
        self.ml_hidden_dim = ml_hidden_dim
        self.models = []

        # 自动推断特征维度
        self.node_dim, self.edge_dim = self._get_feature_dims()

        # 加载 ML 特征 scaler
        scaler_path = os.path.join(model_dir, 'ml_feature_scaler.pkl')
        if os.path.exists(scaler_path):
            self.ml_scaler, self.ml_medians = load_scaler(scaler_path)
            print(f"  ✓ 加载 ML 特征 scaler: {scaler_path}")
        else:
            self.ml_scaler = None
            self.ml_medians = None
            print(f"  ⚠ ML 特征 scaler 未找到，将不使用 ML 全局特征")

        # 加载 5 个 fold 模型
        self.models = self._load_models(model_dir)
        print(f"✓ 成功加载 {len(self.models)} 个模型，使用设备: {device}")

    def _get_feature_dims(self):
        """自动推断节点和边特征维度"""
        try:
            m_tmp = Chem.MolFromSmiles('CB')
            AllChem.ComputeGasteigerCharges(m_tmp)
            node_dim = get_atom_features(m_tmp.GetAtoms()[0]).shape[0]
            edge_dim = get_bond_features(m_tmp.GetBonds()[0]).shape[0]
            return node_dim, edge_dim
        except Exception as e:
            print(f"⚠ 警告: 无法自动推断特征维度，使用默认值 - {e}")
            return 58, 10  # V3 默认值

    def _load_models(self, model_dir):
        """加载 5 个 fold V3 模型"""
        models = []

        # 确定是否使用 ML 特征
        effective_ml_dim = self.ml_feature_dim if self.ml_scaler is not None else 0

        for fold_idx in range(1, 6):
            model_path = os.path.join(model_dir, f'model_v3_fold_{fold_idx}.pth')

            if not os.path.exists(model_path):
                raise FileNotFoundError(f"模型文件不存在: {model_path}")

            try:
                model = BoronNMRNet_V3(
                    node_in_dim=self.node_dim,
                    edge_in_dim=self.edge_dim,
                    num_solvents=11,
                    solvent_dim=self.solvent_dim,
                    hidden_dim=self.hidden_dim,
                    dropout=self.dropout,
                    num_heads=4,
                    ml_feature_dim=effective_ml_dim,
                    ml_hidden_dim=self.ml_hidden_dim
                ).to(self.device)

                # 加载权重
                try:
                    model.load_state_dict(
                        torch.load(model_path, map_location=self.device, weights_only=True)
                    )
                except TypeError:
                    model.load_state_dict(
                        torch.load(model_path, map_location=self.device)
                    )

                model.eval()
                models.append(model)
                print(f"  ✓ 加载 model_v3_fold_{fold_idx}.pth")

            except Exception as e:
                raise Exception(f"加载 model_v3_fold_{fold_idx}.pth 失败: {e}")

        return models

    def _get_solvent_id(self, solvent_name):
        """将溶剂名称映射为整数 ID"""
        return SOLVENT_NAME_TO_ID.get(solvent_name, UNKNOWN_SOLVENT_ID)

    def _smiles_to_data(self, mol_smiles, solvent_name):
        """
        将 SMILES 转换为 PyG Data 对象 (V3 格式)

        Args:
            mol_smiles (str): 分子 SMILES
            solvent_name (str): 溶剂名称

        Returns:
            tuple: (data, mol, canonical_smiles)
        """
        try:
            # ========== STEP 1: 分子标准化 ==========
            temp_mol = Chem.MolFromSmiles(mol_smiles)
            if temp_mol is None:
                raise PredictionError(f"无效的分子 SMILES: {mol_smiles}")

            canonical_mol_smiles = Chem.MolToSmiles(
                temp_mol, canonical=True, isomericSmiles=True
            )
            mol = Chem.MolFromSmiles(canonical_mol_smiles)

            # ========== STEP 2: 计算 Gasteiger 电荷 ==========
            AllChem.ComputeGasteigerCharges(mol)

            # ========== STEP 3: 提取节点特征 ==========
            atom_feats = []
            boron_mask = []

            for atom in mol.GetAtoms():
                atom_feats.append(get_atom_features(atom))
                boron_mask.append(atom.GetSymbol() == 'B')

            x = torch.stack(atom_feats)
            mask_b = torch.tensor(boron_mask, dtype=torch.bool)

            if mask_b.sum() == 0:
                raise PredictionError("分子中不含硼原子！")

            # ========== STEP 4: 提取边特征 ==========
            edge_indices = []
            edge_attrs = []

            for bond in mol.GetBonds():
                i = bond.GetBeginAtomIdx()
                j = bond.GetEndAtomIdx()

                edge_indices.append([i, j])
                edge_indices.append([j, i])

                b_feat = get_bond_features(bond)
                edge_attrs.append(b_feat)
                edge_attrs.append(b_feat)

            if edge_indices:
                edge_index = torch.tensor(edge_indices, dtype=torch.long).t().contiguous()
                edge_attr = torch.stack(edge_attrs)
            else:
                edge_index = torch.empty((2, 0), dtype=torch.long)
                edge_attr = torch.empty((0, self.edge_dim), dtype=torch.float)

            # ========== STEP 5: 溶剂 ID ==========
            solvent_id = torch.tensor([self._get_solvent_id(solvent_name)], dtype=torch.long)

            # ========== STEP 6: ML 全局特征 ==========
            if self.ml_scaler is not None:
                ml_feats = compute_and_normalize(canonical_mol_smiles, self.ml_scaler, self.ml_medians)
                ml_global_features = torch.tensor(ml_feats, dtype=torch.float).unsqueeze(0)  # [1, 20]
            else:
                ml_global_features = None

            # ========== STEP 7: 打包 PyG Data 对象 ==========
            data = Data(
                x=x,
                edge_index=edge_index,
                edge_attr=edge_attr,
                mask_b=mask_b,
                solvent_id=solvent_id,
            )

            if ml_global_features is not None:
                data.ml_global_features = ml_global_features

            return data, mol, canonical_mol_smiles

        except PredictionError:
            raise
        except Exception as e:
            raise PredictionError(f"数据处理失败: {e}")

    def predict(self, mol_smiles, solvent_name):
        """
        执行集成预测

        Args:
            mol_smiles (str): 分子 SMILES
            solvent_name (str): 溶剂名称 (如 'CDCl3')

        Returns:
            dict: 预测结果
        """
        try:
            # ========== STEP 1: 数据预处理 ==========
            data, mol, canonical_smiles = self._smiles_to_data(mol_smiles, solvent_name)
            data = data.to(self.device)

            # ========== STEP 2: 模拟 Batch ==========
            batch = Batch.from_data_list([data])

            # ========== STEP 3: 集成推理（5 个模型） ==========
            fold_preds = []

            with torch.no_grad():
                for i, model in enumerate(self.models):
                    try:
                        # 准备 ML 全局特征
                        ml_feats = getattr(batch, 'ml_global_features', None)

                        pred = model(
                            batch.x,
                            batch.edge_index,
                            batch.edge_attr,
                            batch.solvent_id,
                            batch.mask_b,
                            batch.batch,
                            ml_global_features=ml_feats
                        )

                        if pred.ndim == 0:
                            pred = pred.view(1)

                        fold_preds.append(pred)

                    except Exception as e:
                        raise PredictionError(f"Fold {i+1} 预测失败: {e}")

            # ========== STEP 4: 取 5 个模型的平均值 ==========
            if not fold_preds:
                raise PredictionError("没有成功的模型预测")

            avg_pred = torch.stack(fold_preds).mean(dim=0)

            if avg_pred.ndim == 0:
                avg_pred = avg_pred.view(1)

            # ========== STEP 5: 映射预测值到原子索引 ==========
            boron_indices = torch.where(data.mask_b)[0].cpu().numpy()
            predictions_array = avg_pred.cpu().numpy()

            predictions = []
            for idx, ppm in zip(boron_indices, predictions_array):
                atom = mol.GetAtomWithIdx(int(idx))
                predictions.append({
                    'atom_index': int(idx),
                    'element': atom.GetSymbol(),
                    'ppm': float(ppm)
                })

            return {
                'canonical_smiles': canonical_smiles,
                'predictions': predictions,
                'num_borons': len(predictions),
                'mol_object': mol
            }

        except PredictionError:
            raise
        except Exception as e:
            raise PredictionError(f"预测过程异常: {e}")

    def generate_molecule_image(self, mol, boron_indices, predictions, output_dir):
        """生成高亮硼原子的分子图"""
        try:
            os.makedirs(output_dir, exist_ok=True)

            filename = f"prediction_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(output_dir, filename)

            highlight_atoms = list(boron_indices)
            atom_colors = {idx: (0.8, 0.9, 1.0) for idx in highlight_atoms}

            from rdkit.Chem.Draw import rdMolDraw2D

            drawer = rdMolDraw2D.MolDraw2DCairo(800, 600)

            opts = drawer.drawOptions()
            for pred in predictions:
                idx = pred['atom_index']
                opts.atomLabels[idx] = str(idx)

            drawer.DrawMolecule(
                mol,
                highlightAtoms=highlight_atoms,
                highlightAtomColors=atom_colors
            )
            drawer.FinishDrawing()

            with open(filepath, 'wb') as f:
                f.write(drawer.GetDrawingText())

            return filepath

        except Exception as e:
            raise Exception(f"分子图生成失败: {e}")
