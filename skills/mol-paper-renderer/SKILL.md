---
name: mol-paper-renderer
description: 论文级分子渲染工具。使用 xyzrender 生成出版质量的 SVG、PNG、PDF 和 GIF 动画。支持过渡态、非共价相互作用、分子轨道、晶体结构等高级功能。
trigger: ["论文级", "publication-quality", "出版质量", "xyzrender", "论文图片", "论文绘图", "规范分子图", "过渡态", "TS bond", "NCI", "分子轨道", "cube file", "晶体结构", "unit cell", "convex hull", "GIF 动画", "rotation GIF"]
---

# Publication-Quality Molecular Renderer

使用 **xyzrender** 生成**论文级**分子结构图。这不是普通的分子查看器，而是专门为科研出图设计的自动渲染工具。

## 触发条件

- 用户明确要求"论文级"、"出版质量"、"publication-quality"的图片
- 需要过渡态（TS）结构、非共价相互作用（NCI）展示
- 需要分子轨道（MO）、电子密度、静电势表面
- 需要晶体结构、晶胞、周期性结构
- 需要旋转 GIF 动画用于演示
- 需要凸包（convex hull）标注芳香环或配位 sphere
- 提供 cube 文件、ORCA/Gaussian/Q-Chem 输出文件
- 普通分子可视化但要求高质量输出

## 功能

### 输入格式

- ✅ **XYZ** - 标准坐标文件
- ✅ **mol/SDF/MOL2** - 化学标准格式
- ✅ **PDB** - 蛋白质数据银行格式
- ✅ **SMILES** - 自动 3D 嵌入（需 rdkit）
- ✅ **CIF** - 晶体结构（需 ase）
- ✅ **cube** - 分子轨道、电子密度、ESP
- ✅ **ORCA/Gaussian/Q-Chem 输出** - 直接渲染计算结果
- ✅ **extXYZ** - 带晶格信息的周期性结构
- ✅ **VASP/Quantum ESPRESSO** - 第一性计算结构

### 输出格式

- ✅ **SVG** - 矢量图（默认，适合出版物）
- ✅ **PNG** - 位图（适合网页、PPT）
- ✅ **PDF** - 矢量图（适合 LaTeX）
- ✅ **GIF** - 旋转动画、TS 振动、轨迹动画

### 高级功能

- ✅ **过渡态键** - 自动检测形成/断裂的键（虚线表示）
- ✅ **非共价相互作用** - 氢键、π-堆积等（点线表示）
- ✅ **分子轨道** - HOMO/LUMO 轨道渲染
- ✅ **电子密度表面** - 深度渐变半透明等值面
- ✅ **静电势（ESP）** - 映射到密度表面
- ✅ **凸包（Convex Hull）** - 标注芳香环、配位 sphere
- ✅ **晶体结构** - 晶胞盒、ghost atoms、晶轴箭头
- ✅ **vdW 表面** - 范德华球体叠加
- ✅ **GIF 动画** - 旋转、TS 振动、轨迹
- ✅ **原子性质着色** - 电荷、自旋密度等
- ✅ **测量标注** - 键长、键角、二面角
- ✅ **矢量箭头** - 偶极矩、力、电场

## 使用方法

### 对话框中使用

```
生成 caffeine 的论文级分子结构图
用 xyzrender 渲染这个 XYZ 文件，输出 SVG
画出过渡态结构，显示 TS 键
显示非共价相互作用（NCI）
生成 HOMO 轨道图（从 cube 文件）
创建旋转 GIF 动画用于 PPT
画出晶胞结构，显示周期性
标注芳香环的凸包
```

### 命令行使用

