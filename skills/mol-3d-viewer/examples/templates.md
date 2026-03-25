# 快速使用示例

## 基础示例

### 1. 从 SMILES 生成可交互 3D 网页

```bash
# 乙醇
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol.html --interactive

# 苯
python3 scripts/mol_3d_viewer.py --smiles "C1=CC=CC=C1" --output benzene.html --interactive

# 咖啡因
python3 scripts/mol_3d_viewer.py --smiles "C1=CN=C2C(=N1)N(C(=O)N2C)C" --output caffeine.html --interactive
```

### 2. 从 IUPAC 名称生成

```bash
# 阿司匹林（使用 IUPAC 名称）
python3 scripts/mol_3d_viewer.py --name "acetylsalicylic acid" --output aspirin.html --interactive

# 乙醇
python3 scripts/mol_3d_viewer.py --name "ethanol" --output ethanol.html --interactive

# 苯
python3 scripts/mol_3d_viewer.py --name "benzene" --output benzene.html --interactive
```

### 3. 生成静态 3D 图片

```bash
# PNG 格式
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol_3d.png

# SVG 格式
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol_3d.svg --format svg
```

### 4. 聚合物 3D 结构

```bash
# 聚乙烯
python3 scripts/mol_3d_viewer.py --smiles "*CC*" --output pe.html --interactive

# 聚环氧乙烷
python3 scripts/mol_3d_viewer.py --smiles "*OCC*" --output peo.html --interactive

# 聚环氧丙烷
python3 scripts/mol_3d_viewer.py --smiles "*OCC(C)*" --output ppo.html --interactive
```

### 5. 自定义渲染样式

```bash
# 球棍模型
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol.html --interactive --style ball_stick

# 空间填充模型
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol.html --interactive --style sphere

# 分子表面
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol.html --interactive --style surface
```

### 6. 批量生成

```bash
# 批量生成 3 个分子的 3D 网页
python3 scripts/mol_3d_viewer.py --smiles "CCO,C1=CC=CC=C1,CC(=O)O" --output-dir ./molecules --interactive
```

### 7. 从分子文件生成

```bash
# 从 SDF 文件
python3 scripts/mol_3d_viewer.py --input molecule.sdf --output molecule_3d.html --interactive

# 从 PDB 文件（蛋白质）
python3 scripts/mol_3d_viewer.py --input protein.pdb --output protein_3d.html --interactive --style surface
```

## 与现有化学技能配合

### 与 iupac_to_smiles 配合

```bash
# 1. 转换聚合物名称为 SMILES
python3 ../iupac-to-smiles/scripts/iupac_to_smiles.py \
    --name "poly[oxy(1-methylethylene)]" \
    -o result.json

# 2. 提取 SMILES 并生成 3D 网页
SMILES=$(cat result.json | jq -r '.results[0].polymer_smiles')
python3 scripts/mol_3d_viewer.py --smiles "$SMILES" --output ppo_3d.html --interactive
```

### 与 mol_visualizer 配合（2D + 3D）

```bash
# 生成 2D 结构图
python3 ../mol-visualizer/scripts/mol_visualizer.py --smiles "CCO" --output ethanol_2d.png

# 生成 3D 可交互网页
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol_3d.html --interactive
```

## 输出示例

生成的 HTML 网页支持：

- 🖱️ **鼠标旋转** - 左键拖动旋转分子
- 🔍 **缩放** - 滚轮缩放
- 🎨 **多种显示模式** - 棍状、球棍、空间填充、表面
- 🏷️ **原子标签** - 显示/隐藏元素符号
- 🔄 **自动旋转** - 展示模式
- 📸 **截图保存** - 下载当前视角图片

## 常见化合物 SMILES

| 化合物 | SMILES | IUPAC 名称 |
|--------|--------|-----------|
| 甲烷 | C | methane |
| 乙烷 | CC | ethane |
| 乙烯 | C=C | ethene |
| 乙炔 | C#C | ethyne |
| 苯 | C1=CC=CC=C1 | benzene |
| 乙醇 | CCO | ethanol |
| 乙酸 | CC(=O)O | acetic acid |
| 葡萄糖 | C(C1C(C(C(C(O1)O)O)O)O)O | glucose |
| 咖啡因 | CN1C=NC2=C1C(=O)N(C(=O)N2C)C | caffeine |
| 阿司匹林 | CC(=O)OC1=CC=CC=C1C(=O)O | acetylsalicylic acid |

## 聚合物 SMILES 示例

| 聚合物 | SMILES | 说明 |
|--------|--------|------|
| 聚乙烯 | *CC* | 最简单的碳链聚合物 |
| 聚丙烯 | *CC(C)* | 带甲基侧链 |
| 聚环氧乙烷 | *OCC* | 聚乙二醇 (PEG) |
| 聚环氧丙烷 | *OCC(C)* | 聚丙二醇 (PPG) |
| 聚苯乙烯 | *CC(C1=CC=CC=C1)* | 含苯环侧链 |
| PMMA | *CC(C)(C(=O)OC)* | 聚甲基丙烯酸甲酯 |
