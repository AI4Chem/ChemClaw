#!/usr/bin/env python3
"""
手动提取 JACS 论文中的反应数据
"""

import re
import json
import csv
from pathlib import Path

# 从 PDF 提取的关键反应数据（基于文本解析）
reactions = []

# Table 1: 反应条件优化数据
table1_entries = [
    {
        "entry": 1,
        "deviation": "none",
        "yield": 99,
        "isolated_yield": 99,
        "ee": 99,
        "E_Z": ">20:1",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L7",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": "标准条件 (standard conditions)"
    },
    {
        "entry": 2,
        "deviation": "Pd(OAc)₂",
        "yield": "trace",
        "ee": "-",
        "E_Z": "-",
        "catalyst": "Pd(OAc)₂",
        "ligand": "L7",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": "催化剂筛选"
    },
    {
        "entry": 3,
        "deviation": "PdCl₂",
        "yield": "ND",
        "ee": "-",
        "E_Z": "-",
        "catalyst": "PdCl₂",
        "ligand": "L7",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": "未检测到"
    },
    {
        "entry": 4,
        "deviation": "Pd(dba)₂",
        "yield": 97,
        "ee": 99,
        "E_Z": ">20:1",
        "catalyst": "Pd(dba)₂",
        "ligand": "L7",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": ""
    },
    {
        "entry": 5,
        "deviation": "2,6-DMBQ",
        "yield": 98,
        "ee": 80,
        "E_Z": ">20:1",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L7",
        "oxidant": "2,6-DMBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": "氧化剂筛选"
    },
    {
        "entry": 6,
        "deviation": "DQ",
        "yield": "ND",
        "ee": "-",
        "E_Z": "-",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L7",
        "oxidant": "DQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": ""
    },
    {
        "entry": 7,
        "deviation": "2,6-DTBQ",
        "yield": "ND",
        "ee": "-",
        "E_Z": "-",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L7",
        "oxidant": "2,6-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": ""
    },
    {
        "entry": 8,
        "deviation": "L1",
        "yield": "trace",
        "ee": "-",
        "E_Z": "-",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L1",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": "配体筛选"
    },
    {
        "entry": 9,
        "deviation": "L2",
        "yield": 30,
        "ee": 0,
        "E_Z": ">20:1",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L2",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": ""
    },
    {
        "entry": 10,
        "deviation": "L3",
        "yield": 35,
        "ee": 48,
        "E_Z": ">20:1",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L3",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": ""
    },
    {
        "entry": 11,
        "deviation": "L4",
        "yield": 80,
        "ee": 50,
        "E_Z": ">20:1",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L4",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": ""
    },
    {
        "entry": 12,
        "deviation": "L5/L6",
        "yield": "45/80",
        "ee": "74/80",
        "E_Z": ">20:1",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L5/L6",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": ""
    },
    {
        "entry": 13,
        "deviation": "L8",
        "yield": 25,
        "ee": 88,
        "E_Z": ">20:1",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L8",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": ""
    },
    {
        "entry": 14,
        "deviation": "acetone",
        "yield": 32,
        "ee": 84,
        "E_Z": "1:1.5",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L7",
        "oxidant": "2,5-DTBQ",
        "solvent": "acetone",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": "溶剂筛选"
    },
    {
        "entry": 15,
        "deviation": "without Pd₂(dba)₃",
        "yield": "ND",
        "ee": "-",
        "E_Z": "-",
        "catalyst": "none",
        "ligand": "L7",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": "对照实验"
    },
    {
        "entry": 16,
        "deviation": "without L7",
        "yield": "ND",
        "ee": "-",
        "E_Z": "-",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "none",
        "oxidant": "2,5-DTBQ",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": "对照实验"
    },
    {
        "entry": 17,
        "deviation": "without 2,5-DTBQ",
        "yield": "ND",
        "ee": "-",
        "E_Z": "-",
        "catalyst": "Pd₂(dba)₃",
        "ligand": "L7",
        "oxidant": "none",
        "solvent": "MeOH",
        "temperature": "40 °C",
        "time": "24 h",
        "notes": "对照实验"
    }
]

# 反应物信息
reactant_info = {
    "alkene": "methyl (Z)-oct-2-enoate (1a)",
    "amine": "aniline (2a)",
    "product": "γ-amino ester (3a)",
    "reaction_type": "asymmetric oxidative allylic amination"
}