```bash
# 基础渲染（XYZ → SVG）
xyzrender molecule.xyz -o output.svg

# 指定输出格式
xyzrender molecule.xyz -o output.png
xyzrender molecule.xyz -o output.pdf

# 过渡态（自动检测 TS 键）
xyzrender ts.out --ts -o ts_figure.png

# 非共价相互作用
xyzrender hbond.xyz --nci -o nci.svg

# 旋转 GIF 动画
xyzrender molecule.xyz --gif-rot -o rotation.gif

# TS 振动 GIF
xyzrender ts.out --gif-ts -o ts_vibration.gif

# 分子轨道（HOMO/LUMO）
xyzrender caffeine_homo.cube --mo -o homo.svg

# 电子密度表面
xyzrender caffeine_dens.cube --dens -o density.svg

# 静电势映射
xyzrender caffeine_dens.cube --esp caffeine_esp.cube -o esp.svg

# 晶体结构
xyzrender caffeine_cell.xyz -o crystal.svg

# 凸包（标注芳香环）
xyzrender benzene.xyz --hull 1-6 -o benzene_hull.svg

# vdW 表面
xyzrender molecule.xyz --vdw -o vdw.svg

# 显示氢原子
xyzrender ethanol.xyz --hy -o ethanol_all_h.svg

# 凯库勒化（显示双键）
xyzrender benzene.xyz --kekule -o benzene_kekule.svg

# 原子索引标注
xyzrender caffeine.xyz --idx -o caffeine_indexed.svg

# 键长测量标注
xyzrender ethanol.xyz --measure -o ethanol_measured.svg

# 从 SMILES 生成（自动 3D 嵌入）
xyzrender --smi "C1CC(O)CCC1O" --hy -o molecule.svg

# 使用预设样式
xyzrender molecule.xyz --config flat -o flat.svg
xyzrender molecule.xyz --config paton -o paton.svg
```

### Python API

```python
from xyzrender import load, render, render_gif, build_config

# 加载并渲染
mol = load("caffeine.xyz")
render(mol)  # Jupyter 内联显示
render(mol, output="caffeine.svg")  # 保存 SVG
render(mol, output="caffeine.png")  # 保存 PNG

# 从 SMILES 生成
smi = load("C1CC(O)CCC1O", smiles=True)
smi.to_xyz("smiles.xyz")
render(smi, output="smiles.svg")

# 使用预设配置
cfg = build_config("flat", atom_scale=1.5, gradient=False)
render(mol, config=cfg)

# 高级功能
render(mol, ts_bonds=[(1, 6)])  # 手动 TS 键
render(mol, nci_bonds=[(2, 8)])  # 手动 NCI 键
render(mol, vdw=True)  # vdW 球体
render(mol, hull=[1,2,3,4,5,6])  # 凸包
render(mol, mo=True)  # 分子轨道（cube 文件）
render(mol, dens=True)  # 密度表面
render(mol, esp="esp.cube")  # ESP 映射

# GIF 动画
render_gif("mol.xyz", gif_rot="y", output="rotation.gif")
render_gif("ts.out", gif_ts=True, output="ts_vib.gif")
```

## 参数说明

### 基础参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--output` | `-o` | 输出文件路径 | `{input}.svg` |
| `--config` | `-c` | 样式预设或 JSON 配置 | `default` |
| `--charge` | | 分子电荷 | `0` |
| `--multiplicity` | `-m` | 自旋多重度 | `1` |

### 样式参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--canvas-size` | `-S` | 画布大小（像素） | `800` |
| `--atom-scale` | `-a` | 原子半径缩放 | `1.0` |
| `--bond-width` | `-b` | 键线宽度 | `2.0` |
| `--bond-color` | | 键颜色 | 自动 |
| `--background` | `-B` | 背景颜色 | `#ffffff` |
| `--transparent` | `-t` | 透明背景 | `false` |
| `--gradient` | `--grad` | 径向渐变 | `true` |
| `--fog` | `--fog` | 深度雾效果 | `true` |
| `--bond-orders` | `--bo` | 渲染键级 | `true` |

### 显示参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--hydrogens` | `--hy` | 显示氢原子 | `false` |
| `--no-hydrogens` | `--no-hy` | 隐藏所有氢 | `false` |
| `--kekule` | `-k` | 凯库勒键级 | `false` |
| `--vdw` | | vdW 球体 | `false` |
| `--vdw-opacity` | | vdW 透明度 | `0.25` |

### 过渡态/NCI

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--ts` | | 自动检测 TS 键 | `false` |
| `--ts-bond` | | 手动 TS 键（1-indexed） | - |
| `--nci` | | 自动检测 NCI | `false` |
| `--nci-bond` | | 手动 NCI 键 | - |

### 表面/轨道

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--mo` | | 分子轨道（cube） | `false` |
| `--mo-colors` | | 轨道颜色（正 负） | `steelblue maroon` |
| `--iso` | | 等值面阈值 | `0.05` (MO) / `0.001` (dens) |
| `--dens` | | 电子密度表面 | `false` |
| `--esp` | | ESP cube 文件 | - |
| `--nci-surf` | | NCI 表面 cube | - |

