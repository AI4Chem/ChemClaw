---
name: molecular_properties_predictor
description: 预测小分子多种物化性质（沸点、折射率、密度、黏度、表面张力等），当前已真实接入 bamboo_mixer 单分子物性模型后端。
trigger: ["molecular properties", "物性预测", "熔点", "沸点", "折射率", "介电常数", "表面张力", "密度", "黏度", "蒸气压"]
---

# Molecular Properties Predictor

## 功能概述

该 skill 用于预测**小分子多种物化性质**。

当前版本通过 Bamboo-Mixer 单分子模型返回以下 11 个性质：

- `Tm`：熔点（K）
- `bp`：沸点（K）
- `nD`：折射率（无单位）
- `nD_liquid`：液体折射率（无单位）
- `dc`：介电常数（无单位）
- `ST`：表面张力（mN/m）
- `density`：密度（g/cm^3）
- `vis`：黏度（cP）
- `vapP`：蒸气压（Pa）

---

## 适用场景

当用户有如下需求时适合调用：

- 查询一个分子的多种物化性质
- 一次性获取熔点、沸点、密度、黏度等多个性质
- 为下游分子筛选提供多指标输入
- 作为拆分单项物性 skill 之前的总入口

---

## 输入形式

### 单分子输入
- `smiles`：必填
- `name`：可选
- `temperature`：可选，默认 `25.0`

### 批量输入
支持 JSON 列表输入，每项至少包含：

- `smiles`
- `name`（可选）

---

## 输出字段

每个结果条目通常包含：

- `name`
- `smiles`
- `canonical_smiles`
- `status`
- `temperature_celsius`
- `backend_used`
- `model_source`
- `properties`
- `property_units`
- `raw_backend_output`

---

## ⚠️ pKa 预测特别说明

**本 skill 虽然输出 `pka_a` 和 `pka_b` 字段，但不推荐用于 pKa 预测。**

**推荐方案：** 请使用专门的 [`pka-predictor`](../pka-predictor/SKILL.md) skill 进行 pKa 预测。

**原因：**
| 对比项 | molecular-properties-predictor | pka-predictor |
|--------|-------------------------------|---------------|
| pKa 准确度 | 中等（误差 ~0.4 单位） | 高（误差 ~0.17 单位） |
| 后端 | Bamboo-Mixer 多任务模型 | Uni-pKa 专用模型 |
| 微观态处理 | 无 | 支持微观态枚举 + 自由能计算 |
| 输出详细度 | 仅返回数值 | 电荷态、去质子化方向、置信度等 |

**示例：**
```bash
# ❌ 不推荐：用本 skill 预测 pKa
python scripts/main_script.py --smiles "CC(=O)O" --name "乙酸"

# ✅ 推荐：用 pka-predictor 预测 pKa
cd ../pka-predictor && ./run_with_venv.sh --smiles "CC(=O)O" --name "乙酸" --backend unipka
```

---

## ⚠️ 表面张力预测特别说明

**本 skill 可预测表面张力 (`ST`)，但对于**单一表面张力预测**需求，推荐使用专门的 [`surface-tension-predictor`](../surface-tension-predictor/SKILL.md) skill。**

**推荐策略：**

| 需求场景 | 推荐 Skill/后端 |
|----------|-----------------|
| 仅预测表面张力 | `surface-tension-predictor` |
| 表面张力 + 多种物性 | `molecular-properties-predictor` (Bamboo-Mixer) |
| 小分子 (<10 重原子) | `surface-tension-predictor` (baseline) |
| 大分子 (≥10 重原子) | `surface-tension-predictor` (public_joblib) |

**原因：**
| 对比项 | molecular-properties-predictor | surface-tension-predictor |
|--------|-------------------------------|---------------------------|
| 表面张力准确度 | 好（误差 ~5%） | 好（误差 ~5% baseline） |
| 后端 | Bamboo-Mixer 多任务模型 | baseline / public_joblib |
| 特征数 | 隐式描述符 | 8 个 (baseline) / 130 个 (public_joblib) |
| 灵活性 | 固定 11 个性质 | 可切换后端，针对表面张力优化 |
| 适用场景 | 多种物性一次性预测 | 单一表面张力预测 |

**测试对比（苯甲酸）：**
| Skill/后端 | 预测值 | 文献值 | 偏差 |
|------------|--------|--------|------|
| surface-tension-predictor (baseline) | 41.63 mN/m | ~44 mN/m | -5.4% ✅ |
| molecular-properties-predictor (Bamboo) | 41.38 mN/m | ~44 mN/m | -5.9% ✅ |
| surface-tension-predictor (public_joblib) | 33.19 mN/m | ~44 mN/m | -24.6% ⚠️ |

**示例：**
```bash
# ✅ 推荐：仅预测表面张力，用 surface-tension-predictor
cd ../surface-tension-predictor
python scripts/main_script.py --smiles "O=C(O)c1ccccc1" --name "苯甲酸" --backend baseline

# ✅ 推荐：同时预测多种物性，用本 skill
cd ../molecular-properties-predictor
python scripts/main_script.py --smiles "O=C(O)c1ccccc1" --properties bp,ST,density
```

---

## 后端说明

## bamboo_mixer

### 定位
这是当前 skill 的真实模型后端，用于对接 Bamboo-Mixer 单分子物性模型。

### 当前已完成的真实接入链路
当前版本已完成以下流程：

1. 准备单分子输入 JSON
2. 调用 Bamboo-Mixer 的：
   - `scripts/prepare_data/prepare_data.py --data_type mono`
3. 调用 Bamboo-Mixer 的：
   - `scripts/test_results/mono.py`
4. 使用 mono checkpoint：
   - `hf_bamboo_mixer/ckpts/mono/optimal.pt`
5. 解析输出 `output_mono.json`
6. 返回 11 个物性结果

### 当前使用的环境变量

- `BAMBOO_MIXER_ADAPTER_PY`
- `BAMBOO_MIXER_REPO`
- `BAMBOO_MIXER_PYTHON`
- `BAMBOO_MIXER_MONO_CKPT`

推荐写法：

```bash
export BAMBOO_MIXER_ADAPTER_PY=scripts/adapters/bamboo_mixer_properties_adapter.py
export BAMBOO_MIXER_REPO=assets/bamboo_mixer
export BAMBOO_MIXER_PYTHON=assets/bamboo_mixer/.venv/bin/python
export BAMBOO_MIXER_MONO_CKPT=assets/bamboo_mixer/hf_bamboo_mixer/ckpts/mono/optimal.pt
```