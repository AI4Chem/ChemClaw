---
name: literature-parsing
description: 将 PDF 文献转换为 Markdown 文件，并提取所有图表图片。使用 MinerU (opendatalab) 进行工业级高质量解析。
trigger: ["PDF 转 Markdown", "PDF 转换", "文献解析", "提取图片", "PDF to Markdown", "convert PDF", "extract figures", "PDF 转 markdown", "解析文献", "PDF 提取", "PDF 转文字"]
---

# Literature Parsing Skill

将 PDF 文献完整转换为 Markdown 文件，并自动提取所有图表和图片。**使用 MinerU (opendatalab) 进行工业级高质量解析**。

## 触发条件

- 用户提供 PDF 文件并要求转换为 Markdown
- 提到"PDF 转 Markdown"、"文献解析"
- 说"提取 PDF 中的图片"、"extract figures from PDF"
- 需要批量处理多个 PDF 文件

## 功能特性

- ✅ **PDF → Markdown 转换** - 保留标题、段落、列表、公式等结构
- ✅ **智能空格处理** - 自动修复中英文之间的空格
- ✅ **图表提取** - 提取 PDF 中嵌入的真实图片
- ✅ **表格识别** - 检测并转换表格为 Markdown 格式
- ✅ **公式保留** - LaTeX 格式数学公式
- ✅ **元数据提取** - 提取标题、作者等信息
- ✅ **批量处理** - 支持同时处理多个 PDF
- ✅ **结构化输出** - 生成组织良好的 Markdown 文档

## 核心技术

| 组件 | 用途 |
|------|------|
| **MinerU** | 工业级 PDF 解析引擎 (opendatalab) |
| **Pipeline Backend** | 文本提取、布局分析 |
| **OCR** | 扫描版 PDF 文字识别 |

## 输出结构

转换后的目录结构：

```
output_folder/
├── document.md          # 主 Markdown 文件
├── images/              # 提取的图片
│   ├── xxx.jpg
│   ├── yyy.jpg
│   └── ...
└── document_metadata.json  # 文档元数据
```

## 使用方法

### 对话框中使用

```
将这个 PDF 转换为 Markdown
解析这篇文献，提取所有图片
PDF to Markdown with figures
批量转换这些 PDF 文件
```

### 命令行使用

```bash
# 基本转换（自动模式）
python3 scripts/literature_parsing.py -i paper.pdf -o ./output

# 文本 PDF（速度快）
python3 scripts/literature_parsing.py -i paper.pdf -o ./output -m txt

# 扫描版 PDF（使用 OCR）
python3 scripts/literature_parsing.py -i paper.pdf -o ./output -m ocr

# 指定语言（提高 OCR 准确率）
python3 scripts/literature_parsing.py -i paper.pdf -o ./output -l en

# 使用 GPU 加速
python3 scripts/literature_parsing.py -i paper.pdf -o ./output -d cuda
```

### 直接使用 MinerU

```bash
# 基本用法
mineru -p paper.pdf -o ./output

# 文本模式（无图片，速度快）
mineru -p paper.pdf -o ./output -m txt

# OCR 模式（扫描版）
mineru -p paper.pdf -o ./output -m ocr

# 指定语言
mineru -p paper.pdf -o ./output -l ch

# 指定设备
mineru -p paper.pdf -o ./output --device cpu
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--input` | `-i` | 输入 PDF 文件路径 | - |
| `--output` | `-o` | 输出目录 | `~/.openclaw/media/literature-parsing` |
| `--method` | `-m` | 解析方法：auto/txt/ocr | `auto` |
| `--lang` | `-l` | OCR 语言：ch/en 等 | `ch` |
| `--device` | `-d` | 设备：cpu/cuda | `cpu` |
| `--quiet` | `-q` | 安静模式（输出 JSON） | `false` |

## 输出示例

### 基本转换

```bash
$ python3 scripts/literature_parsing.py -i paper.pdf -o ./output
✓ 开始处理：paper.pdf
  输出目录：./output
  解析方法：auto
  设备：cpu
✓ 处理完成：paper.pdf
  Markdown: paper.md
  图片数量：12 张
✓ 文件已整理到：./output/paper

✅ 转换完成！
📄 Markdown: ./output/paper/paper.md
🖼️  图片：./output/paper/images (12 张)
📊 元数据：./output/paper/paper_metadata.json
```

### 批量处理

```bash
# 处理目录中所有 PDF
for pdf in *.pdf; do
  python3 scripts/literature_parsing.py -i "$pdf" -o ./output
done
```

## Markdown 输出格式

生成的 Markdown 文件结构：

```markdown
# 论文标题

作者信息

# Abstract

摘要内容...

# 1. Introduction

正文内容，保留 LaTeX 公式：$E = mc^2$

![Figure 1](images/xxx.jpg)

## 2. Methods

### 2.1 Data Collection

| Column 1 | Column 2 |
|----------|----------|
| Data A   | Data B   |

![Figure 2](images/yyy.jpg)

# References

[1] Author A, et al. Title. Journal, 2023.
```

## 依赖安装

```bash
# 安装 MinerU
pip install 'mineru[all]'

# 如果遇到 numpy 版本问题
pip install 'numpy<2.0' 'pandas<3.0'
```

## 特性说明

### 文本提取改进

