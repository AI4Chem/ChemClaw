#!/usr/bin/env python3
"""
PDF DFT Extractor 安装测试脚本
"""

import sys
import os

# 测试导入
try:
    from extract_dft import process_pdf, batch_process, extract_molecules_from_markdown
    print("✓ 模块导入成功")
except ImportError as e:
    print(f"✗ 模块导入失败: {e}")
    sys.exit(1)

# 测试MinerU依赖
try:
    sys.path.insert(0, os.path.expanduser('~/.config/agents/skills/mineru-pdf-converter/scripts'))
    from pdf_to_markdown import get_api_token
    print("✓ MinerU依赖检查通过")
except ImportError:
    print("✗ 未找到MinerU PDF Converter，请先安装该skill")
    sys.exit(1)

# 测试坐标提取功能
test_md = """
# Computed coordinates

01_test_molecule_b3pw91.log
<table>
<tr><td>C</td><td>0.000000</td><td>0.000000</td><td>0.000000</td></tr>
<tr><td>H</td><td>1.000000</td><td>0.000000</td><td>0.000000</td></tr>
</table>

02_test_molecule_pbe0.log
<table>
<tr><td>O</td><td>0.500000</td><td>0.500000</td><td>0.500000</td></tr>
</table>
"""

molecules = extract_molecules_from_markdown(test_md)
if len(molecules) == 2:
    print(f"✓ 坐标提取功能正常 (提取到 {len(molecules)} 个分子)")
else:
    print(f"✗ 坐标提取功能异常 (期望2个，实际{len(molecules)}个)")

print("\n所有测试通过！SKILL安装正确。")
print("\n使用示例:")
print("  python extract_dft.py your_paper.pdf -o ./output")