# 构建完整的反应数据
reactions = []
for entry in table1_entries:
    reaction = {
        "reaction_id": f"RXN_{entry['entry']:03d}",
        "entry": entry["entry"],
        "reactants": [reactant_info["alkene"], reactant_info["amine"]],
        "products": [reactant_info["product"]],
        "catalyst": entry["catalyst"],
        "ligand": entry["ligand"],
        "oxidant": entry["oxidant"],
        "base": None,
        "solvent": entry["solvent"],
        "temperature": entry["temperature"],
        "time": entry["time"],
        "yield_value": entry["yield"],
        "isolated_yield": entry.get("isolated_yield"),
        "ee_value": entry["ee"],
        "E_Z_ratio": entry["E_Z"],
        "reaction_type": reactant_info["reaction_type"],
        "scheme_number": "Table 1",
        "page_number": 2,
        "deviation_from_standard": entry["deviation"],
        "notes": entry["notes"],
        "confidence": 0.95
    }
    reactions.append(reaction)

# 输出目录
output_dir = Path("/home/lla/.openclaw/media/reaction-data-extraction/output_manual")
output_dir.mkdir(parents=True, exist_ok=True)

# 保存为 CSV
csv_file = output_dir / "reaction_conditions_table1.csv"
with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    fieldnames = [
        'reaction_id', 'entry', 'reactants', 'products', 'catalyst', 'ligand',
        'oxidant', 'base', 'solvent', 'temperature', 'time', 'yield_value',
        'isolated_yield', 'ee_value', 'E_Z_ratio', 'reaction_type',
        'scheme_number', 'page_number', 'deviation_from_standard', 'notes', 'confidence'
    ]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for rxn in reactions:
        # 将列表转换为字符串
        row = rxn.copy()
        row['reactants'] = '; '.join(rxn['reactants'])
        row['products'] = '; '.join(rxn['products'])
        writer.writerow(row)

# 保存为 JSON
json_file = output_dir / "reaction_conditions_table1.json"
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump({
        "paper_title": "Palladium-Catalyzed Asymmetric Oxidative Amination of Internal α,β-Unsaturated Esters with Lewis Basic Amines",
        "journal": "J. Am. Chem. Soc.",
        "year": 2026,
        "doi": "10.1021/jacs.5c17010",
        "extraction_date": "2026-03-17",
        "table_number": "Table 1",
        "table_description": "Optimization of the Reaction Conditions",
        "total_entries": len(reactions),
        "optimal_condition": "Entry 1",
        "reactions": reactions
    }, f, indent=2, ensure_ascii=False)

# 生成摘要报告
summary_file = output_dir / "extraction_summary.txt"
with open(summary_file, 'w', encoding='utf-8') as f:
    f.write("反应条件优化数据提取报告\n")
    f.write("=" * 60 + "\n\n")
    f.write(f"文献标题：Palladium-Catalyzed Asymmetric Oxidative Amination...\n")
    f.write(f"期刊：J. Am. Chem. Soc. 2026\n")
    f.write(f"DOI: 10.1021/jacs.5c17010\n")
    f.write(f"提取日期：2026-03-17\n\n")
    
    f.write("反应概述:\n")
    f.write(f"  反应类型：{reactant_info['reaction_type']}\n")
    f.write(f"  烯烃底物：{reactant_info['alkene']}\n")
    f.write(f"  胺底物：{reactant_info['amine']}\n")
    f.write(f"  产物：{reactant_info['product']}\n\n")
    
    f.write("Table 1 条件优化摘要:\n")
    f.write(f"  总条目数：{len(reactions)}\n")
    f.write(f"  最优条件：Entry 1\n")
    f.write(f"  最佳产率：99% (分离产率)\n")
    f.write(f"  最佳 e.e.: 99%\n")
    f.write(f"  E/Z 选择性：>20:1\n\n")
    
    f.write("最优反应条件:\n")
    f.write("  催化剂：Pd₂(dba)₃ (2.5 mol%)\n")
    f.write("  配体：L7 (6.0 mol%)\n")
    f.write("  氧化剂：2,5-DTBQ (1.2 equiv)\n")
    f.write("  溶剂：MeOH\n")
    f.write("  温度：40 °C\n")
    f.write("  时间：24 h\n")
    f.write("  气氛：N₂\n\n")
    
    f.write("关键发现:\n")
    f.write("  1. Pd₂(dba)₃ 是最佳催化剂前体\n")
    f.write("  2. L7 配体提供最佳对映选择性\n")
    f.write("  3. 2,5-DTBQ 是最佳氧化剂\n")
    f.write("  4. MeOH 是最佳溶剂\n")
    f.write("  5. 无催化剂/配体/氧化剂时反应不进行\n\n")
    
    f.write("输出文件:\n")
    f.write(f"  CSV: {csv_file}\n")
    f.write(f"  JSON: {json_file}\n")
    f.write(f"  摘要：{summary_file}\n")

print(f"✅ 手动提取完成！")
print(f"📊 CSV: {csv_file}")
print(f"📋 JSON: {json_file}")
print(f"📝 摘要：{summary_file}")
print(f"\n共提取 {len(reactions)} 个反应条件优化条目")
