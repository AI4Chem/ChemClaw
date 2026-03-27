---
name: pdf-dft-extractor
description: |
  Extract DFT calculation coordinates from PDF files and generate Gaussian gjf files. 
  从PDF文件中提取DFT计算坐标并生成Gaussian gjf输入文件。
  Supports batch processing with separate output folders for each PDF.
  支持批量处理，每个PDF单独生成输出文件夹。
---

# PDF DFT Extractor | DFT坐标提取器

Extract DFT calculation coordinates from PDF files (especially supplementary materials) and generate Gaussian input files (.gjf). Supports batch processing with separate output folders for each PDF.
从PDF文件（特别是论文支撑材料）中提取DFT计算坐标，生成Gaussian输入文件(gjf)。支持批量处理，每个PDF文件单独生成一个输出文件夹。

## 功能特性

- 📄 **PDF转Markdown**: 使用MinerU API将PDF转换为结构化Markdown
- 🧮 **自动提取DFT坐标**: 从计算化学部分自动识别和提取分子坐标
- 📁 **批量处理**: 支持同时处理多个PDF文件
- 📂 **独立输出**: 每个PDF文件生成单独的输出文件夹
- ⚙️ **可配置参数**: 支持自定义CPU核数、内存、计算方法等

## 快速开始

### 命令行使用

```bash
# 单个PDF文件
python extract_dft.py paper.pdf

# 批量处理整个目录
python extract_dft.py ./pdfs/

# 指定输出目录和计算参数
python extract_dft.py ./pdfs/ -o ./output/ --cpu 64 --mem 128GB
```

### Python API使用

```python
from extract_dft import process_pdf, batch_process

# 处理单个PDF
result = process_pdf(
    pdf_path="paper.pdf",
    output_dir="./output/paper1",
    cpu=64,
    mem="128GB",
    method="B3PW91/def2TZVP em=d3bj"
)

# 批量处理
results = batch_process(
    pdf_dir="./pdfs/",
    output_base_dir="./output",
    cpu=64,
    mem="128GB"
)
```

## 参数说明

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `-o, --output` | `./dft_output` | 输出目录 |
| `--cpu` | 64 | CPU核数 |
| `--mem` | 128GB | 内存 |
| `--method` | B3PW91/def2TZVP em=d3bj | 计算方法和色散校正 |
| `--solvent` | SMD(toluene) | 溶剂模型 |
| `--charge` | 0 | 电荷 |
| `--multiplicity` | 1 | 自旋多重度 |
| `--keywords` | opt freq | 计算关键词 |
| `--keep-temp` | False | 保留临时文件 |

### 关于Gaussian计算方法的写法

在Gaussian中，色散校正需要单独使用`em=`关键词指定，**不要**写成`B3PW91-D3(BJ)`的形式。

**✅ 正确写法：**
```
# B3PW91/def2TZVP em=d3bj opt freq
```

**❌ 错误写法：**
```
# B3PW91-D3(BJ)/def2TZVP opt freq   ← 这种写法Gaussian不识别
```

**常用色散校正关键词：**
| 色散校正 | 关键词 |
|----------|--------|
| D3 with Becke-Johnson damping | `em=d3bj` |
| D3 with zero damping | `em=d3` or `em=gd3` |
| D3(BJ) for DFT-D3 | `em=d3bj` |
| Grimme's GD3 | `em=gd3` |
| GD3BJ | `em=gd3bj` |

**示例对比：**
```bash
# B3PW91 with D3BJ
--method "B3PW91/def2TZVP em=d3bj"

# B3LYP with GD3  
--method "B3LYP/6-31G(d) em=gd3"

# PBE0 with D3BJ
--method "PBE1PBE/def2TZVP em=d3bj"

# ωB97X-D (已内置色散，无需额外添加)
--method "wB97XD/def2TZVP"
```

## 输出目录结构

```
output/
├── paper1/                        # 每个PDF一个独立文件夹
│   ├── README.txt                 # 文件说明和统计
│   ├── 01_molecule_b3pw91.gjf    # 生成的gjf文件
│   ├── 02_molecule_b3pw91.gjf
│   └── ...
├── paper2/
│   ├── README.txt
│   └── ...
└── ...
```

## 生成的gjf文件格式

```
%chk=molecule.chk
%mem=128GB
%nprocshared=64
# B3PW91/def2TZVP em=d3bj nosymm int=ultrafine SMD(toluene) opt freq

molecule_name

0 1
C      -1.46713000   0.31261700   0.00075400
H      -1.10131700   0.82908900  -0.88608000
...
```

**注意：** 色散校正`em=d3bj`是单独的关键词，不是方法名的一部分。这是Gaussian的标准写法。

## 完整示例

### 示例1: 处理单个PDF

