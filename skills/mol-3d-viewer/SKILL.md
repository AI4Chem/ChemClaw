---
name: mol-3d-viewer
description: 将 SMILES 或化学名称转换为分子 3D 结构。支持生成 SDF 文件、3D 分子图片和可交互 HTML 网页（可旋转观察）。
trigger: ["3D 分子", "分子 3D", "3D 结构", "3D visualization", "rotate molecule", "交互分子", "3D model", "分子模型"]
---

# Molecular 3D Viewer

将 SMILES 字符串或化学名称转换为分子 **3D 结构**，支持生成 **SDF 文件**、**3D 分子图片**和 **可交互 HTML 网页**（可用鼠标旋转观察）。

## 触发条件

- 用户提供 SMILES 并要求 3D 可视化
- 提到"3D 分子"、"分子 3D"、"3D 结构"
- 说"3D visualization"、"rotate molecule"、"交互分子"
- 要求生成可旋转的分子模型
- 提供分子文件（SDF、MOL、PDB 等）

## 功能

- ✅ **SMILES → 3D 分子结构**
- ✅ **IUPAC 名称 → 3D 结构**（自动通过 OPSIN 转 SMILES）
- ✅ **分子文件支持** - SDF、MOL、PDB 格式
- ✅ **3D 优化** - 使用 RDKit MMFF94 力场优化几何结构
- ✅ **SDF 文件输出** - 标准分子结构文件格式
- ✅ **真正的 3D 渲染图片** - 基于 3D 坐标渲染，不是 2D 结构图
- ✅ **可交互 HTML** - 生成 WebGL 网页，支持鼠标旋转、缩放
- ✅ **多种渲染样式** - 球棍模型、棍状模型、空间填充模型
- ✅ **聚合物支持** - 正确渲染聚合物 3D 结构
- ✅ **批量生成** - 支持多个分子同时处理
- ✅ **分子信息展示** - HTML 中显示分子式、分子量

## 三种输出格式

### 1. SDF 文件 (.sdf)

- **格式**: Structure Data File
- **用途**: 标准分子结构交换格式
- **内容**: 3D 坐标、原子、键信息
- **兼容**: 支持所有化学软件（ChemDraw、PyMOL 等）

### 2. 3D 图片 (.png)

- **格式**: PNG 位图
- **渲染**: 基于真实 3D 坐标渲染
- **样式**: 默认球棍模型（ball_stick）
- **尺寸**: 800x600（可自定义）
- **用途**: 快速预览、文档插入

### 3. 可交互 HTML (.html)

- **渲染**: 3Dmol.js WebGL
- **功能**:
  - 🖱️ 鼠标旋转、平移、缩放
  - 🎨 多种显示模式切换
  - 📊 分子式、分子量展示
  - 💾 截图保存功能
  - 🔄 自动旋转开关
- **特点**: 分子自动居中，打开即可见

## 使用方法

### 对话框中使用

```
生成 ethanol 的 3D 分子结构
SMILES: CCO，创建 3D 可交互网页
可视化 aspirin 的 3D 结构，保存为 HTML
poly[oxy(1-methylethylene)] 生成 3D 模型
从文件 molecule.sdf 生成 3D 展示
批量生成 3D：CCO,C1=CC=CC=C1
```

### 命令行使用

```bash
# 生成全部三种输出（SDF + 3D 图片 + HTML）
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol

# 只生成 SDF 文件
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol --sdf-only

# 只生成 3D 图片
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol --image-only

# 只生成 HTML
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol --html-only

# 从名称生成
python3 scripts/mol_3d_viewer.py --name "aspirin" --output aspirin

# 自定义渲染样式
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol --style ball_stick

# 批量生成
python3 scripts/mol_3d_viewer.py --smiles "CCO,C1=CC=CC=C1" --output-dir ./3d_molecules
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--smiles` | `-s` | SMILES 字符串（可多个） | - |
| `--name` | `-n` | IUPAC 名称 | - |
| `--input` | `-i` | 输入分子文件 | - |
| `--output` | `-o` | 输出文件基础路径 | 自动生成 |
| `--output-dir` | `-d` | 输出目录（批量模式） | `~/.openclaw/media/mol-3d-viewer` |
| `--sdf-only` | | 只生成 SDF 文件 | `false` |
| `--image-only` | | 只生成 3D 图片 | `false` |
| `--html-only` | | 只生成 HTML | `false` |
| `--style` | `-S` | 渲染样式 | `ball_stick` |
| `--width` | `-W` | 宽度（像素） | `800` |
| `--height` | `-H` | 高度（像素） | `600` |
| `--bg-color` | `-b` | 背景颜色 | `white` |
| `--show-labels` | `-l` | 显示原子标签 | `true` |
| `--hide-labels` | | 隐藏原子标签 | `false` |
| `--auto-rotate` | `-r` | HTML 自动旋转 | `false` |
| `--force-field` | | 力场类型 | `mmff94` |
| `--max-steps` | | 优化最大步数 | `200` |

