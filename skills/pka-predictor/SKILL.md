---
name: pka_predictor
description: 预测小分子的 pKa，支持 custom 启发式后端和 Uni-pKa 单文件权重后端（Bohrium notebook 路线）。
trigger: ["pKa", "酸度常数", "电离常数", "acidic pKa", "basic pKa", "macro pKa", "microstate", "protonation", "deprotonation", "质子化", "去质子化"]
---

# pKa Predictor

预测小分子的 pKa，支持两类后端：

- **custom**：基于规则、官能团和可选自定义模型的本地预测
- **unipka**：基于 **Uni-pKa Bohrium notebook 单文件权重路线** 的微观态枚举 + 自由能汇总预测

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

**使用虚拟环境（推荐，支持 UniPKA 后端）：**

```bash
# 使用包装脚本（自动激活虚拟环境）
./run_with_venv.sh --smiles "CC(=O)O" --name "乙酸"

# unipka 后端（使用默认单文件权重与模板）
./run_with_venv.sh --smiles "CC(=O)O" --name "乙酸" --backend unipka --cpu

# 显式指定模型与模板
./run_with_venv.sh \
  --smiles "CC(=O)O" \
  --name "乙酸" \
  --backend unipka \
  --model "Uni-pKa/uni-pka-ckpt_v2/t_dwar_v_novartis_a_b.pt" \
  --template "Uni-pKa/uni-pka-ckpt_v2/smarts_pattern.tsv" \
  --cpu
```

**直接运行（仅 Custom 后端）：**

```bash
# custom 后端
python3 scripts/predict_pka.py --smiles "CC(=O)O" --name "乙酸" --backend custom