### 凸包（需要 xyzrender >= 0.3）

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--hull` | | 凸包原子索引 | - |
| `--hull-color` | | 凸包颜色 | 自动循环 |
| `--hull-opacity` | | 凸包透明度 | `0.2` |
| `--hull-edge` | | 绘制凸包边 | `true` |

> **注意**: 凸包功能需要 xyzrender >= 0.3。当前安装版本为 0.2.1。

### 晶体

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--crystal` | | 加载 VASP/QE 结构 | `false` |
| `--cell` | | 绘制晶胞盒 | 自动 |
| `--cell-color` | | 晶胞颜色 | `gray` |
| `--ghosts` | | 显示 ghost atoms | `true` |
| `--axes` | | 显示晶轴箭头 | `true` |
| `--axis` | | 观察方向 [HKL] | `001` |

### 动画

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--gif-rot` | | 旋转 GIF | `false` |
| `--gif-ts` | | TS 振动 GIF | `false` |
| `--gif-trj` | | 轨迹 GIF | `false` |
| `--gif-output` | `-go` | GIF 输出路径 | `{input}.gif` |
| `--gif-fps` | | GIF 帧率 | `10` |
| `--rot-frames` | | 旋转帧数 | `120` |

### 标注

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--measure` | | 输出键长/角/二面角 | `false` |
| `--index` | `--idx` | 原子索引标注 | `false` |
| `--label` | `-l` | 内联标注 | - |
| `--label-file` | | 批量标注文件 | - |
| `--cmap` | | 原子性质着色文件 | - |
| `--vectors` | | 矢量箭头 JSON | - |

## 输出示例

### 基础分子渲染

```bash
$ xyzrender caffeine.xyz -o caffeine.svg
✓ 已生成：caffeine.svg (800x800, SVG)
```

### 过渡态结构

```bash
$ xyzrender sn2.out --ts -o sn2_ts.png
✓ 已生成：sn2_ts.png (800x800, PNG) [过渡态，自动检测 TS 键]
```

### 非共价相互作用

```bash
$ xyzrender hbond.xyz --nci -o hbond.svg
✓ 已生成：hbond.svg (800x800, SVG) [NCI 相互作用]
```

### 旋转 GIF 动画

```bash
$ xyzrender molecule.xyz --gif-rot -o rotation.gif
✓ 已生成：rotation.gif (800x800, 120 帧，10fps)
```

### 分子轨道（HOMO）

```bash
$ xyzrender caffeine_homo.cube --mo -o homo.svg
✓ 已生成：homo.svg (800x800, SVG) [HOMO 轨道]
```

### 静电势表面

```bash
$ xyzrender caffeine_dens.cube --esp caffeine_esp.cube -o esp.svg
✓ 已生成：esp.svg (800x800, SVG) [ESP 映射]
```

### 晶体结构

```bash
$ xyzrender caffeine_cell.xyz -o crystal.svg
✓ 已生成：crystal.svg (800x800, SVG) [晶胞，ghost atoms，晶轴]
```

### 凸包标注

```bash
$ xyzrender benzene.xyz --hull 1-6 -o benzene_hull.svg
✓ 已生成：benzene_hull.svg (800x800, SVG) [芳香环凸包]
```

## 样式预设

| 预设 | 说明 | 适用场景 |
|------|------|----------|
| `default` | 默认样式，带渐变和深度雾 | 通用 |
| `flat` | 无渐变，平面风格 | 简洁图表 |
| `paton` | PyMOL 风格（参考 Rob Paton） | 计算化学论文 |

## 依赖安装

### 基础安装

```bash
pip install xyzrender
```

### 完整功能安装

```bash
# 所有功能
pip install 'xyzrender[all]'

# 或按需安装
pip install xyzrender[smiles]  # SMILES 支持（rdkit）
pip install xyzrender[cif]     # CIF 支持（ase）
pip install xyzrender[crystal] # VASP/QE 支持（phonopy）
pip install xyzrender[v]       # 交互式查看器（vmol，Linux only）
pip install xyzrender[gif]     # GIF 生成（cairosvg, Pillow）
```

### 使用 uv 安装

```bash
uv tool install xyzrender
uv tool install --editable .  # 开发模式
```

## 与其他技能配合

### 与 mol_2d_viewer 配合

- **mol_2d_viewer**: 快速 2D 结构预览
- **mol_paper_renderer**: 论文级最终出图

