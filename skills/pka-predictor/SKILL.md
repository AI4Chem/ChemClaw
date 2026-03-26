---
name: pka_predictor
description: 预测小分子的 pKa，支持 custom 启发式后端和 Uni-pKa 单文件权重后端（Bohrium notebook 路线）。
trigger: ["pKa", "酸度常数", "电离常数", "acidic pKa", "basic pKa", "macro pKa", "microstate", "protonation", "deprotonation", "质子化", "去质子化"]
---

# pKa Predictor

预测小分子的 pKa，支持两类后端：

- **custom**：基于规则、官能团和可选自定义模型的本地预测
- **unipka**：基于 **Uni-pKa Bohrium notebook 单文件权重路线** 的微观态枚举 + 自由能汇总预测

## ⚡ 快速开始（首次使用必读）

### 1. 安装依赖

```bash
cd skills/pka-predictor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. 下载 Uni-pKa 模型权重（仅 unipka 后端需要）

**使用 Hugging Face CLI（推荐）：**

```bash
# 安装 huggingface_hub（如果尚未安装）
pip install huggingface_hub

# 下载模型权重文件
mkdir -p skills/pka-predictor/assets/Uni-pKa/uni-pka-ckpt_v2
hf download Lai-ao/uni-pka-ckpt_v2 t_dwar_v_novartis_a_b.pt \
  --repo-type model \
  --local-dir skills/pka-predictor/assets/Uni-pKa/uni-pka-ckpt_v2

# 下载模板文件（如果本地没有）
hf download Lai-ao/uni-pka-ckpt_v2 smarts_pattern.tsv \
  --repo-type model \
  --local-dir skills/pka-predictor/assets/Uni-pKa/uni-pka-ckpt_v2

hf download Lai-ao/uni-pka-ckpt_v2 simple_smarts_pattern.tsv \
  --repo-type model \
  --local-dir skills/pka-predictor/assets/Uni-pKa/uni-pka-ckpt_v2
```

**或手动下载：**

访问 https://huggingface.co/Lai-ao/uni-pka-ckpt_v2 下载以下文件到 `assets/Uni-pKa/uni-pka-ckpt_v2/` 目录：
- `t_dwar_v_novartis_a_b.pt`（~571MB，模型权重）
- `smarts_pattern.tsv`（SMARTS 模板）
- `simple_smarts_pattern.tsv`（简化 SMARTS 模板）

### 3. 验证安装

```bash
# 测试 custom 后端
./scripts/run_with_venv.sh --smiles "CC(=O)O" --name "乙酸" --backend custom

# 测试 unipka 后端
./scripts/run_with_venv.sh --smiles "CC(=O)O" --name "乙酸" --backend unipka --cpu
```

## 触发条件

当用户有以下需求时适合调用：

- 预测某个分子的 pKa
- 估算 strongest acidic/basic pKa
- 比较几个分子的电离性质
- 查看不同电荷态之间的 pKa 转换
- 分析质子化 / 去质子化行为

## 功能

- ✅ 支持单个 SMILES 输入
- ✅ 支持批量文件输入（`.smi` / `.txt` / `.csv` / `.json`）
- ✅ 支持 JSON / CSV / TXT 输出
- ✅ custom 后端支持官能团识别与启发式预测
- ✅ unipka 后端支持模板枚举微观态并基于单文件权重做自由能预测
- ✅ 返回结构化结果，便于 OpenClaw 解析

## 后端说明

### custom
适合本地快速使用，不依赖 Uni-pKa 环境。  
输出主要是启发式 strongest acidic/basic pKa。

### unipka
基于 Bohrium notebook 单权重流程，而不是 GitHub 仓库中 `infer_pka.sh` 的 5-fold 推理流程。  
它的基本逻辑是：

1. 使用模板文件枚举相邻电荷态的微观态
2. 用单文件权重模型预测各微观态自由能
3. 对相邻电荷态使用 Boltzmann / log-sum-exp 汇总
4. 得到相邻电荷态之间的 **macro pKa transitions**

因此，`unipka` 输出中最重要的是：

- `dominant_neutral_to_anion_pka`
- `dominant_cation_to_neutral_pka`
- `all_predictions`（每一步 `from_charge -> to_charge`）

## 使用方法

### 对话中使用

- 预测乙酸的 pKa
- 这个 SMILES 的 pKa 是多少：`CC(=O)O`
- 比较这两个分子的电离性质
- 这个分子的去质子化 pKa 是多少

### 命令行使用

**一键安装（首次使用）：**

```bash
# 运行安装脚本（自动下载模型和模板文件）
./scripts/setup_models.sh
```

**使用虚拟环境（推荐，支持 UniPKA 后端）：**

```bash
# 使用包装脚本（自动激活虚拟环境）
./scripts/run_with_venv.sh --smiles "CC(=O)O" --name "乙酸"

# unipka 后端（使用默认单文件权重与模板）
./scripts/run_with_venv.sh --smiles "CC(=O)O" --name "乙酸" --backend unipka --cpu

# 显式指定模型与模板
./scripts/run_with_venv.sh \
  --smiles "CC(=O)O" \
  --name "乙酸" \
  --backend unipka \
  --model "assets/Uni-pKa/uni-pka-ckpt_v2/t_dwar_v_novartis_a_b.pt" \
  --template "assets/Uni-pKa/uni-pka-ckpt_v2/smarts_pattern.tsv" \
  --cpu
```

**直接运行（仅 Custom 后端）：**

```bash
# custom 后端
python3 scripts/predict_pka.py --smiles "CC(=O)O" --name "乙酸" --backend custom
```

---

## 🔧 调试指南

### 推荐调试环境

**方案 1：虚拟环境（推荐）**
```bash
cd skills/pka-predictor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**方案 2：Conda 环境**
```bash
conda create -n pka-predictor python=3.12
conda activate pka-predictor
pip install -r requirements.txt
```

### 常见错误及解决方案

| 错误 | 解决方案 |
|------|----------|
| `No module named 'pandas'` | `pip install pandas` |
| `No module named 'scipy'` | `pip install scipy` |
| `No module named 'torch'` | `pip install torch` |
| RDKit 导入失败 | `pip uninstall rdkit && pip install rdkit` |

### 调试技巧

**启用详细输出：**
```bash
./scripts/run_with_venv.sh --smiles "CC(=O)O" --verbose
```

**交互式调试：**
```python
from scripts.backends.custom_backend import CustomBackend
backend = CustomBackend()
result = backend.predict("CC(=O)O", "乙酸")
print(result)
```

**检查依赖版本：**
```bash
python3 -c "import rdkit, pandas, torch; print(rdkit.__version__, pandas.__version__, torch.__version__)"
```

### 测试命令

**基础测试：**
```bash
# custom 后端
./scripts/run_with_venv.sh --smiles "CC(=O)O" --backend custom

# unipka 后端
./scripts/run_with_venv.sh --smiles "CC(=O)O" --backend unipka --cpu
```

**批量测试：**
```bash
cat > test_compounds.smi << EOF
CC(=O)O 乙酸
c1ccccc1O 苯酚
CCO 乙醇
EOF
./scripts/run_with_venv.sh --input test_compounds.smi --output results.json
```