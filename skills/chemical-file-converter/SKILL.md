---
name: chemical-file-converter
description: 化学文件格式转换工具。支持 .xyz, .gjf (Gaussian), .mol, .sdf, .pdb, .mol2 等格式互转。使用 Open Babel 或 RDKit 进行转换。当用户提供化学文件并要求转换格式、生成不同格式的文件、或提到文件转换时触发。
---

# Chemical File Converter

化学文件格式转换技能，支持多种常见化学文件格式之间的互转。

## 支持的文件格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| **XYZ** | `.xyz` | 简单坐标格式，包含原子类型和 3D 坐标 |
| **Gaussian Input** | `.gjf`, `.com` | Gaussian 计算输入文件 |
| **MDL Molfile** | `.mol` | 单个分子的 2D/3D 结构 |
| **Structure Data** | `.sdf`, `.sd` | 多个分子的结构数据文件 |
| **Protein Data Bank** | `.pdb` | 生物大分子结构 |
| **Tripos Mol2** | `.mol2` | Tripos 分子格式 |
| **SMILES** | `.smi`, `.smiles` | 线性分子表示 |
| **CML** | `.cml` | 化学标记语言 (XML) |
| **MOPAC** | `.mop`, `.zmt` | MOPAC 输入文件 |

## 使用方法

### 对话框中使用

用户可以直接上传文件并要求转换：

```
把这个 xyz 文件转成 gjf 格式
将 molecule.mol 转换为 .sdf 格式
帮我生成 Gaussian 输入文件，用 B3LYP/6-31G* 方法
把 pdb 文件转成 xyz 坐标
批量转换这些文件为 .mol2 格式
```

### 命令行使用

```bash
# 基本转换
python3 scripts/convert_chemical.py input.xyz -o output.gjf

# 指定输出格式
python3 scripts/convert_chemical.py input.mol --format sdf

# 批量转换
python3 scripts/convert_chemical.py *.xyz --output-dir ./converted

# Gaussian 输入文件（指定方法和基组）
python3 scripts/convert_chemical.py input.xyz -o output.gjf \
  --method B3LYP --basis 6-31G* --charge 0 --multiplicity 1

# 使用 Open Babel（如果可用）
python3 scripts/convert_chemical.py input.pdb -o output.xyz --use-openbabel
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--input` | `-i` | 输入文件路径 | 必需 |
| `--output` | `-o` | 输出文件路径 | 自动生成 |
| `--format` | `-f` | 输出格式 (xyz/sdf/mol2/pdb/gjf 等) | 从输出文件扩展名推断 |
| `--output-dir` | `-d` | 输出目录（批量模式） | 当前目录 |
| `--method` | `-m` | Gaussian 计算方法 | B3LYP |
| `--basis` | `-b` | Gaussian 基组 | 6-31G* |
| `--charge` | | 分子电荷 | 0 |
| `--multiplicity` | | 自旋多重度 | 1 |
| `--link0` | | Gaussian Link0 命令（如 %mem=4GB） | 自动 |
| `--use-openbabel` | | 强制使用 Open Babel | 自动检测 |
| `--use-rdkit` | | 强制使用 RDKit | 自动检测 |

## 工作流程

### 1. 文件上传和识别

用户上传化学文件后，自动识别文件格式：

```python
# 根据扩展名识别格式
.xyz → xyz
.gjf/.com → gaussian
.mol → mdl
.sdf → sdf
.pdb → pdb
.mol2 → mol2
```

### 2. 格式转换

根据目标格式选择合适的转换引擎：

| 转换类型 | 推荐引擎 | 说明 |
|---------|---------|------|
| xyz ↔ mol/sdf | RDKit | 支持 3D 坐标 |
| pdb ↔ xyz | Open Babel | 生物大分子支持好 |
| 任意 → gjf | 内置脚本 | 可自定义 Gaussian 参数 |
| 任意格式互转 | Open Babel | 支持 100+ 格式 |

### 3. Gaussian 输入文件生成

对于 `.gjf` 格式，可以自定义计算参数：

```
%chk=molecule.chk
%mem=4GB
%nproc=4
#p B3LYP/6-31G* opt freq

分子标题

电荷 多重度
原子坐标
...

```

## 输出示例

### 转换成功

```bash
$ python3 convert_chemical.py ethanol.xyz -o ethanol.gjf
✓ 已读取：ethanol.xyz (9 原子)
✓ 已生成：ethanol.gjf (Gaussian 输入，B3LYP/6-31G*)
```

### 批量转换

```bash
$ python3 convert_chemical.py *.mol --output-dir ./sdf_output
✓ 已转换：mol_1.mol → sdf_output/mol_1.sdf
✓ 已转换：mol_2.mol → sdf_output/mol_2.sdf
✓ 已转换：mol_3.mol → sdf_output/mol_3.sdf
完成：3/3 成功
```

### Gaussian 文件定制

```bash
$ python3 convert_chemical.py input.xyz -o custom.gjf \
  --method wB97XD --basis def2TZVP --charge -1 --multiplicity 2 \
  --link0 "%mem=8GB,%nproc=8"
✓ 已生成：custom.gjf (wB97XD/def2TZVP, 阴离子，双重态)
```

## 依赖

### 必需依赖

```bash
pip install rdkit
```

### 可选依赖（推荐安装）

```bash
# Open Babel（支持更多格式）
conda install -c conda-forge openbabel
# 或
pip install openbabel-wheel

# ASE（原子模拟环境，支持更多量子化学格式）
pip install ase
```

