---
name: mol-2d-viewer
description: 将 SMILES 或化学名称转换为分子 2D 结构图。支持普通分子和聚合物 2D 结构绘制。
trigger: ["2D 分子", "分子 2D", "2D 结构", "2D visualization", "molecule 2D", "分子结构图", "SMILES 转图片", "draw molecule", "聚合物结构"]
---

# Molecular Structure Visualizer

将 SMILES 字符串或化学名称转换为分子结构图，**支持聚合物 2D 结构绘制**。

## 触发条件

- 用户提供 SMILES 并要求可视化
- 提到"分子结构"、"可视化"、"draw molecule"
- 说"SMILES 转图片"、"显示结构"
- 提供聚合物名称或 SMILES

## 功能

- ✅ **SMILES → 分子结构图**
- ✅ **IUPAC 名称 → 结构图**（自动通过 OPSIN 转 SMILES）
- ✅ **聚合物支持** - 正确渲染聚合物重复单元
- ✅ **输出 PNG 或 SVG 格式**
- ✅ **可自定义尺寸、样式**
- ✅ **批量生成**
- ✅ **聚合物标题** - 自动添加化合物名称作为标题

## 聚合物渲染

对于聚合物 SMILES（包含 `*` 连接点标记）：

- 自动识别聚合物标记
- 清理 SMILES 以便正确渲染
- 添加"Polymer Structure"标题
- 使用增强的渲染选项（更粗的键、更大的原子标签）

### 聚合物 SMILES 格式

```
*monomer*          # 简单聚合物
*[linker]monomer*  # 带连接基团的聚合物
*CC*               # 聚乙烯
*OCC*              # 聚环氧乙烷
*OCC(C)*           # 聚环氧丙烷
```

## 使用方法

### 对话框中使用

```
画出 ethanol 的分子结构
SMILES: CCO，生成结构图
可视化 aspirin，保存为 SVG
poly[oxy(1-methylethylene)] 画结构图
批量生成：CCO,C1=CC=CC=C1
```

### 命令行使用

```bash
# 从 SMILES 生成
python3 scripts/mol_2d_viewer.py --smiles "CCO" --output ethanol.png

# 从名称生成
python3 scripts/mol_2d_viewer.py --name "aspirin" --output aspirin.svg

# 聚合物 SMILES
python3 scripts/mol_2d_viewer.py --smiles "*OCC*" --output peo.png

# 聚合物名称
python3 scripts/mol_2d_viewer.py --name "poly[oxy(1-methylethylene)]" --output ppo.png

# 批量生成
python3 scripts/mol_2d_viewer.py --smiles "CCO,C1=CC=CC=C1" --output-dir ./molecules

# 自定义尺寸
python3 scripts/mol_2d_viewer.py --smiles "CCO" --width 400 --height 300
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--smiles` | `-s` | SMILES 字符串（可多个） | - |
| `--name` | `-n` | IUPAC 名称 | - |
| `--output` | `-o` | 输出文件路径 | 自动生成 |
| `--output-dir` | `-d` | 输出目录（批量模式） | `~/.openclaw/media/mol-2d-viewer` |
| `--format` | `-f` | 输出格式：png/svg | `png` |
| `--width` | `-W` | 图片宽度（像素） | `400` |
| `--height` | `-H` | 图片高度（像素） | `300` |
| `--kekulize` | `-k` | 凯库勒化（显示双键） | `false` |
| `--quiet` | `-q` | 安静模式 | `false` |
| `--stdout` | | 输出 base64 到 stdout | `false` |

## 输出示例

### 单个分子

```bash
$ python3 mol_2d_viewer.py -s "CCO" -o ethanol.png
✓ 已生成：ethanol.png (400x300, PNG)
```

### 聚合物

```bash
$ python3 mol_2d_viewer.py -s "*OCC*" -o peo.png
✓ 已生成：peo.png (400x300, PNG) [聚合物]

$ python3 mol_2d_viewer.py -n "poly[oxy(1-methylethylene)]" -o ppo.png
✓ 已生成：ppo.png (400x300, PNG) [聚合物]
```

### 批量生成