```bash
python extract_dft.py 41557_2026_2096_MOESM1_ESM.pdf \
    -o ./output \
    --cpu 64 \
    --mem 128GB \
    --method "B3PW91/def2TZVP em=d3bj" \
    --solvent "SMD(toluene)"
```

生成的关键词行：
```
# B3PW91/def2TZVP em=d3bj nosymm int=ultrafine SMD(toluene) opt freq
```

**注意：** `em=d3bj`是独立的Gaussian关键词，用于启用Grimme的D3色散校正（Becke-Johnson阻尼），不是方法名的一部分。

输出:
```
./output/
├── README.txt
├── 01_trifluoroethane_b3pw91.gjf
├── 02_khmds_dimer_b3pw91.gjf
├── 03_khmds_monomer_b3pw91.gjf
└── ... (174个gjf文件)
```

### 示例2: 批量处理多个PDF

```bash
# 将多个PDF放入一个目录
mkdir -p ./papers
cp paper1.pdf paper2.pdf paper3.pdf ./papers/

# 批量处理
python extract_dft.py ./papers/ -o ./all_outputs
```

输出:
```
./all_outputs/
├── paper1/
│   ├── README.txt
│   └── *.gjf
├── paper2/
│   ├── README.txt
│   └── *.gjf
└── paper3/
    ├── README.txt
    └── *.gjf
```

### 示例3: 不同DFT方法的写法

```bash
# B3PW91 with D3BJ (最常用的色散校正DFT)
python extract_dft.py paper.pdf --method "B3PW91/def2TZVP em=d3bj"

# B3LYP with GD3
python extract_dft.py paper.pdf --method "B3LYP/6-31G(d) em=gd3"

# PBE0 with D3BJ
python extract_dft.py paper.pdf --method "PBE1PBE/def2TZVP em=d3bj"

# ωB97X-D (长程校正泛函，已内置色散)
python extract_dft.py paper.pdf --method "wB97XD/def2TZVP"

# M06-2X (Minnesota泛函，已内置色散)
python extract_dft.py paper.pdf --method "M062X/def2TZVP"

# TPSSh with D3BJ (meta-GGA)
python extract_dft.py paper.pdf --method "TPSSh/def2TZVP em=d3bj"
```

### 示例4: Python API调用

```python
from extract_dft import process_pdf

# 自定义所有参数
result = process_pdf(
    pdf_path="supplementary_material.pdf",
    output_dir="./my_output",
    cpu=32,
    mem="64GB",
    method="B3LYP/6-31G(d) em=gd3",
    solvent="SMD(water)",
    charge=0,
    multiplicity=1,
    keywords="opt freq scrf"
)

if result["success"]:
    print(f"提取了 {result['molecule_count']} 个分子")
    print(f"输出目录: {result['output_dir']}")
else:
    print(f"错误: {result['error']}")
```

## 支持的计算方法

脚本会自动识别PDF中使用的计算方法，包括但不限于:
- B3PW91, B3LYP, PBE0, ωB97X-D, M06-2X, M06-L, BP86
- 支持各种色散校正 (D3, D3BJ, GD3, etc.)

**重要：** 在Gaussian输入文件中，色散校正必须通过独立的`em=`关键词指定，而不是作为方法名的一部分。

| 原文中的写法 | Gaussian正确写法 |
|--------------|------------------|
| B3PW91-D3(BJ) | `B3PW91/def2TZVP em=d3bj` |
| B3LYP-D3 | `B3LYP/6-31G(d) em=gd3` |
| PBE0-D3BJ | `PBE1PBE/def2TZVP em=d3bj` |
| ωB97X-D | `wB97XD/def2TZVP` (已内置色散) |
| M06-2X | `M062X/def2TZVP` (已内置色散) |

## 依赖要求

- Python 3.8+
- MinerU PDF Converter (会自动调用)

## 注意事项

1. **大文件处理**: 超过600页的PDF会自动分批处理
2. **每日限制**: MinerU API每日免费额度2000页
3. **网络要求**: 需要联网调用MinerU API
4. **文件名过滤**: 会自动过滤掉包含HTML标签或非法字符的分子名称
5. **坐标验证**: 会自动过滤原子数超过10000的异常结构

## 故障排除

### 问题: 未找到分子坐标
- 确保PDF中包含"Computed coordinates"或类似的坐标部分
- 检查PDF是否为扫描版(需要可搜索的文本)

### 问题: MinerU API调用失败
- 检查网络连接
- 可能是API限额已满，请等待或联系管理员

### 问题: 生成的gjf文件不完整
- 使用 `--keep-temp` 参数保留临时文件进行调试
- 检查PDF中的坐标表格格式是否标准

## 相关SKILL

- [mineru-pdf-converter](minerr-pdf-converter) - PDF转Markdown工具