- ✅ **智能空格修复** - 自动在中英文之间添加空格
- ✅ **保留布局** - 使用先进的布局分析
- ✅ **段落识别** - 自动检测段落边界
- ✅ **标题检测** - 识别标题层级

### 图片提取改进

- ✅ **嵌入图片提取** - 提取真实嵌入的图片
- ✅ **格式保留** - 保持原始图片格式（JPG/PNG）
- ✅ **按哈希命名** - 自动去重

### 公式处理

- ✅ **LaTeX 保留** - 内联公式 `$...$` 和显示公式 `$$...$$`
- ✅ **数学符号** - 完整保留数学符号

### 表格处理

- ✅ **自动检测** - 识别 PDF 中的表格
- ✅ **Markdown 转换** - 转换为标准 Markdown 表格

## 注意事项

- ✅ **自动创建目录** - 输出目录不存在时自动创建
- ✅ **图片去重** - 使用 MD5 哈希值自动去重
- ✅ **错误处理** - 损坏的 PDF 会跳过并报告
- ⚠️ **扫描版 PDF** - 使用 `-m ocr` 模式
- ⚠️ **加密 PDF** - 需要先解密
- ⚠️ **复杂布局** - 多栏复杂排版可能影响转换质量

## 错误处理

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| `File not found` | PDF 文件不存在 | 检查文件路径 |
| `Invalid PDF` | PDF 格式损坏 | 尝试修复或重新下载 |
| `Permission denied` | 无读取权限 | 检查文件权限 |
| `No images found` | 未找到图片 | PDF 可能使用矢量图形 |
| `Timeout` | 处理超时（>10 分钟） | 尝试 `-m txt` 模式或减小文件 |

## 与其他技能配合

### 与 chemical_file_converter 配合

处理化学文献时，可以：

1. **literature-parsing**: 提取 PDF 中的分子结构和反应式图片
2. **chemical_file_converter**: 转换提取的化学结构文件格式

### 与 mol_paper_renderer 配合

生成高质量论文：

1. **mol_paper_renderer**: 生成出版级分子图片
2. **literature-parsing**: 将包含这些图片的 PDF 转换为 Markdown

## 完整工作流程示例

### 示例 1: 单篇文献转换

```bash
# 转换单篇 PDF
python3 scripts/literature_parsing.py -i nature_paper.pdf -o ./papers/nature

# 查看结果
ls -la ./papers/nature/
# paper.md
# images/xxx.jpg ...
# paper_metadata.json
```

### 示例 2: 批量文献库处理

```bash
# 批量转换
mkdir -p ~/papers/library
for pdf in ~/downloads/*.pdf; do
  python3 scripts/literature_parsing.py -i "$pdf" -o ~/papers/library
done
```

### 示例 3: 只处理特定页面

```bash
# 使用 MinerU 直接处理
mineru -p paper.pdf -o ./output -s 0 -e 9  # 只处理前 10 页
```

## 性能优化

### 文本 PDF（无图片）

```bash
# 使用 txt 模式，速度更快
python3 scripts/literature_parsing.py -i paper.pdf -o ./output -m txt
```

### 扫描版 PDF

```bash
# 使用 OCR 模式
python3 scripts/literature_parsing.py -i scanned.pdf -o ./output -m ocr

# 指定语言提高准确率
python3 scripts/literature_parsing.py -i scanned.pdf -o ./output -m ocr -l en
```

### CPU/GPU 选择

```bash
# 使用 CPU（兼容性好）
python3 scripts/literature_parsing.py -i paper.pdf -o ./output -d cpu

# 使用 GPU（速度快，需要 CUDA）
python3 scripts/literature_parsing.py -i paper.pdf -o ./output -d cuda
```

## 输出目录白名单

**重要**：为了能在飞书等平台上发送生成的文件，输出目录必须在白名单内：

- ✅ `~/.openclaw/media/`
- ✅ `~/.openclaw/workspace/`
- ✅ `~/.openclaw/agents/`

本 skill 默认输出到 `~/.openclaw/media/literature-parsing/`，可以直接分享！

## 技术细节

### MinerU 优势

MinerU 是 opendatalab 开源的工业级 PDF 解析工具：

- 📊 **布局分析** - 准确识别标题、段落、表格、图片
- 📐 **公式识别** - 完整保留 LaTeX 数学公式
- 🖼️ **图片提取** - 提取真实嵌入的图片
- 📝 **OCR 支持** - 支持扫描版 PDF
- 🌍 **多语言** - 支持 109 种语言 OCR

### 与之前版本对比

| 特性 | PyMuPDF | MinerU |
|------|---------|--------|
| 文本提取 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 公式保留 | ❌ | ✅ |
| 表格识别 | ⭐⭐ | ⭐⭐⭐⭐ |
| 布局分析 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| OCR 支持 | ❌ | ✅ |
| 扫描版支持 | ❌ | ✅ |

### 处理流程

1. **布局分析** - 识别页面布局、文本区域、图片区域
2. **文本提取** - 从 PDF 中提取文本内容
3. **公式识别** - 识别并保留 LaTeX 公式
4. **表格识别** - 检测表格并转换为 Markdown
5. **图片提取** - 提取嵌入的图片
6. **OCR（可选）** - 对扫描版进行文字识别
7. **格式整理** - 生成结构化的 Markdown 文档
