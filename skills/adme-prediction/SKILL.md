---
name: adme-prediction
description: ADME 性质预测工具。预测分子的吸收、分布、代谢、排泄性质，包括 Caco-2 通透性、PAMPA、HIA、Pgp 抑制、生物利用度、亲脂性等。使用 Morgan 指纹 + Random Forest/XGBoost。当用户提到 ADME 预测、药物性质、通透性、吸收、代谢等时触发。
---

# ADME Prediction

ADME（吸收、分布、代谢、排泄）性质预测技能，用于药物发现和开发早期的药物动力学性质评估。

## 支持的 ADME 性质

| 性质 | 数据集 | 类型 | 说明 |
|------|--------|------|------|
| **Caco-2 通透性** | Caco2_Wang | 回归 | 预测 Caco-2 细胞有效通透性 (log Papp) |
| **PAMPA 通透性** | PAMPA_NCATS | 分类 | 预测人工膜通透性 (高/低 - 中) |
| **肠道吸收** | HIA_Hou | 分类 | 预测人体肠道吸收 (活性/非活性) |
| **Pgp 抑制** | Pgp_Broccatelli | 分类 | 预测 P-糖蛋白抑制 (抑制剂/非抑制剂) |
| **生物利用度** | Bioavailability_Ma | 分类 | 预测口服生物利用度 (高/低) |
| **亲脂性** | Lipophilicity_AstraZeneca | 回归 | 预测亲脂性 (logD) |

## 使用方法

### 对话框中使用

用户可以直接提供 SMILES 并要求预测：

```
预测这个分子的 ADME 性质：CCO
计算 Caco-2 通透性：c1ccccc1
这个化合物的肠道吸收怎么样？CC(=O)O
预测 Pgp 抑制活性：CCN(CC)CC
```

### 命令行使用

```bash
# 预测单个分子
python3 scripts/adme_predictor.py --smiles "CCO"

# 预测特定性质
python3 scripts/adme_predictor.py --smiles "c1ccccc1" --property Caco2_Wang

# 批量预测（从文件读取 SMILES）
python3 scripts/adme_predictor.py --file molecules.smi --output results.json

# 列出所有可用性质
python3 scripts/adme_predictor.py --list

# JSON 输出
python3 scripts/adme_predictor.py --smiles "CCO" --json
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--smiles` | `-s` | SMILES 字符串 | 必需（或 --file） |
| `--file` | `-f` | 包含 SMILES 的文件（每行一个） | 必需（或 --smiles） |
| `--property` | `-p` | 要预测的性质（可多个） | 全部 |
| `--output` | `-o` | 输出文件路径 | 标准输出 |
| `--json` | `-j` | 以 JSON 格式输出 | 表格格式 |
| `--list` | `-l` | 列出所有可用性质 | - |
| `--model-dir` | `-m` | 模型目录 | 默认模型目录 |

## 工作流程

### 1. 分子输入

支持多种输入方式：

```python
# 单个 SMILES
smiles = "CCO"

# 从文件读取
with open("molecules.smi") as f:
    smiles_list = [line.strip() for line in f]

# 从其他格式转换
from rdkit import Chem
mol = Chem.MolFromMolFile("input.mol")
smiles = Chem.MolToSmiles(mol)
```

### 2. 指纹计算

使用 Morgan 指纹（ECFP4）表示分子：

```python
from rdkit.Chem import AllChem

fp = AllChem.GetMorganFingerprintAsBitVect(
    mol, 
    radius=2,      # ECFP4
    nBits=2048     # 指纹长度
)
```

### 3. 性质预测

加载预训练模型进行预测：

```python
# 加载模型
import pickle
with open("models/Caco2_Wang.pkl", "rb") as f:
    model = pickle.load(f)

# 预测
prediction = model.predict([fp])[0]
```

## 输出示例

### 单个分子预测

```bash
$ python3 scripts/adme_predictor.py --smiles "CCO" --json

{
  "smiles": "CCO",
  "predictions": {
    "Caco2_Wang": {
      "value": -0.52,
      "type": "regression",
      "unit": "log Papp (10^-6 cm/s)",
      "description": "Caco-2 细胞有效通透性"
    },
    "HIA_Hou": {
      "class": "Active",
      "probability": 0.89,
      "type": "classification",
      "description": "人体肠道吸收"
    },
    "Lipophilicity_AstraZeneca": {
      "value": -0.31,
      "type": "regression",
      "unit": "logD",
      "description": "亲脂性"
    }
  }
}
```

