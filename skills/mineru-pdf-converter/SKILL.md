---
name: mineru-pdf-converter
description: |
  Convert PDF files to Markdown using MinerU API. 
  使用MinerU API将PDF文件转换为Markdown格式。
  Use when Kimi needs to extract structured text, images, tables, and formulas from PDF documents while preserving document layout and formatting. 
  适用于需要提取结构化文本、图片、表格和公式并保留文档布局的场景。
  Supports batch conversion and outputs full.md with images/, JSON metadata, and other extracted assets. 
  支持批量转换，输出full.md、images/目录、JSON元数据等。
  Now supports large PDFs (600+ pages) by automatic splitting and merging.
  现已支持大文件(600+页)自动拆分和合并处理。
---

# MinerU PDF Converter | PDF转Markdown工具

将 PDF 文件转换为 Markdown 格式，完整保留图片、表格、公式和文档结构。**支持超过 600 页的大文件自动分批处理。**

## 功能特性

- 提取文本、图片、表格、公式
- 保留文档原始布局和格式
- **自动处理超过 600 页的大文件**（智能拆分、分批转换、自动合并）
- 输出包含：
  - `full.md` - 主 Markdown 文件
  - `images/` - 提取的图片目录
  - `*.json` - 布局分析和内容元数据
  - `*_origin.pdf` - 原始 PDF 副本

## 快速开始

### 环境准备

需要 Python 3.8+ 和依赖包：

```bash
pip install requests urllib3 pymupdf
```

### API Token 配置

Skill 已内置 API Key，**无需额外配置即可使用**。

如需使用自己的 Token，可通过以下方式（优先级从高到低）：

```bash
# 方式1: 命令行参数（最高优先级）
python scripts/pdf_to_markdown.py paper.pdf -t YOUR_TOKEN

# 方式2: 环境变量
export MINERU_API_TOKEN="your-api-token"

# 方式3: 修改 Skill 内置 Key
# 编辑 API_KEY 文件 (位于 skill 目录下)
```

### 使用方法

#### 命令行

```bash
# 单个文件（自动处理大文件）
python scripts/pdf_to_markdown.py paper.pdf -t $MINERU_API_TOKEN

# 批量转换整个目录
python scripts/pdf_to_markdown.py ./pdfs/ -t $MINERU_API_TOKEN -o ./output/

# 指定模型版本
python scripts/pdf_to_markdown.py paper.pdf -t $MINERU_API_TOKEN -m vlm
```

#### Python API

```python
from scripts.pdf_to_markdown import convert_pdf, convert_large_pdf, batch_convert, get_api_token

# 获取 Token（自动从环境变量或 Skill 内置获取）
token = get_api_token()

# 单个文件转换（自动检测文件大小，大文件自动分批处理）
result = convert_large_pdf(
    token=token,
    pdf_path="large_paper.pdf",  # 支持任意页数
    output_dir="output/paper",
    model_version="vlm"
)
print(result["files"])  # 查看提取的所有文件
print(result.get("batches"))  # 如果分批处理，显示批次数量

# 批量转换
results = batch_convert(
    token=token,
    pdf_paths=["a.pdf", "b.pdf"],
    output_base_dir="output"
)
```

## 大文件处理说明

MinerU API 单文件限制 **600 页**。本 Skill 已内置智能处理：

1. **自动检测**：检测 PDF 页数是否超过 600 页
2. **智能拆分**：按 600 页为一批次拆分 PDF（使用 PyMuPDF）
3. **分批转换**：依次转换每个批次
4. **自动合并**：将各批次的 Markdown 和图片合并为完整文件
5. **清理临时文件**：处理完成后自动清理拆分产生的临时文件

**示例输出（1655 页 PDF）：**
```
[LargePDF] 总页数: 1655
[LargePDF] 文件超过 600 页，需要分批处理
[Split] PDF 共 1655 页，将拆分为 3 个批次（每批最多 600 页）
[Split] 批次 1/3: 第 1-600 页 -> orca_part001.pdf
[Split] 批次 2/3: 第 601-1200 页 -> orca_part002.pdf
[Split] 批次 3/3: 第 1201-1655 页 -> orca_part003.pdf

# 各批次依次转换...

[Merge] 合并 3 个 Markdown 文件...
[LargePDF] 大文件处理完成!
```

## 参数说明

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `token` | str | - | MinerU API Token (必填) |
| `pdf_path` | str | - | PDF 文件路径或目录 |
| `output_dir` | str | "output" | 输出目录 |
| `model_version` | str | "vlm" | 模型: vlm/pipeline/MinerU-HTML |
| `max_wait` | int | 600 | 每批最大等待时间(秒) |

## 输出目录结构

```
output/
├── {pdf-name}/
│   ├── full.md              # 主 Markdown 文件（大文件为合并后的完整内容）
│   ├── images/              # 提取的图片
│   │   ├── batch0001_xxx.jpg  # 图片命名包含批次信息
│   │   └── ...
│   ├── layout.json          # 布局分析结果
│   ├── content_list_v2.json # 内容列表
│   └── *_origin.pdf         # 原始 PDF
```

## 模型版本选择

- `vlm` - 视觉语言模型，适合学术论文、复杂排版 (推荐)
- `pipeline` - 传统流水线，速度较快
- `MinerU-HTML` - 针对 HTML 文件优化

## 限制与注意

- 单文件最大 200MB
- **单文件最多 600 页**（本 Skill 已自动处理大文件拆分）
- 每日免费额度 2000 页
- 图片引用使用相对路径 `images/xxx.jpg`
- 遇到 SSL 问题时脚本会自动处理代理绕过

## 依赖安装

```bash
# 必需依赖
pip install requests urllib3

# 大文件处理需要（用于拆分 PDF）
pip install pymupdf
```
