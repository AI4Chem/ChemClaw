# Reaction Data Extraction Skill

从化学文献 PDF 中精确提取化学反应数据，特别是反应条件优化信息。

## 快速开始

### 安装依赖

```bash
cd ~/.openclaw/workspace/skills/reaction-data-extraction
pip install -r requirements.txt
```

### 基本使用

```bash
# 提取单个 PDF
python3 scripts/reaction_data_extraction.py -i paper.pdf -o ./output

# 批量处理
python3 scripts/reaction_data_extraction.py -i ./papers/ -o ./output --batch

# 只提取表格数据
python3 scripts/reaction_data_extraction.py -i paper.pdf -o ./output --tables-only
```

### 运行测试

```bash
python3 scripts/test_extraction.py
```

## 输出格式

- **CSV**: 结构化表格，便于 Excel 打开
- **JSON**: 包含完整元数据
- **XLSX**: Excel 格式（需要安装 openpyxl）

## 提取的数据字段

- 反应物/产物
- 催化剂、配体、碱、溶剂
- 温度、时间、压力
- 产率（数值和类型）
- 反应类型
- 置信度评分

## 文档

详细文档请查看 [SKILL.md](SKILL.md)