### 表格输出

```
SMILES: CCO (乙醇)

ADME 性质预测结果:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
性质                    预测值          置信度
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Caco-2 通透性           -0.52          -
PAMPA 通透性            High           0.78
肠道吸收 (HIA)          Active         0.89
Pgp 抑制                Non-inhibitor  0.92
生物利用度              High           0.85
亲脂性 (logD)           -0.31          -
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 批量预测

```bash
$ python3 scripts/adme_predictor.py --file drugs.smi -o results.csv

✓ 已处理：10/10 分子
✓ 输出：results.csv

$ cat results.csv
smiles,Caco2_Wang,HIA_Hou,Lipophilicity
CCO,-0.52,Active,-0.31
c1ccccc1,0.23,Active,2.15
CC(=O)O,-0.71,Active,-0.17
```

## 依赖

### 必需依赖

```bash
pip install rdkit scikit-learn pandas numpy
```

### 可选依赖（推荐）

```bash
# XGBoost（更好的性能）
pip install xgboost

# TDC（下载训练数据）
pip install PyTDC
```

### 检查安装

```bash
# 检查 RDKit
python3 -c "from rdkit import Chem; print('RDKit OK')"

# 检查 scikit-learn
python3 -c "from sklearn.ensemble import RandomForestClassifier; print('sklearn OK')"
```

## 模型训练

### 下载 TDC 数据

```python
from tdc.single_pred import ADME

# 下载 Caco-2 数据集
data = ADME(name='Caco2_Wang')
df = data.get_data()

# 获取数据分割
split = data.get_split()
train_df = data.get_split()['train']
```

### 训练模型

```bash
# 训练 Caco-2 模型
python3 scripts/adme_train.py \
  --property Caco2_Wang \
  --data data/caco2_train.csv \
  --output models/Caco2_Wang.pkl

# 训练所有模型
python3 scripts/adme_train.py --all --data-dir ./tdc_data/ --output-dir ./models/
```

### 训练参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--property` | 要训练的性质 | 必需 |
| `--data` | 训练数据 CSV | 必需 |
| `--output` | 输出模型路径 | 必需 |
| `--model-type` | 模型类型 (rf/xgboost) | rf |
| `--n-estimators` | 树的数量 | 100 |
| `--max-depth` | 最大深度 | 10 |

## ADME 性质详解

### Caco-2 通透性 (Caco2_Wang)

**说明**: Caco-2 细胞系用于模拟人体肠道组织，预测药物口服吸收能力。

**单位**: log Papp (10^-6 cm/s)

**解释**:
>
- > -5.0: 高通透性（吸收良好）
- -6.0 to -5.0: 中等通透性
- < -6.0: 低通透性（吸收差）

### PAMPA 通透性 (PAMPA_NCATS)

**说明**: 平行人工膜通透性测定，高通量筛选药物渗透性。

**类别**:

- `High`: 高通透性
- `Low-Moderate`: 低 - 中等通透性

### 人体肠道吸收 (HIA_Hou)

**说明**: 预测药物从胃肠道吸收到血液的能力。

**类别**:

- `Active`: 吸收良好
- `Inactive`: 吸收差

### P-糖蛋白抑制 (Pgp_Broccatelli)

**说明**: Pgp 是 ABC 转运蛋白，影响药物代谢和脑渗透。

**类别**:

- `Inhibitor`: Pgp 抑制剂（可能影响其他药物代谢）
- `Non-inhibitor`: 非抑制剂

### 口服生物利用度 (Bioavailability_Ma)

**说明**: 预测药物口服后到达作用部位的比例。

**类别**:

- `High`: 生物利用度高（>50%）
- `Low`: 生物利用度低

### 亲脂性 (Lipophilicity_AstraZeneca)

**说明**: 预测药物在脂质环境中的溶解能力。

**单位**: logD

**解释**:

