# Literature Parsing Skill

将 PDF 文献转换为 Markdown 文件并提取图表图片的 OpenClaw Skill。

**核心技术**：PyMuPDF + pdfplumber

## 功能特性

- ✅ PDF → Markdown 转换
- ✅ 智能空格修复（中英文混排）
- ✅ 提取嵌入的真实图片（非页面截图）
- ✅ 图片自动去重
- ✅ 表格识别与转换
- ✅ 元数据提取（标题、作者等）
- ✅ 批量处理支持
- ✅ 结构化输出

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install pymupdf pdfplumber Pillow
```

### 基本使用

```bash
# 转换单个 PDF
python3 scripts/literature_parsing.py --input paper.pdf --output ./output

# 批量转换
python3 scripts/literature_parsing.py -i "*.pdf" -o ./batch_output

# 只提取图片
python3 scripts/literature_parsing.py -i paper.pdf --extract-figures-only

# 只提取元数据
python3 scripts/literature_parsing.py -i paper.pdf --metadata-only
```

### 在 OpenClaw 中使用

直接在对话框说：
- "将这个 PDF 转换为 Markdown"
- "解析这篇文献，提取所有图片"
- "PDF to Markdown with figures"

## 输出结构

```
output_folder/
├── document.md              # 主 Markdown 文件
├── figures/                 # 提取的图片
│   ├── fig_001.png
│   ├── fig_002.png
│   └── ...
└── document_metadata.json   # 文档元数据
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--input` | `-i` | 输入 PDF 文件 | - |
| `--output` | `-o` | 输出目录 | `~/.openclaw/media/literature-parsing` |
| `--figures-dir` | `-f` | 图片输出子目录 | `figures` |
| `--min-figure-size` | `-m` | 最小图片尺寸 KB | `5` |
| `--extract-figures-only` | | 只提取图片 | `false` |
| `--metadata-only` | | 只提取元数据 | `false` |
| `--quiet` | `-q` | 安静模式 | `false` |

## 输出示例

### 基本转换

```bash
$ python3 scripts/literature_parsing.py -i paper.pdf -o ./output
✓ 处理中：paper.pdf
✓ 提取文本：45 页
✓ 提取图片：12 张
✓ 生成 Markdown: output/paper.md
完成：paper.pdf → output/paper.md
```

### 元数据提取

```bash
$ python3 scripts/literature_parsing.py -i paper.pdf --metadata-only
{
  "title": "Deep Learning for NLP",
  "authors": "John Smith, Jane Doe",
  "pages": 45,
  "figures_count": 12,
  "extracted_at": "2024-01-15T10:30:00"
}
```

## 📁 飞书兼容性

**重要**：为了能在飞书中发送生成的文件，输出目录必须在白名单内：

- ✅ `~/.openclaw/media/`
- ✅ `~/.openclaw/workspace/`
- ✅ `~/.openclaw/agents/`
- ❌ `/tmp/` 或其他自定义目录

本 skill 默认输出到 `~/.openclaw/media/literature-parsing/`，可以直接在飞书中发送！

## 依赖说明

| 依赖 | 用途 |
|------|------|
| `pymupdf` | PDF 解析、嵌入图片提取、元数据提取 |
| `pdfplumber` | 高质量文本提取、表格识别 |
| `Pillow` | 图片处理 |

## 测试

```bash
# 测试基本转换
python3 scripts/literature_parsing.py -i test.pdf -o ./test_output

# 测试批量处理
python3 scripts/literature_parsing.py -i "tests/*.pdf" -o ./test_batch

# 测试元数据提取
python3 scripts/literature_parsing.py -i test.pdf --metadata-only

# 测试只提取图片
python3 scripts/literature_parsing.py -i test.pdf --extract-figures-only -o ./test_figs
```

## 常见问题

### Q: 为什么提取的图片数量和我看到的不一样？
A: 本 skill 提取的是 PDF 中嵌入的真实图片对象，不是页面截图。有些 PDF 使用矢量图形绘制图表，这些不会被提取为图片。

### Q: 文字之间没有空格怎么办？
A: 本 skill 已内置智能空格修复功能，会自动在中英文之间添加空格。如果仍有问题，可能是 PDF 本身的文本编码问题。

### Q: 扫描版 PDF 能处理吗？
A: 当前版本不支持 OCR。扫描版 PDF 需要先用 OCR 工具（如 Tesseract）处理。可以安装可选依赖：
```bash
pip install pytesseract opencv-python
```

### Q: 如何提取更高质量的图片？
A: 本 skill 提取的是原始嵌入图片，质量已经是最佳的。降低 `--min-figure-size` 可以提取更多小图片。

### Q: 表格提取效果不好怎么办？
A: 复杂表格可能无法完美转换。可以手动调整生成的 Markdown 表格。

### Q: 如何批量处理大量文献？
A: 使用通配符或结合 shell 脚本：
```bash
for pdf in ~/downloads/*.pdf; do
    python3 scripts/literature_parsing.py -i "$pdf" -o ~/papers/library
done
```

## 性能优化

### 大文件处理

```bash
# 降低最小图片大小以提取更多图片
python3 scripts/literature_parsing.py -i large.pdf -o ./output --min-figure-size 2
```

### 批量处理优化

```bash
# 使用 GNU Parallel 并行处理
ls *.pdf | parallel -j 4 python3 scripts/literature_parsing.py -i {} -o ./output
```

## 输出格式

### Markdown 文件

生成的 Markdown 包含：
- 文档标题和元数据
- 按页组织的正文内容（带空格修复）
- 图片引用链接
- 表格（Markdown 格式）
- 图片列表（含尺寸信息）

### 图片文件

- 格式：保持原始格式（PNG、JPEG 等）
- 命名：fig_001.png, fig_002.png...
- 位置：output/figures/
- 去重：相同图片只保存一次

### 元数据 JSON

包含：
- 文件名、页数
- 标题、作者（如果可提取）
- 图片列表和位置、尺寸
- 提取时间

## 技术原理

### 图片提取

使用 PyMuPDF 的 `get_images()` 和 `extract_image()` 方法：

1. 遍历每一页
2. 获取嵌入的图片对象（xref）
3. 提取原始图片数据
4. MD5 哈希去重
5. 保存为顺序编号的文件

### 文本提取

使用 pdfplumber 的 `extract_text()` 方法：

1. 保持布局模式提取
2. 智能空格修复（中英文混排）
3. 段落识别
4. 标题检测

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