```bash
$ python3 mol_2d_viewer.py -s "CCO,C1=CC=CC=C1" -d ./output
✓ 已生成：./output/mol_1.png
✓ 已生成：./output/mol_2.png
完成：2/2 成功
```

## 依赖

```bash
pip install rdkit Pillow requests
```

## 输出格式

### PNG

- 位图格式
- 适合网页展示
- 文件较小
- 聚合物使用增强的 Cairo 渲染

### SVG

- 矢量格式
- 无限缩放不失真
- 适合出版物
- 支持标题嵌入

## 聚合物渲染选项

| 选项 | 说明 | 默认 |
|------|------|------|
| 键宽度 | 化学键线宽 | 2 |
| 原子标签字体 | 元素符号大小 | 14 |
| 高亮键宽倍数 | 高亮显示倍数 | 3 |
| 标题 | 化合物名称 | 自动 |

## 完整工作流程示例

### 示例 1: 从 IUPAC 名称到结构图

```bash
# 1. 转换名称为 SMILES
python3 scripts/iupac_to_smiles.py --name "poly[oxy(1-methylethylene)]"

# 输出:
# {
#   "polymer_smiles": "*OCC(C)*",
#   "explanation": "连接基团：oxy | 单体 SMILES: CC(C)"
# }

# 2. 绘制结构图
python3 scripts/mol_2d_viewer.py --smiles "*OCC(C)*" --output ppo.png --title "PPO"
```

### 示例 2: 批量处理

```bash
# 创建输入文件
cat > polymers.txt << EOF
poly[oxyethylene]
poly[methyl methacrylate]
poly[styrene]
EOF

# 批量转换
python3 scripts/iupac_to_smiles.py --input polymers.txt --output polymers.json

# 提取 SMILES 并批量绘制
python3 scripts/mol_2d_viewer.py --smiles "*OCC*,*CC(C)(C(=O)OC)*,*CC(C1=CC=CC=C1)*" \
  --output-dir ./polymers --format png
```

## 注意事项

- ✅ **聚合物自动识别** - 包含 `*` 的 SMILES 自动按聚合物渲染
- ✅ **名称转结构** - IUPAC 名称自动通过 OPSIN 转换
- ✅ **增强渲染** - 聚合物使用更大的字体和更粗的键
- ⚠️ 复杂聚合物可能渲染不完整 - RDKit 对某些复杂重复单元支持有限
- ⚠️ 需要网络连接 - IUPAC 名称转换需要 OPSIN API
- ⚠️ SVG 文件通常比 PNG 大

## 错误处理

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| `Invalid SMILES` | SMILES 格式错误 | 检查语法，确保括号匹配 |
| `Cannot parse` | 无法解析结构 | 简化 SMILES 或检查聚合物标记 |
| `Name not found` | 名称无法识别 | OPSIN 无法识别，使用 SMILES 直接输入 |

## 与 iupac_to_smiles 技能配合使用

这两个技能可以完美配合：

1. **iupac_to_smiles**: 将 IUPAC 名称（包括聚合物）转换为 SMILES
2. **mol_2d_viewer**: 将 SMILES 转换为可视化的 2D 结构图

```bash
# 完整流程示例
# 1. 转换
python3 scripts/iupac_to_smiles.py -n "poly[oxy(1-methylethylene)]" -o result.json

# 2. 从结果提取 SMILES 并绘制
SMILES=$(cat result.json | jq -r '.results[0].polymer_smiles')
python3 scripts/mol_2d_viewer.py -s "$SMILES" -o structure.png
```

## 支持的聚合物类型

| 聚合物 | SMILES 示例 | 说明 |
|--------|------------|------|
| 聚乙烯 | `*CC*` | 最简单的碳链聚合物 |
| 聚环氧乙烷 | `*OCC*` | 含氧连接基团 |
| 聚环氧丙烷 | `*OCC(C)*` | 带侧链的聚醚 |
| 聚苯乙烯 | `*CC(C1=CC=CC=C1)*` | 含苯环侧链 |
| PMMA | `*CC(C)(C(=O)OC)*` | 聚甲基丙烯酸甲酯 |
