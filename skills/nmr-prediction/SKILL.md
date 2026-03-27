---
name: nmr-prediction
description: Predict liquid-phase ¹H and ¹³C NMR chemical shifts from a SMILES string using NMRNet (deep learning, SE(3)-Transformer). Outputs per-atom shift values (ppm) and Lorentzian-broadened spectrum PNG files.
---

# NMR Chemical Shift Prediction Skill

## When to use this
Use this skill when the user provides a **SMILES** string and wants:
- Per-atom ¹H or ¹³C liquid-phase NMR chemical shifts (ppm)
- Simulated NMR spectrum image (Lorentzian line-shape)
- Quick deep-learning based prediction without DFT

## Inputs
- **SMILES string** (required, e.g. `CCO` for ethanol)
- `--nucleus H | C | both` (optional, default `both`)

## Outputs
- `/tmp/chemclaw/nmr_1H_<smiles>.png`  — ¹H NMR spectrum
- `/tmp/chemclaw/nmr_13C_<smiles>.png` — ¹³C NMR spectrum
- Console: per-atom chemical shifts (ppm)

## 目录结构

```
nmr-prediction/
├── SKILL.md
├── nmr_prediction.py
├── requirements.txt
└── assets/
    ├── NMRNet/        ← NMRNet 精简推理代码 + `oc_limit_dict.txt`
    └── Uni-Core/      ← Uni-Core 基础库（需要先 install）
```

模型权重（大文件，不放进 repo）存放于 `/tmp/weights/`，通过 `--setup` 自动下载。

## 环境安装 (首次)

### 1. 准备 assets/

```bash
# 将 NMRNet 放入 assets/（从 GitHub 下载 zip 后解压）
cp -r ~/Downloads/NMRNet-main nmr-prediction/assets/NMRNet

# 将 Uni-Core 放入 assets/ 并安装
cp -r ~/Downloads/Uni-Core-main nmr-prediction/assets/Uni-Core
cd nmr-prediction/assets/Uni-Core
python setup.py install    # macOS 默认禁用 CUDA，直接执行
```

### 2. 安装 Python 依赖

```bash
cd nmr-prediction
pip install -r requirements.txt
# 如果还没装 torch：pip install torch  (CPU 版即可)
```

### 3. 下载模型权重 + scaler → /tmp/weights/

```bash
cd nmr-prediction
python nmr_prediction.py --setup
```

此命令通过 remotezip 从 Zenodo 仅提取所需文件：
- H/C 模型 checkpoint（各 ~560 MB）→ `/tmp/weights/finetune/liquid/.../`
- H/C 液相 scaler（各 623 B）→ 同上目录

> 注意：NMRNet 仓库自带的 `demo/notebook/scaler/` 是**固态** NMR scaler，不适用于液相预测。
> 当前 skill 只保留 NMRNet 的精简推理代码与 `oc_limit_dict.txt`，不依赖 `demo/` 数据目录。

## How to run（环境已准备好时）

```bash
cd nmr-prediction

# 预测乙醇的 ¹H + ¹³C 谱
python nmr_prediction.py "CCO"

# 只预测苯的 ¹³C 谱
python nmr_prediction.py "c1ccccc1" --nucleus C

# 预测咖啡因的 ¹H 谱
python nmr_prediction.py "Cn1cnc2c1c(=O)n(c(=O)n2C)C" --nucleus H
```

## 运行原理（Pipeline）

```
SMILES
  ↓ RDKit: AddHs + EmbedMolecule + MMFFOptimize
3D 分子坐标 (atoms + coordinates)
  ↓ atoms_target_mask: 标记目标元素 (H 或 C) 为 1
NMRNet 数据记录 (dict)
  ↓ UniMatModel (SE(3)-Transformer, unimol_large 架构)
每原子预测化学位移 (scaled)
  ↓ TargetScaler.inverse_transform
化学位移 (ppm)
  ↓ Lorentzian 叠加
NMR 谱图 PNG
```

## 注意事项

- 模型仅训练于液态 NMR 数据（nmrshiftdb2），固态化合物不适用
- macOS CPU 推理速度较慢：¹H 约 10-30 秒，¹³C 约 10-30 秒（取决于分子大小）
- 权重固定存放在 `/tmp/weights/`（重启后消失，需重新 `--setup`）
- NMRNet / Uni-Core 代码在 `assets/` 里，随 repo 一起走
- `assets/NMRNet/oc_limit_dict.txt` 为运行时所需字典文件，不能删除

## References

- NMRNet 论文: [arXiv:2408.15681](https://arxiv.org/abs/2408.15681)
- NMRNet 代码: https://github.com/Colin-Jay/NMRNet
- Uni-Core: https://github.com/dptech-corp/Uni-Core
- 模型权重: https://zenodo.org/records/19142375