```bash
# 快速预览
python3 scripts/mol_2d_viewer.py -s "CCO" -o ethanol_preview.png

# 论文级渲染
xyzrender ethanol.xyz -o ethanol_paper.svg --config paton
```

### 与 mol_3d_viewer 配合

- **mol_3d_viewer**: 生成 3D 坐标、SDF 文件、可交互 HTML
- **mol_paper_renderer**: 从 3D 坐标生成出版质量图片

```bash
# 生成 3D 坐标
python3 scripts/mol_3d_viewer.py -s "CCO" -o ethanol

# 使用生成的 XYZ 进行论文级渲染
xyzrender ethanol.xyz -o ethanol_paper.svg --config paton --hy
```

### 与 iupac_to_smiles 配合

```bash
# 1. 转换名称为 SMILES
python3 scripts/iupac_to_smiles.py -n "caffeine" -o result.json

# 2. 提取 SMILES 并生成 3D 坐标
SMILES=$(cat result.json | jq -r '.results[0].smiles')
xyzrender --smi "$SMILES" --hy -o caffeine.svg
```

## 完整工作流程示例

### 示例 1: 从 SMILES 到论文级图片

```bash
# 一键生成（SMILES → 3D 嵌入 → 论文级 SVG）
xyzrender --smi "C1=CC(=CC=C1C(=O)O)C(=O)O" --hy --config paton -o aspirin.svg
```

### 示例 2: 过渡态分析

```bash
# 从 ORCA 输出直接渲染 TS 结构
xyzrender ts_freq.out --ts --hy --vdw 84-169 -o ts_figure.svg

# 生成 TS 振动 GIF
xyzrender ts_freq.out --gif-ts --gif-rot -o ts_animation.gif
```

### 示例 3: 非共价相互作用分析

```bash
# 从几何结构自动检测 NCI
xyzrender complex.xyz --nci -o nci_auto.svg

# 或使用 NCIPLOT cube 文件
xyzrender complex_dens.cube --nci-surf complex_grad.cube -o nci_surface.svg
```

### 示例 4: 分子轨道可视化

```bash
# 从 ORCA 生成 cube 文件后渲染
orca_plot calculation.out -i
# 选择 HOMO 轨道，生成 caffeine_homo.cube

# 渲染 HOMO
xyzrender caffeine_homo.cube --mo -o homo.svg

# 渲染 LUMO
xyzrender caffeine_lumo.cube --mo --mo-colors teal orange -o lumo.svg
```

### 示例 5: 晶体结构

```bash
# 从 extXYZ 渲染（自动检测晶格）
xyzrender caffeine_cell.xyz -o crystal.svg

# 沿 [111] 方向观察
xyzrender caffeine_cell.xyz --axis 111 -o crystal_111.svg

# 生成旋转 GIF
xyzrender caffeine_cell.xyz --gif-rot 111 -o crystal_rot.gif
```

### 示例 6: 静电势分析

```bash
# 从 ORCA 生成密度和 ESP cube
orca_plot calculation.out -i
# 生成 density.cube 和 esp.cube

# 渲染 ESP 映射表面
xyzrender density.cube --esp esp.cube -o esp_map.svg
```

## 注意事项

- ✅ **论文级质量** - 专为出版物设计，默认 SVG 矢量输出
- ✅ **自动检测** - TS 键、NCI、芳香性自动识别
- ✅ **多种输入** - 支持几乎所有化学/计算化学格式
- ✅ **高级功能** - 轨道、密度、ESP、凸包、晶体
- ✅ **动画支持** - 旋转、TS 振动、轨迹 GIF
- ⚠️ **SMILES 需要 rdkit** - `pip install xyzrender[smiles]`
- ⚠️ **晶体需要 phonopy** - `pip install xyzrender[crystal]`
- ⚠️ **GIF 需要 cairosvg+Pillow** - `pip install xyzrender[gif]`
- ⚠️ **交互查看器仅 Linux** - `pip install xyzrender[v]`
- ⚠️ **cube 文件需外部生成** - 使用 ORCA/Gaussian 的 cubegen

## 错误处理

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| `File not found` | 输入文件不存在 | 检查路径 |
| `Invalid format` | 文件格式不支持 | 检查扩展名或添加 `--rebuild` |
| `RDKit not installed` | SMILES 嵌入失败 | `pip install xyzrender[smiles]` |
| `phonopy not installed` | 晶体加载失败 | `pip install xyzrender[crystal]` |
| `cairosvg not installed` | GIF/PNG 转换失败 | `pip install xyzrender[gif]` |
| `No bond orders` | 键级检测失败 | 添加 `--bo` 或检查几何结构 |