- 过高：代谢快、溶解度差
- 过低：膜通透性差
- 理想范围：1-3

## 与其他化学技能配合

### 与 mol_2d_viewer 配合

```bash
# 1. 预测 ADME 性质
python3 scripts/adme_predictor.py --smiles "CCO" -o adme_results.json

# 2. 生成 2D 结构图
python3 ../mol-2d-viewer/scripts/mol_2d_viewer.py --smiles "CCO" --output structure.png
```

### 与 smiles_to_iupac 配合

```bash
# 1. SMILES 转 IUPAC 名称
python3 ../smiles-to-iupac/scripts/smiles_to_iupac.py --smiles "CCO"

# 2. 预测 ADME 性质
python3 scripts/adme_predictor.py --smiles "CCO"
```

### 与 mol_paper_renderer 配合

```bash
# 1. 预测性质
python3 scripts/adme_predictor.py --smiles "CCO" --json > adme.json

# 2. 生成论文级渲染图
python3 ../mol-paper-renderer/scripts/mol_paper_renderer.py \
  --smiles "CCO" \
  --output ethanol_figure.svg \
  --caption "Ethanol: ADME properties predicted"
```

## 常见问题

### Q: 预测结果不准确怎么办？

A:

- 检查分子是否在训练数据范围内（类似结构）
- 尝试使用 XGBoost 模型（通常更准确）
- 考虑使用集成方法（多个模型平均）

### Q: 如何评估模型质量？

A: 使用 TDC 提供的 scaffold split 进行评估：

```python
from sklearn.metrics import roc_auc_score, mean_squared_error

# 分类任务
auc = roc_auc_score(y_true, y_pred)

# 回归任务
rmse = mean_squared_error(y_true, y_pred, squared=False)
```

### Q: 支持大分子（蛋白质、抗体）吗？

A: 当前版本仅支持小分子。大分子需要使用专门的模型（如 Developability 预测）。

### Q: 如何自定义模型参数？

A: 修改训练脚本中的模型配置：

```python
model = RandomForestClassifier(
    n_estimators=200,  # 增加树的数量
    max_depth=15,      # 增加深度
    class_weight='balanced'  # 处理类别不平衡
)
```

## 注意事项

- ✅ **快速预测** - 每个分子 <100ms
- ✅ **批量处理** - 支持数千分子批量预测
- ✅ **置信度评估** - 分类任务提供概率
- ✅ **TDC 兼容** - 使用标准数据集和分割方法
- ⚠️ **小分子限制** - 仅适用于小分子药物
- ⚠️ **结构相似性** - 对训练集外结构预测可能不准确
- ⚠️ **实验验证** - 预测结果需实验验证

## 错误处理

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| `Invalid SMILES` | SMILES 格式错误 | 检查 SMILES 语法 |
| `Model not found` | 模型文件缺失 | 运行训练脚本 |
| `RDKit error` | 分子处理失败 | 检查分子是否有效 |
| `Property not supported` | 不支持的性质 | 使用 --list 查看可用性质 |

## 性能参考

| 分子数量 | 预测时间（单线程） | 预测时间（多线程） |
|----------|-------------------|-------------------|
| 1 | <0.1s | <0.1s |
| 10 | 0.5s | 0.2s |
| 100 | 5s | 1s |
| 1000 | 50s | 10s |

## 数据来源

所有数据集来自 [Therapeutics Data Commons (TDC)](https://tdcommons.ai/single_pred_tasks/adme/)

**引用**:

```
@article{huang2022therapeutics,
  title={Therapeutics Data Commons: Machine Learning Datasets and Tasks for Drug Discovery and Development},
  author={Huang, Kexin and Fu, Tianfan and Gao, Wenhao and Zhao, Yu and Roohani, Yusuf and Leskovec, Jure},
  journal={Nature Chemical Biology},
  year={2022}
}
```

## 输出文件位置

默认输出到当前目录，或使用 `--output` 指定：

```bash
python3 scripts/adme_predictor.py --smiles "CCO" -o ./output/adme_results.json
```

对于飞书兼容性，建议输出到白名单目录：

- `~/.openclaw/media/adme-prediction/`
- `~/.openclaw/workspace/`