## 渲染样式

| 样式 | 说明 | 适用场景 |
|------|------|----------|
| `stick` | 棍状模型 | 清晰展示化学键 |
| `sphere` | 空间填充模型 | 展示分子体积和形状 |
| `ball_stick` | 球棍模型（默认） | 平衡结构和原子 |
| `surface` | 分子表面 | 展示静电势、疏水性 |
| `line` | 线状模型 | 快速预览大分子 |

## 输出示例

### 生成全部三种输出

```bash
$ python3 mol_3d_viewer.py -s "CCO" -o ethanol
✓ 已生成 3D 优化结构
  📄 SDF: ethanol.sdf
  🖼️  3D 图片：ethanol_3d.png
  🌐 HTML: ethanol.html (可交互，支持旋转)
```

### 从名称生成

```bash
$ python3 mol_3d_viewer.py -n "caffeine" -o caffeine
✓ 已生成 3D 优化结构
  📄 SDF: caffeine.sdf
  🖼️  3D 图片：caffeine_3d.png
  🌐 HTML: caffeine.html (可交互，支持旋转)
```

### 聚合物 3D 结构

```bash
$ python3 mol_3d_viewer.py -s "*OCC*" -o peo
✓ 已生成 3D 优化结构 [聚合物]
  📄 SDF: peo.sdf
  🖼️  3D 图片：peo_3d.png
  🌐 HTML: peo.html (可交互，支持旋转)
```

### 批量生成

```bash
$ python3 mol_3d_viewer.py -s "CCO,C1=CC=CC=C1,CC(=O)O" -d ./3d_molecules
✓ 已生成：./3d_molecules/mol_1/ (3 files)
✓ 已生成：./3d_molecules/mol_2/ (3 files)
✓ 已生成：./3d_molecules/mol_3/ (3 files)
完成：3/3 成功
```

## 可交互 HTML 功能

生成的 HTML 网页支持：

### 鼠标控制

- **左键拖动** - 旋转分子
- **右键拖动** - 平移分子
- **滚轮** - 缩放
- **双击** - 重置视角

### 显示模式切换

- 棍状模型（Stick）
- 球棍模型（Ball & Stick）
- 空间填充（Space Fill）
- 分子表面（Surface）

### 信息展示

- **分子式** - 醒目显示在顶部
- **分子量** - 精确到小数点后两位
- **SMILES** - 可滚动查看完整结构
- **输入名称** - 如果从名称生成

### 其他功能

- 原子标签显示/隐藏
- 自动旋转开关
- 截图保存（一键下载 PNG）
- 响应式设计（适配桌面和移动设备）

## 依赖

```bash
pip install rdkit requests numpy
```

**可选依赖**（用于更高级的 3D 优化）：

```bash
pip install openbabel  # 支持更多文件格式
```

## OPSIN API 说明

- **来源**: 剑桥大学（重定向至欧洲生物信息学研究所 EBI）
- **网址**: <https://opsin.ch.cam.ac.uk/>
- **优势**:
  - 支持复杂 IUPAC 名称解析
  - 无需 API 密钥
  - 自动跟随重定向
- **限制**:
  - 需要网络连接
  - 某些商品名可能无法识别

## 3D 优化流程

1. **从 SMILES 生成 2D 结构** - RDKit
2. **添加氢原子** - 补全分子
3. **生成 3D 坐标** - ETKDG 算法
4. **力场优化** - MMFF94 或 UFF
5. **能量最小化** - 最多 200 步迭代
6. **渲染输出** - 3Dmol.js（HTML）或 RDKit（图片）

## 完整工作流程示例

### 示例 1: 从 IUPAC 名称到三种输出

```bash
# 一键生成（自动转换名称 + 3D 优化 + 三种输出）
python3 scripts/mol_3d_viewer.py --name "aspirin" --output aspirin
```

### 示例 2: 从分子文件到 3D 展示

```bash
# 从 SDF 文件生成
python3 scripts/mol_3d_viewer.py --input molecule.sdf --output molecule_3d

# 从 PDB 文件生成（蛋白质等生物大分子）
python3 scripts/mol_3d_viewer.py --input protein.pdb --output protein_3d --style surface
```

### 示例 3: 批量处理聚合物