## 技术实现

### 键级检测

- **库**: xyzgraph
- **方法**: 基于几何距离的键级感知
- **支持**: 单键、双键、三键、芳香键

### TS 键检测

- **库**: graphRC
- **方法**: 从虚频振动模式分析
- **输出**: 形成/断裂的键（虚线）

### NCI 检测

- **库**: xyzgraph
- **方法**: 几何判据（距离、角度）
- **支持**: 氢键、卤键、π-堆积、阳离子-π

### 晶体渲染

- **库**: phonopy（可选）、ase（CIF）
- **功能**: 晶胞盒、ghost atoms、晶轴箭头
- **方向**: 支持 Miller 指数 [HKL] 观察

### GIF 生成

- **库**: CairoSVG、Pillow
- **类型**: 旋转、TS 振动、轨迹
- **控制**: 帧率、帧数、旋转轴

## 性能参考

| 任务 | 时间 | 说明 |
|------|------|------|
| 小分子 SVG | <1s | <50 原子 |
| 大分子 SVG | 1-5s | 50-200 原子 |
| 晶体结构 | 2-10s | 含 ghost atoms |
| MO 表面 | 5-20s | cube 文件等值面 |
| 旋转 GIF | 10-60s | 120 帧，10fps |
| TS 振动 GIF | 10-30s | 含 graphRC 分析 |

## 输出文件位置

默认输出目录：`~/.openclaw/media/mol-paper-renderer/`

```bash
mkdir -p ~/.openclaw/media/mol-paper-renderer
```

## 高级技巧

### 自定义样式配置

创建 `my_style.json`：

```json
{
  "canvas_size": 1200,
  "atom_scale": 2.0,
  "bond_width": 3.0,
  "gradient": true,
  "fog": true,
  "background": "#f8f8f8",
  "colors": {
    "C": "#333333",
    "H": "#ffffff",
    "N": "#3050F8",
    "O": "#FF0000"
  }
}
```

使用：

```bash
xyzrender molecule.xyz --config my_style.json -o custom.svg
```

### 批量标注

创建 `labels.txt`：

```
1 2 d
2 3 4 a
1 2 3 4 t
7 "Partial charge: +0.5"
```

使用：

```bash
xyzrender molecule.xyz --label labels.txt -o labeled.svg
```

### 原子性质着色

创建 `charges.txt`：

```
1 0.512
2 -0.234
3 0.041
```

使用：

```bash
xyzrender molecule.xyz --cmap charges.txt --cmap-range -0.5 0.5 -o colored.svg
```

## 版本说明

**当前安装版本**: xyzrender 0.2.1

### 已测试功能（✅ 可用）

- ✅ SMILES → 3D 嵌入并渲染
- ✅ XYZ/SDF/PDB 文件渲染
- ✅ SVG/PNG/GIF 输出
- ✅ 样式预设（default, flat, paton）
- ✅ 氢原子显示/隐藏
- ✅ 凯库勒键级
- ✅ vdW 球体表面
- ✅ 原子索引标注
- ✅ 键长/键角/二面角测量
- ✅ 旋转 GIF 动画
- ✅ TS 振动 GIF（需要 QM 输出文件）
- ✅ 分子轨道渲染（需要 cube 文件）
- ✅ 电子密度表面
- ✅ 静电势映射
- ✅ NCI 相互作用检测
- ✅ 晶体结构（需要 phonopy）

### 需要更新版本的功能（⚠️ 0.3+）

- ⚠️ 凸包（Convex Hull）
- ⚠️ 某些高级标注功能

如需使用最新功能，可升级：
```bash
pip install --upgrade xyzrender --break-system-packages
```

## 资源链接

- **GitHub**: https://github.com/aligfellow/xyzrender
- **文档**: https://xyzrender.readthedocs.io
- **Web App**: https://xyzrender-web.streamlit.app
- **依赖**:
  - xyzgraph: https://github.com/aligfellow/xyzgraph
  - graphRC: https://github.com/aligfellow/graphRC
  - v (viewer): https://github.com/briling/v
  - xyz2svg (inspiration): https://github.com/briling/xyz2svg
