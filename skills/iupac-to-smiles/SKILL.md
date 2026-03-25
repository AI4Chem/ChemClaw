---
name: iupac-to-smiles
description: 将 IUPAC 化学名称转换为 SMILES 字符串。完全使用 OPSIN API，支持聚合物智能解析。
trigger: ["IUPAC", "SMILES", "化学名称", "分子式", "name to smiles", "名称转换", "聚合物", "poly"]
---

# IUPAC Name to SMILES Converter

将 IUPAC 化学名称转换为 SMILES 字符串，**完全使用 OPSIN API**，支持聚合物智能解析。

## 触发条件

- 用户提供 IUPAC 名称并要求转换
- 提到"SMILES"、"化学名称转换"
- 说"name to smiles"、"IUPAC 转 SMILES"
- 提到聚合物名称（如 `poly[...]`）

## 功能

- ✅ **完全使用 OPSIN API**（剑桥大学）- 不再依赖 PubChem
- ✅ **聚合物智能解析** - 自动识别 `poly[...]`、`poly(...)` 格式
- ✅ **单体提取** - 从聚合物名称中提取单体并解析
- ✅ **连接基团识别** - 自动识别 oxy、thio、imino 等连接基团
- ✅ **批量转换** - 支持多个名称同时转换
- ✅ **分子信息** - 返回分子式、分子量等（普通化合物）
- ✅ **聚合物说明** - 生成聚合物结构说明

## 聚合物解析逻辑

对于聚合物名称如 `poly[oxy(1-methylethylene)]`：

1. **识别聚合物前缀**: `poly[...]`
2. **提取括号内容**: `oxy(1-methylethylene)`
3. **解析连接基团**: `oxy` → 氧原子 `-O-`
4. **解析单体**: `1-methylethylene` → 通过 OPSIN 转换为 SMILES
5. **组合结果**: 生成聚合物 SMILES 和说明

### 支持的连接基团

| 名称 | SMILES | 说明 |
|------|--------|------|
| oxy | O | 氧桥 -O- |
| thio | S | 硫桥 -S- |
| imino | NH | 亚氨基 -NH- |
| carbonyl | C=O | 羰基 |
| ester | C(=O)O | 酯基 |
| amide | C(=O)N | 酰胺基 |

## 使用方法

### 对话框中使用

```
把 ethanol 转成 SMILES
IUPAC: 2-hydroxypropanoic acid，转 SMILES
poly[oxy(1-methylethylene)] 转 SMILES
批量转换：ethanol, benzene, poly[oxyethylene]
```

### 命令行使用

```bash
# 单个名称转换
python3 scripts/iupac_to_smiles.py --name "ethanol"

# 聚合物转换
python3 scripts/iupac_to_smiles.py --name "poly[oxy(1-methylethylene)]"

# 批量转换
python3 scripts/iupac_to_smiles.py --names "ethanol,benzene,poly[oxyethylene]"

# 从文件读取
python3 scripts/iupac_to_smiles.py --input names.txt --output results.json

# 指定输出格式
python3 scripts/iupac_to_smiles.py --name "aspirin" --format csv
```

## 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--name` | `-n` | 单个 IUPAC 名称 | - |
| `--names` | `-N` | 多个名称（逗号分隔） | - |
| `--input` | `-i` | 输入文件（每行一个名称） | - |
| `--output` | `-o` | 输出文件路径 | 自动生成 |
| `--format` | `-f` | 输出格式：json/csv | `json` |
| `--quiet` | `-q` | 安静模式 | `false` |

## 输出示例

### 简单化合物

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
      "source": "OPSIN",
      "status": "success",
      "type": "simple"
    }
  ]
}
```

### 聚合物

```json
{
  "status": "success",
  "results": [
    {
      "input_name": "poly[oxy(1-methylethylene)]",
      "status": "success",
      "type": "polymer",
      "polymer_info": {
        "is_polymer": true,
        "monomers": [
          {"name": "1-methylethylene", "position": "repeat_unit"}
        ],
        "linkers": [
          {"name": "oxy", "smiles": "O", "position": "backbone"}
        ]
      },
      "monomer_results": [
        {
          "name": "1-methylethylene",
          "smiles": "CC(C)",
          "status": "success"
        }
      ],
      "polymer_smiles": "*OCC(C)*",
      "final_smiles": "*OCC(C)*",
      "explanation": "连接基团：oxy | 单体 SMILES: CC(C) | 聚合物 SMILES: *OCC(C)*"
    }
  ]
}
```

### CSV 格式

```csv
input_name,smiles,status,type,monomer_count,explanation
ethanol,CCO,success,simple,,
poly[oxy(1-methylethylene)],*OCC(C)*,success,polymer,1,连接基团：oxy | 单体 SMILES: CC(C)
```

## 依赖

```bash
pip install rdkit requests
```

## OPSIN API 说明

- **来源**: 剑桥大学化学系
- **网址**: https://opsin.ch.cam.ac.uk/
- **优势**: 
  - 支持复杂 IUPAC 名称解析
  - 对聚合物名称有更好的支持
  - 无需 API 密钥
- **限制**: 
  - 需要网络连接
  - 某些非常复杂的名称可能失败

## 聚合物解析示例

### 示例 1: poly[oxy(1-methylethylene)]

```
输入：poly[oxy(1-methylethylene)]
解析:
  - 聚合物类型：bracketed
  - 连接基团：oxy → O
  - 单体：1-methylethylene → CC(C)
输出：*OCC(C)* (聚环氧丙烷)
```

### 示例 2: poly[oxyethylene]

```
输入：poly[oxyethylene]
解析:
  - 聚合物类型：bracketed
  - 连接基团：oxy → O
  - 单体：ethylene → CC
输出：*OCC* (聚环氧乙烷)
```

### 示例 3: poly(methyl methacrylate)

```
输入：poly(methyl methacrylate)
解析:
  - 聚合物类型：bracketed
  - 单体：methyl methacrylate
输出：*CC(C)(C(=O)OC)* (PMMA)
```

## 注意事项

- ✅ **完全使用 OPSIN** - 不再使用 PubChem 作为后备
- ✅ **聚合物支持** - 自动识别和解析聚合物名称
- ✅ **灵活解析** - 支持多种聚合物命名格式
- ⚠️ 复杂聚合物可能无法完全解析 - OPSIN 对某些复杂名称支持有限
- ⚠️ 需要网络连接 - OPSIN API 需要在线访问
- ⚠️ 建议先测试常见化合物

## 错误处理

| 错误 | 说明 | 解决方案 |
|------|------|----------|
| `Name not found` | OPSIN 无法识别名称 | 检查拼写，尝试更简单的名称 |
| `API error` | OPSIN API 调用失败 | 检查网络连接 |
| `Parse error` | 聚合物解析失败 | 提供更标准的聚合物名称 |

## 与旧版本的区别

- ❌ **移除了 PubChem 后备** - 完全依赖 OPSIN
- ✅ **新增聚合物解析** - 智能识别和解析聚合物
- ✅ **新增连接基团识别** - 自动识别 oxy、thio 等
- ✅ **新增单体提取** - 从复杂名称中提取可解析的部分
- ✅ **更详细的输出** - 包含聚合物结构说明
