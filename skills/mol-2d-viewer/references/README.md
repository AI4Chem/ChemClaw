# Molecular Structure Visualizer

将 SMILES 或化学名称转换为分子结构图的 OpenClaw Skill。

## 功能特性

- ✅ SMILES → 分子结构图
- ✅ IUPAC 名称 → 自动转 SMILES 后绘制
- ✅ PNG/SVG 双格式支持
- ✅ 自定义尺寸和样式
- ✅ 批量生成
- ✅ 支持立体化学显示

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```bash
# 从 SMILES 生成
python3 scripts/mol_2d_viewer.py --smiles "CCO" --output ethanol.png

# 从名称生成
python3 scripts/mol_2d_viewer.py --name "aspirin" --output aspirin.svg

# 批量生成
python3 scripts/mol_2d_viewer.py --smiles "CCO,C1=CC=CC=C1" --output-dir ./molecules
```

### 在 OpenClaw 中使用

直接在对话框说：
- "画出 ethanol 的分子结构"
- "SMILES: CCO，生成结构图"
- "可视化 aspirin，保存为 SVG"

## 输出示例

### 单个分子

```bash
$ python3 mol_2d_viewer.py -s "CCO" -o ethanol.png
✓ 已生成：ethanol.png (300x300, PNG)
```

### 批量生成

```bash
$ python3 mol_2d_viewer.py -s "CCO,C1=CC=CC=C1" -d ./output
✓ 已生成：./output/mol_1.png
✓ 已生成：./output/mol_2.png
完成：2/2 成功
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--smiles` | `-s` | SMILES 字符串（可多个） | - |
| `--name` | `-n` | IUPAC 名称 | - |
| `--output` | `-o` | 输出文件路径 | 自动生成 |
| `--output-dir` | `-d` | 输出目录（批量模式） | `~/.openclaw/media/mol-2d-viewer` |

## 📁 飞书兼容性

**重要**：为了能在飞书中发送分子结构图，图片必须保存在 OpenClaw 媒体白名单目录内：

- ✅ `~/.openclaw/media/`
- ✅ `~/.openclaw/workspace/`
- ✅ `~/.openclaw/agents/`
- ❌ `/tmp/` 或其他自定义目录

本 skill 默认输出到 `~/.openclaw/media/mol-2d-viewer/`，可以直接在飞书中发送！
| `--format` | `-f` | 输出格式：png/svg | `png` |
| `--width` | `-W` | 图片宽度（像素） | `300` |
| `--height` | `-H` | 图片高度（像素） | `300` |
| `--kekulize` | `-k` | 凯库勒化（显示双键） | `false` |
| `--quiet` | `-q` | 安静模式 | `false` |

## 输出格式对比

| 格式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **PNG** | 文件小、兼容性好 | 放大失真 | 网页展示、PPT |
| **SVG** | 无限缩放、可编辑 | 文件较大 | 出版物、海报 |

## 样式选项

### 凯库勒化（--kekulize）

将芳香环显示为交替的单双键：

- 默认：苯环显示为圆圈
- `--kekulize`：苯环显示为交替双键

### 尺寸调整

```bash
# 小图（缩略图）
python3 mol_2d_viewer.py -s "CCO" -W 150 -H 150 -o small.png

# 大图（海报用）
python3 mol_2d_viewer.py -s "CCO" -W 800 -H 600 -o large.png
```

## 测试

```bash
# 测试简单分子
python3 scripts/mol_2d_viewer.py -s "CCO" -o test_ethanol.png

# 测试复杂分子
python3 scripts/mol_2d_viewer.py -s "CC(C)Cc1ccc(cc1)C(=O)O" -o test_ibuprofen.png

# 测试从名称生成
python3 scripts/mol_2d_viewer.py -n "caffeine" -o test_caffeine.png

# 测试批量生成
python3 scripts/mol_2d_viewer.py -s "CCO,C1=CC=CC=C1,CC(=O)Oc1ccccc1C(=O)O" -d test_output
```

## 常见问题

### Q: 为什么有些 SMILES 无法生成图片？
A: 检查 SMILES 语法是否正确。可以使用 RDKit 的 `Chem.MolFromSmiles()` 验证。

### Q: SVG 和 PNG 哪个更好？
A: 
- 网页展示/快速预览 → PNG
- 出版物/需要缩放 → SVG

### Q: 如何生成更清晰的图片？
A: 增加 `--width` 和 `--height` 参数，或使用 SVG 格式。

### Q: 可以自定义原子颜色吗？
A: 当前版本使用 RDKit 默认配色。自定义颜色需要修改脚本。

## 依赖说明

| 依赖 | 用途 |
|------|------|
| `rdkit` | 分子结构解析和渲染 |
| `Pillow` | PNG 图片生成 |
| `pubchempy` | IUPAC 名称转 SMILES |

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
