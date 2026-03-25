# IUPAC Name to SMILES Converter

将 IUPAC 化学名称转换为 SMILES 字符串的 OpenClaw Skill。

## 功能特性

- ✅ IUPAC 名称 → SMILES 转换
- ✅ 批量转换支持
- ✅ 返回标准化 SMILES 和 Isomeric SMILES
- ✅ 提供分子式、分子量等理化性质
- ✅ 支持从文件批量读取
- ✅ JSON/CSV 双格式输出

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 基本使用

```bash
# 单个名称转换
python3 scripts/iupac_to_smiles.py --name "ethanol"

# 批量转换
python3 scripts/iupac_to_smiles.py --names "ethanol,benzene,aspirin"

# 从文件读取
python3 scripts/iupac_to_smiles.py --input names.txt --output results.json
```

### 在 OpenClaw 中使用

直接在对话框说：
- "把 ethanol 转成 SMILES"
- "IUPAC: 2-hydroxypropanoic acid，转 SMILES"
- "批量转换：ethanol, benzene, aspirin"

## 输出示例

### JSON 格式

```json
{
  "status": "success",
  "results": [
    {
      "input_name": "ethanol",
      "smiles": "CCO",
      "isomeric_smiles": "CCO",
      "molecular_formula": "C2H6O",
      "molecular_weight": 46.07,
      "cid": 702,
      "synonyms": ["ethyl alcohol", "alcohol"]
    }
  ]
}
```

### CSV 格式

```csv
input_name,smiles,isomeric_smiles,molecular_formula,molecular_weight
ethanol,CCO,CCO,C2H6O,46.07
benzene,C1=CC=CC=C1,c1ccccc1,C6H6,78.11
aspirin,CC(=O)Oc1ccccc1C(=O)O,CC(=O)Oc1ccccc1C(=O)O,C9H8O4,180.16
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--name` | `-n` | 单个 IUPAC 名称 | - |
| `--names` | `-N` | 多个名称（逗号分隔） | - |
| `--input` | `-i` | 输入文件（每行一个名称） | - |
| `--output` | `-o` | 输出文件路径 | 自动生成 |
| `--format` | `-f` | 输出格式：json/csv | `json` |
| `--no-info` | | 不包含分子信息 | `false` |
| `--quiet` | `-q` | 安静模式 | `false` |

## 返回的分子信息

| 字段 | 说明 |
|------|------|
| `smiles` | 标准 SMILES |
| `isomeric_smiles` | 异构 SMILES（包含立体化学） |
| `molecular_formula` | 分子式 |
| `molecular_weight` | 分子量 |
| `exact_mass` | 精确质量 |
| `logp` | 疏水性（LogP） |
| `h_bond_donors` | 氢键供体数 |
| `h_bond_acceptors` | 氢键受体数 |
| `rotatable_bonds` | 可旋转键数 |
| `tpsa` | 拓扑极性表面积 |

## 测试

```bash
# 测试单个化合物
python3 scripts/iupac_to_smiles.py -n "aspirin"

# 测试批量转换
python3 scripts/iupac_to_smiles.py -N "ethanol,benzene,caffeine"

# 测试文件输入
echo -e "ethanol\nbenzene\naspirin" > test_names.txt
python3 scripts/iupac_to_smiles.py -i test_names.txt -o test_results.json
```

## 常见问题

### Q: 为什么有些名称无法识别？
A: 使用 PubChem API 进行匹配，建议使用标准 IUPAC 名称或常见俗名。复杂化合物可以使用 CAS 号。

### Q: 如何提高转换成功率？
A: 
- 使用标准 IUPAC 命名
- 尝试常见俗名（如 aspirin 而非 acetylsalicylic acid）
- 使用 CAS 号（如果知道）

### Q: 批量转换有数量限制吗？
A: 理论上无限制，但建议分批处理（每批 100 个以内）以避免 API 限流。

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
