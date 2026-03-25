#!/usr/bin/env python3
"""
测试反应数据提取功能
"""

import sys
from pathlib import Path

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from reaction_data_extraction import ReactionDataExtractor


def test_basic_extraction():
    """测试基本提取功能"""
    print("=" * 60)
    print("测试：基本反应数据提取")
    print("=" * 60)
    
    extractor = ReactionDataExtractor(verbose=True)
    
    # 测试文本
    test_texts = [
        # Suzuki 偶联反应
        "The reaction of 4-bromotoluene with phenylboronic acid was carried out using Pd(PPh3)4 (5 mol%) as catalyst, K2CO3 (2.0 equiv) as base in DMF at 80 °C for 12 h, affording the desired product in 85% isolated yield.",
        
        # 条件优化
        "When the reaction was performed in toluene instead of DMF, the yield decreased to 72%. Using Pd(dppf)Cl2 as catalyst gave 91% yield.",
        
        # 温度优化
        "At 100 °C, the reaction completed in 6 h with 88% yield. At room temperature, no reaction was observed.",
        
        # 溶剂筛选
        "Various solvents were screened: THF (65% yield), DMSO (78% yield), MeCN (45% yield), and dioxane (82% yield).",
    ]
    
    all_reactions = []
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n测试文本 {i}:")
        print(f"  \"{text[:80]}...\"")
        
        reactions = extractor.extract_from_text(text)
        
        for rxn in reactions:
            print(f"\n  提取结果:")
            print(f"    ID: {rxn.get('reaction_id')}")
            print(f"    反应物：{rxn.get('reactants', [])}")
            print(f"    催化剂：{rxn.get('catalyst')}")
            print(f"    溶剂：{rxn.get('solvent')}")
            print(f"    温度：{rxn.get('temperature')}")
            print(f"    时间：{rxn.get('time')}")
            print(f"    产率：{rxn.get('yield_value')}%")
            print(f"    置信度：{rxn.get('confidence'):.2f}")
            
            all_reactions.append(rxn)
    
    print(f"\n{'=' * 60}")
    print(f"总计：提取 {len(all_reactions)} 个反应")
    print(f"{'=' * 60}\n")
    
    return all_reactions


def test_table_extraction():
    """测试表格数据提取"""
    print("=" * 60)
    print("测试：表格反应数据提取")
    print("=" * 60)
    
    import pandas as pd
    
    # 模拟反应条件优化表格
    data = {
        'Entry': [1, 2, 3, 4, 5],
        'Catalyst': ['Pd(PPh3)4', 'Pd(dppf)Cl2', 'Pd(OAc)2', 'NiCl2(dppp)', 'CuI'],
        'Ligand': ['PPh3', 'dppf', '-', 'dppp', '-'],
        'Base': ['K2CO3', 'Na2CO3', 'K2CO3', 'K3PO4', 'Cs2CO3'],
        'Solvent': ['DMF', 'DMF', 'Toluene', 'DMF', 'DMSO'],
        'Temp (°C)': [80, 80, 80, 80, 100],
        'Time (h)': [12, 12, 24, 12, 6],
        'Yield (%)': [85, 91, 72, 45, 38],
    }
    
    df = pd.DataFrame(data)
    
    print("\n模拟表格数据:")
    print(df.to_string())
    print()
    
    extractor = ReactionDataExtractor(verbose=True)
    reactions = extractor.extract_from_table(df, "Table 1")
    
    print(f"提取结果:")
    for rxn in reactions:
        print(f"\n  Entry {rxn.get('entry')}:")
        print(f"    催化剂：{rxn.get('catalyst')}")
        print(f"    配体：{rxn.get('ligand')}")
        print(f"    碱：{rxn.get('base')}")
        print(f"    溶剂：{rxn.get('solvent')}")
        print(f"    温度：{rxn.get('temperature')}")
        print(f"    时间：{rxn.get('time')}")
        print(f"    产率：{rxn.get('yield_value')}%")
        print(f"    置信度：{rxn.get('confidence'):.2f}")
    
    print(f"\n{'=' * 60}")
    print(f"总计：提取 {len(reactions)} 个反应")
    print(f"{'=' * 60}\n")
    
    return reactions


def test_smiles_conversion():
    """测试化学名称到 SMILES 转换"""
    print("=" * 60)
    print("测试：化学名称 → SMILES 转换")
    print("=" * 60)
    
    test_names = [
        "4-bromotoluene",
        "phenylboronic acid",
        "benzene",
        "ethanol",
        "acetic acid",
    ]
    
    extractor = ReactionDataExtractor()
    
    print()
    for name in test_names:
        smiles = extractor.convert_to_smiles(name)
        if smiles:
            print(f"  {name:25} → {smiles}")
        else:
            print(f"  {name:25} → 转换失败")
    
    print()


def main():
    """运行所有测试"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Reaction Data Extraction Tests" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # 测试 1: 基本提取
    text_reactions = test_basic_extraction()
    
    # 测试 2: 表格提取
    table_reactions = test_table_extraction()
    
    # 测试 3: SMILES 转换
    test_smiles_conversion()
    
    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"  文本提取反应：{len(text_reactions)}")
    print(f"  表格提取反应：{len(table_reactions)}")
    print(f"  总计：{len(text_reactions) + len(table_reactions)}")
    print()
    
    # 保存测试输出
    output_dir = Path(__file__).parent.parent / "test_output"
    output_dir.mkdir(exist_ok=True)
    
    extractor = ReactionDataExtractor()
    
    all_reactions = text_reactions + table_reactions
    csv_path = output_dir / "test_reactions.csv"
    extractor.save_to_csv(all_reactions, csv_path)
    
    json_path = output_dir / "test_reactions.json"
    extractor.save_to_json(all_reactions, json_path, {
        'test': True,
        'date': '2026-03-17'
    })
    
    print(f"✓ 测试输出已保存:")
    print(f"    CSV: {csv_path}")
    print(f"    JSON: {json_path}")
    print()


if __name__ == '__main__':
    main()
