#!/usr/bin/env python3
"""
ADME 模型训练脚本 - 使用真实 TDC 数据
完整训练所有 6 个 ADME 性质预测模型
"""

import argparse
import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

try:
    from tdc.single_pred import ADME
    HAS_TDC = True
    print("✓ TDC 库已安装")
except ImportError as e:
    HAS_TDC = False
    print(f"✗ TDC 库未安装：{e}")
    print("  请运行：pip install PyTDC")

from rdkit import Chem
from rdkit.Chem import AllChem, Descriptors
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier, GradientBoostingRegressor, GradientBoostingClassifier
from sklearn.model_selection import cross_val_score, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error, roc_auc_score, accuracy_score, classification_report
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class ADMEModelTrainer:
    """ADME 模型训练器 - 使用 TDC 真实数据"""
    
    # TDC 数据集配置
    DATASETS = {
        'Caco2_Wang': {
            'type': 'regression', 
            'description': 'Caco-2 细胞有效通透性',
            'unit': 'log Papp (10^-6 cm/s)',
            'metric': 'R²'
        },
        'PAMPA_NCATS': {
            'type': 'classification', 
            'description': 'PAMPA 通透性',
            'classes': ['Low-Moderate', 'High'],
            'metric': 'AUC'
        },
        'HIA_Hou': {
            'type': 'classification', 
            'description': '人体肠道吸收',
            'classes': ['Inactive', 'Active'],
            'metric': 'AUC'
        },
        'Pgp_Broccatelli': {
            'type': 'classification', 
            'description': 'P-糖蛋白抑制',
            'classes': ['Non-inhibitor', 'Inhibitor'],
            'metric': 'AUC'
        },
        'Bioavailability_Ma': {
            'type': 'classification', 
            'description': '口服生物利用度',
            'classes': ['Low', 'High'],
            'metric': 'AUC'
        },
        'Lipophilicity_AstraZeneca': {
            'type': 'regression', 
            'description': '亲脂性',
            'unit': 'logD',
            'metric': 'R²'
        },
    }
    
    def __init__(self, model_dir: str = 'models', cache_dir: str = 'data_cache'):
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 分子指纹参数
        self.fingerprint_radius = 2  # ECFP4
        self.fingerprint_nbits = 2048
        
        # 模型参数
        self.n_estimators = 200
        self.max_depth = 15
        self.min_samples_split = 5
        self.min_samples_leaf = 2
        
        print(f"\n📁 模型输出目录：{self.model_dir.absolute()}")
        print(f"📁 数据缓存目录：{self.cache_dir.absolute()}")
    
    def smiles_to_fingerprint(self, smiles: str) -> Optional[np.ndarray]:
        """将 SMILES 转换为 Morgan 指纹 (ECFP4)"""
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            
            fp = AllChem.GetMorganFingerprintAsBitVect(
                mol, 
                radius=self.fingerprint_radius,
                nBits=self.fingerprint_nbits
            )
            return np.array(fp)
        except:
            return None
    
    def download_and_cache_data(self, dataset_name: str) -> pd.DataFrame:
        """从 TDC 下载数据并缓存到本地"""
        cache_file = self.cache_dir / f"{dataset_name}.csv"
        
        # 检查缓存
        if cache_file.exists():
            print(f"  ✓ 从缓存加载：{cache_file}")
            return pd.read_csv(cache_file)
        
        # 下载新数据
        if not HAS_TDC:
            raise ImportError("TDC 库未安装")
        
        print(f"  📥 正在从 TDC 下载 {dataset_name} 数据集...")
        data = ADME(name=dataset_name)
        df = data.get_data()
        
        # 保存到缓存
        df.to_csv(cache_file, index=False)
        print(f"  ✓ 下载完成：{len(df)} 个样本")
        print(f"  ✓ 已缓存到：{cache_file}")
        
        return df
    
    def prepare_data(self, df: pd.DataFrame, 
                    smiles_col: str = None, 
                    target_col: str = None) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """准备训练数据"""
        # 自动检测列名
        if smiles_col is None:
            # 尝试常见的 SMILES 列名
            for col in ['Drug', 'SMILES', 'smiles', 'Molecule', 'Structure']:
                if col in df.columns:
                    smiles_col = col
                    break
        
        if target_col is None:
            # 尝试常见的目标列名
            for col in ['Y', 'y', 'Target', 'target', 'Value', 'value', 'Label', 'label']:
                if col in df.columns:
                    target_col = col
                    break
        
        if smiles_col is None or target_col is None:
            print(f"  ⚠️  列名检测失败，可用列：{list(df.columns)}")
            return None, None, None
        
        X = []
        y = []
        valid_smiles = []
        invalid = 0
        
        for idx, row in df.iterrows():
            smiles = row[smiles_col]
            fp = self.smiles_to_fingerprint(smiles)
            
            if fp is not None:
                X.append(fp)
                y.append(row[target_col])
                valid_smiles.append(smiles)
            else:
                invalid += 1
        
        print(f"  ✓ 有效样本：{len(X)}, 无效样本：{invalid}")
        return np.array(X), np.array(y), valid_smiles
    
    def train_model(self, X_train: np.ndarray, y_train: np.ndarray, 
                   model_type: str = 'regression',
                   use_cv: bool = True) -> object:
        """训练优化的模型"""
        
        # 选择模型类型
        if model_type == 'regression':
            base_model = RandomForestRegressor(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                random_state=42,
                n_jobs=-1
            )
        else:  # classification
            base_model = RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=self.max_depth,
                min_samples_split=self.min_samples_split,
                min_samples_leaf=self.min_samples_leaf,
                random_state=42,
                n_jobs=-1
            )
        
        print(f"  🚀 开始训练模型...")
        print(f"     训练样本数：{len(X_train)}")
        print(f"     特征维度：{X_train.shape[1]}")
        
        # 训练
        model = base_model
        model.fit(X_train, y_train)
        
        # 交叉验证
        if use_cv and len(X_train) > 50:
            print(f"  📊 进行 5 折交叉验证...")
            cv_scores = cross_val_score(model, X_train, y_train, cv=5, n_jobs=-1)
            print(f"     CV 得分：{cv_scores.mean():.3f} ± {cv_scores.std():.3f}")
        
        print(f"  ✓ 训练完成")
        return model
    
    def evaluate_model(self, model: object, X_test: np.ndarray, y_test: np.ndarray,
                      model_type: str = 'regression') -> Dict[str, float]:
        """评估模型性能"""
        y_pred = model.predict(X_test)
        
        metrics = {}
        if model_type == 'regression':
            metrics['R²'] = r2_score(y_test, y_pred)
            metrics['RMSE'] = np.sqrt(mean_squared_error(y_test, y_pred))
            metrics['MAE'] = mean_squared_error(y_test, y_pred, squared=False)
        else:
            if len(np.unique(y_test)) > 1:
                metrics['AUC'] = roc_auc_score(y_test, y_pred)
            metrics['Accuracy'] = accuracy_score(y_test, y_pred)
        
        return metrics
    
    def save_model(self, model: object, dataset_name: str, metadata: Dict = None):
        """保存模型和元数据"""
        # 保存模型
        model_path = self.model_dir / f"{dataset_name}.pkl"
        with open(model_path, 'wb') as f:
            pickle.dump(model, f)
        print(f"  ✓ 模型已保存：{model_path}")
        
        # 保存元数据
        if metadata:
            meta_path = self.model_dir / f"{dataset_name}_metadata.json"
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            print(f"  ✓ 元数据已保存：{meta_path}")
    
    def train_dataset(self, dataset_name: str) -> Dict:
        """训练单个数据集"""
        print(f"\n{'='*70}")
        print(f"训练 {dataset_name}")
        print(f"{'='*70}")
        
        info = self.DATASETS[dataset_name]
        print(f"描述：{info['description']}")
        print(f"类型：{info['type']}")
        
        try:
            # 1. 下载数据
            df = self.download_and_cache_data(dataset_name)
            
            # 2. 准备数据
            X, y, valid_smiles = self.prepare_data(df)
            if X is None or len(X) < 50:
                print(f"  ✗ 数据量不足，跳过")
                return {'success': False, 'error': 'Insufficient data'}
            
            # 3. 划分训练/测试集 (80/20)
            n_test = int(len(X) * 0.2)
            indices = np.random.permutation(len(X))
            X_train, X_test = X[indices[:-n_test]], X[indices[-n_test:]]
            y_train, y_test = y[indices[:-n_test]], y[indices[-n_test:]]
            
            print(f"  训练集：{len(X_train)} 样本")
            print(f"  测试集：{len(X_test)} 样本")
            
            # 4. 训练模型
            model = self.train_model(X_train, y_train, info['type'])
            
            # 5. 评估模型
            print(f"  📈 评估模型性能...")
            train_metrics = self.evaluate_model(model, X_train, y_train, info['type'])
            test_metrics = self.evaluate_model(model, X_test, y_test, info['type'])
            
            print(f"  训练集性能:")
            for metric, value in train_metrics.items():
                print(f"    {metric}: {value:.3f}")
            
            print(f"  测试集性能:")
            for metric, value in test_metrics.items():
                print(f"    {metric}: {value:.3f}")
            
            # 6. 保存模型
            metadata = {
                'dataset': dataset_name,
                'description': info['description'],
                'type': info['type'],
                'unit': info.get('unit', ''),
                'training_date': datetime.now().isoformat(),
                'n_train': len(X_train),
                'n_test': len(X_test),
                'train_metrics': train_metrics,
                'test_metrics': test_metrics,
                'fingerprint': {
                    'radius': self.fingerprint_radius,
                    'nbits': self.fingerprint_nbits
                },
                'model_params': {
                    'n_estimators': self.n_estimators,
                    'max_depth': self.max_depth,
                    'min_samples_split': self.min_samples_split,
                    'min_samples_leaf': self.min_samples_leaf
                }
            }
            
            self.save_model(model, dataset_name, metadata)
            
            # 7. 打印性能总结
            primary_metric = info['metric']
            test_value = test_metrics.get(primary_metric, 0)
            
            print(f"\n  📊 性能总结 ({primary_metric}):")
            if info['type'] == 'regression':
                if test_value >= 0.8:
                    print(f"     ⭐⭐⭐⭐⭐ 优秀 ({test_value:.3f})")
                elif test_value >= 0.7:
                    print(f"     ⭐⭐⭐⭐ 良好 ({test_value:.3f})")
                elif test_value >= 0.6:
                    print(f"     ⭐⭐⭐ 中等 ({test_value:.3f})")
                else:
                    print(f"     ⭐⭐ 需改进 ({test_value:.3f})")
            else:
                if test_value >= 0.9:
                    print(f"     ⭐⭐⭐⭐⭐ 优秀 ({test_value:.3f})")
                elif test_value >= 0.8:
                    print(f"     ⭐⭐⭐⭐ 良好 ({test_value:.3f})")
                elif test_value >= 0.7:
                    print(f"     ⭐⭐⭐ 中等 ({test_value:.3f})")
                else:
                    print(f"     ⭐⭐ 需改进 ({test_value:.3f})")
            
            return {
                'success': True,
                'dataset': dataset_name,
                'metrics': test_metrics,
                'n_train': len(X_train),
                'n_test': len(X_test)
            }
            
        except Exception as e:
            print(f"  ✗ 训练失败：{e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def train_all(self):
        """训练所有 ADME 模型"""
        print("\n" + "="*70)
        print("🚀 ADME 模型训练 - 使用 TDC 真实数据")
        print("="*70)
        print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"模型目录：{self.model_dir.absolute()}")
        print(f"缓存目录：{self.cache_dir.absolute()}")
        
        results = []
        
        for dataset_name in self.DATASETS.keys():
            result = self.train_dataset(dataset_name)
            results.append(result)
        
        # 打印总结
        print("\n" + "="*70)
        print("📊 训练总结")
        print("="*70)
        
        successful = [r for r in results if r.get('success')]
        failed = [r for r in results if not r.get('success')]
        
        print(f"成功：{len(successful)}/{len(results)}")
        print(f"失败：{len(failed)}/{len(results)}")
        
        if successful:
            print("\n✅ 成功训练的模型:")
            for r in successful:
                metrics = r.get('metrics', {})
                primary = list(metrics.keys())[0] if metrics else 'N/A'
                value = metrics.get(primary, 0)
                print(f"  ✓ {r['dataset']}: {primary} = {value:.3f} (n={r['n_train']})")
        
        if failed:
            print("\n❌ 失败的模型:")
            for r in failed:
                print(f"  ✗ {r.get('dataset', 'Unknown')}: {r.get('error', 'Unknown error')}")
        
        print(f"\n结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*70)
        
        return results


def main():
    parser = argparse.ArgumentParser(
        description='训练 ADME 模型 - 使用 TDC 真实数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                          # 训练所有模型
  %(prog)s -d Caco2_Wang            # 只训练 Caco-2 模型
  %(prog)s -d all -o ./models       # 训练所有，指定输出目录
        """
    )
    
    parser.add_argument('-d', '--dataset', type=str, default='all',
                       help='数据集名称，或"all"训练所有')
    parser.add_argument('-o', '--output-dir', type=str, default='models',
                       help='模型输出目录')
    parser.add_argument('-c', '--cache-dir', type=str, default='data_cache',
                       help='数据缓存目录')
    parser.add_argument('--n-estimators', type=int, default=200,
                       help='树的数量 (默认 200)')
    parser.add_argument('--max-depth', type=int, default=15,
                       help='最大深度 (默认 15)')
    
    args = parser.parse_args()
    
    # 创建训练器
    trainer = ADMEModelTrainer(
        model_dir=args.output_dir,
        cache_dir=args.cache_dir
    )
    
    # 设置模型参数
    trainer.n_estimators = args.n_estimators
    trainer.max_depth = args.max_depth
    
    # 训练
    if args.dataset == 'all':
        trainer.train_all()
    else:
        # 训练单个数据集
        if args.dataset in trainer.DATASETS:
            trainer.train_dataset(args.dataset)
        else:
            print(f"✗ 未知数据集：{args.dataset}")
            print(f"可用数据集：{list(trainer.DATASETS.keys())}")


if __name__ == '__main__':
    main()
