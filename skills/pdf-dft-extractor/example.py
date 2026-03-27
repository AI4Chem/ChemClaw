#!/usr/bin/env python3
"""
PDF DFT Extractor 使用示例
"""

from extract_dft import process_pdf, batch_process

# 示例1: 处理单个PDF文件
print("=" * 60)
print("示例1: 处理单个PDF文件")
print("=" * 60)

result = process_pdf(
    pdf_path="41557_2026_2096_MOESM1_ESM.pdf",
    output_dir="./output/paper1",
    cpu=64,
    mem="128GB",
    method="B3PW91/def2TZVP em=d3bj",
    solvent="SMD(toluene)"
)

if result["success"]:
    print(f"✓ 成功提取 {result['molecule_count']} 个分子")
    print(f"  输出目录: {result['output_dir']}")
else:
    print(f"✗ 失败: {result.get('error')}")


# 示例2: 批量处理多个PDF文件
print("\n" + "=" * 60)
print("示例2: 批量处理目录中的所有PDF")
print("=" * 60)

results = batch_process(
    pdf_dir="./pdfs/",
    output_base_dir="./output",
    cpu=64,
    mem="128GB",
    method="B3PW91/def2TZVP em=d3bj"
)

print(f"\n处理完成，共 {len(results)} 个文件")