### 检查安装

```bash
# 检查 RDKit
python3 -c "from rdkit import Chem; print('RDKit OK')"

# 检查 Open Babel
obabel -L formats | head -20

# 检查 ASE
python3 -c "import ase; print('ASE OK')"
```

## 文件格式详解

### XYZ 格式

```
9
乙醇分子
C     0.000000     0.000000     0.000000
C     1.500000     0.000000     0.000000
O     2.000000     1.200000     0.000000
H    -0.300000    -1.000000     0.000000
...
```

### Gaussian (GJF) 格式

```
%chk=molecule.chk
%mem=4GB
%nproc=4
#p B3LYP/6-31G* opt freq

乙醇优化和频率计算

0 1
C     0.000000     0.000000     0.000000
C     1.500000     0.000000     0.000000
O     2.000000     1.200000     0.000000
...

```

### MDL Molfile 格式

```
  Mrv2014 01012021

  9  8  0  0  0  0            999 V2000
    0.0000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
    1.5000    0.0000    0.0000 C   0  0  0  0  0  0  0  0  0  0  0  0
...
  1  2  1  0  0  0  0
  2  3  1  0  0  0  0
...
M  END
```

## 常见问题

### Q: 转换后原子坐标变了？
A: 某些格式转换可能涉及坐标变换（如内坐标↔笛卡尔坐标）。使用 `--use-openbabel` 通常能保持坐标一致。

### Q: Gaussian 文件无法运行？
A: 检查：
- Link0 命令格式（%mem, %nproc）
- 方法和基组名称是否正确
- 电荷和多重度是否合理
- 原子坐标格式（Gaussian 使用笛卡尔坐标）

### Q: 批量转换时部分文件失败？
A: 检查失败文件的格式是否正确。某些文件可能包含不支持的原子类型或格式错误。

### Q: 如何转换大分子（蛋白质）？
A: 对于 PDB 文件，建议使用 Open Babel 或 ASE：
```bash
obabel protein.pdb -o xyz -O protein.xyz
```

## 与其他化学技能配合

### 与 mol_2d_viewer 配合

```bash
# 1. 转换格式
python3 scripts/convert_chemical.py input.xyz -o output.mol

# 2. 生成 2D 结构图
python3 ../mol-2d-viewer/scripts/mol_2d_viewer.py --input output.mol --output structure.png
```

### 与 mol_3d_viewer 配合

```bash
# 1. 从 Gaussian 文件提取坐标
python3 scripts/convert_chemical.py input.gjf -o output.xyz

# 2. 生成 3D 可视化
python3 ../mol-3d-viewer/scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol_3d
```

### 与 iupac_to_smiles 配合

```bash
# 1. 从文件提取 SMILES
python3 scripts/convert_chemical.py input.mol -o output.smiles

# 2. 转换名称为 SMILES
python3 ../iupac-to-smiles/scripts/iupac_to_smiles.py --name "ethanol" --output name_result.json
```

## 注意事项

- ✅ **自动检测引擎** - 优先使用 RDKit，失败时尝试 Open Babel
- ✅ **保持 3D 坐标** - 转换时保留原始 3D 几何结构
- ✅ **Gaussian 定制** - 支持自定义方法、基组、电荷、多重度
- ✅ **批量转换** - 支持通配符和目录批量处理
- ⚠️ **格式限制** - 某些格式不支持 3D 坐标（如 SMILES）
- ⚠️ **大分子处理** - PDB 文件建议使用 Open Babel
- ⚠️ **键信息丢失** - XYZ→MOL 转换可能需要推断化学键

## 错误处理

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| `Format not supported` | 不支持的格式 | 检查扩展名，使用 `--format` 明确指定 |
| `RDKit error` | RDKit 转换失败 | 尝试 `--use-openbabel` |
| `Open Babel not found` | 未安装 Open Babel | 安装：`conda install openbabel` |
| `Invalid Gaussian parameters` | Gaussian 参数错误 | 检查方法和基组名称 |
| `File read error` | 文件读取失败 | 检查文件编码和格式 |

## 技术实现

### 转换引擎选择

1. **RDKit** - 优先用于小分子有机化合物
2. **Open Babel** - 用于大分子、无机化合物、特殊格式
3. **ASE** - 用于量子化学格式（VASP, Quantum ESPRESSO 等）
4. **内置解析器** - 用于 Gaussian 输入文件生成

### 坐标处理

- **XYZ 格式** - 直接读取/写入笛卡尔坐标
- **MOL/SDF** - 使用 RDKit 解析键级和立体化学
- **PDB** - 处理残基、链、异原子记录
- **GJF** - 解析 Link0 命令和路由部分

## 性能参考

| 分子大小 | 转换时间 (RDKit) | 转换时间 (Open Babel) |
|----------|-----------------|----------------------|
| 小分子 (<20 原子) | <0.1s | <0.2s |
| 中等分子 (20-50 原子) | 0.1-0.5s | 0.2-1s |
| 大分子 (50-200 原子) | 0.5-2s | 1-5s |
| 蛋白质 (>200 原子) | 不支持 | 5-30s |

## 输出文件位置

默认输出到输入文件同目录，或使用 `--output-dir` 指定：

```bash
python3 scripts/convert_chemical.py input.xyz -o ./output/converted.gjf
```

对于飞书兼容性，建议输出到白名单目录：
- `~/.openclaw/media/chemical-converter/`
- `~/.openclaw/workspace/`