```bash
# 创建聚合物列表
cat > polymers.txt << EOF
poly[oxyethylene]
poly[methyl methacrylate]
poly[styrene]
EOF

# 批量转换并生成 3D
python3 scripts/iupac_to_smiles.py --input polymers.txt --output polymers.json

# 提取 SMILES 并批量生成 3D
python3 scripts/mol_3d_viewer.py --smiles "*OCC*,*CC(C)(C(=O)OC)*,*CC(C1=CC=CC=C1)*" \
  --output-dir ./polymer_3d
```

## 与其他化学技能配合

### 与 iupac_to_smiles 配合

```bash
# 1. 转换名称为 SMILES
python3 scripts/iupac_to_smiles.py --name "poly[oxy(1-methylethylene)]" -o result.json

# 2. 生成 3D 三种输出
SMILES=$(cat result.json | jq -r '.results[0].polymer_smiles')
python3 scripts/mol_3d_viewer.py --smiles "$SMILES" --output ppo_3d
```

### 与 mol_visualizer 配合

```bash
# 2D 结构图 + 3D 可交互模型一起生成
python3 scripts/mol_visualizer.py --smiles "CCO" --output ethanol_2d.png
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol_3d
```

## 支持的分子文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| SDF | `.sdf`, `.sd` | Structure Data File，支持多个分子 |
| MOL | `.mol` | MDL Molfile，单个分子 |
| PDB | `.pdb` | Protein Data Bank，生物大分子 |
| XYZ | `.xyz` | 简单坐标格式 |

## 注意事项

- ✅ **三种输出** - 默认生成 SDF + 3D 图片 + HTML
- ✅ **3D 优化** - 所有结构都经过力场优化，接近真实几何
- ✅ **聚合物支持** - 正确处理聚合物连接点
- ✅ **自动加氢** - 自动补充氢原子确保价态正确
- ✅ **交互友好** - HTML 分子自动居中，打开即可见
- ✅ **信息完整** - HTML 显示分子式、分子量
- ⚠️ **大分子优化时间** - 超过 100 个原子的分子可能需要数秒优化
- ⚠️ **构象异构体** - 生成的是单一构象，可能存在多种稳定构象
- ⚠️ **需要网络连接** - IUPAC 名称转换需要 OPSIN API
- ⚠️ **HTML 需要浏览器** - 可交互网页需要现代浏览器（支持 WebGL）

## 错误处理

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| `Invalid SMILES` | SMILES 格式错误 | 检查语法，确保括号匹配 |
| `3D generation failed` | 3D 坐标生成失败 | 简化分子或检查价态 |
| `Force field error` | 力场优化失败 | 尝试 UFF 力场（`--force-field uff`） |
| `Name not found` | 名称无法识别 | OPSIN 无法识别，使用 SMILES 直接输入 |
| `File format error` | 文件格式不支持 | 检查文件格式，转换为 SDF/MOL |

## 技术实现

### 3D 坐标生成

- **算法**: ETKDG (Experimental-Torsion Knowledge Distance Geometry)
- **库**: RDKit
- **精度**: 接近实验晶体结构

### 力场优化

- **默认**: MMFF94 (Merck Molecular Force Field)
- **备选**: UFF (Universal Force Field)
- **迭代**: 最多 200 步能量最小化

### 3D 图片渲染

- **库**: RDKit MolDraw2D (Cairo/SVG)
- **类型**: 真正的 3D 坐标渲染（不是 2D 结构图）
- **默认样式**: 球棍模型（ball_stick）

### HTML 渲染

- **库**: 3Dmol.js (v2.x)
- **渲染器**: WebGL
- **兼容性**: 所有现代浏览器

## 性能参考

| 分子大小 | 3D 生成时间 | HTML 生成时间 |
|----------|------------|--------------|
| 小分子 (<20 原子) | <0.5s | <0.1s |
| 中等分子 (20-50 原子) | 0.5-2s | <0.1s |
| 大分子 (50-100 原子) | 2-5s | <0.2s |
| 聚合物/蛋白 (>100 原子) | 5-20s | 0.2-1s |

## 输出文件位置

默认输出目录：`~/.openclaw/media/mol-3d-viewer/`

可以在技能目录创建输出目录：

```bash
mkdir -p ~/.openclaw/media/mol-3d-viewer
```

## 高级选项

### 自定义力场

```bash
# 使用 UFF 力场（适合含金属的分子）
python3 mol_3d_viewer.py -s "CCO" -o ethanol --force-field uff
```

### 自定义优化步数

```bash
# 增加优化步数（更精确但更慢）
python3 mol_3d_viewer.py -s "CCO" -o ethanol --max-steps 500
```

### 自定义样式

```bash
# 球棍模型
python3 mol_3d_viewer.py -s "CCO" -o ethanol --style ball_stick

# 空间填充模型
python3 mol_3d_viewer.py -s "CCO" -o ethanol --style sphere
```
