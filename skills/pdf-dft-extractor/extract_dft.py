#!/usr/bin/env python3
"""
PDF DFT Extractor - 从PDF中提取DFT计算坐标并生成Gaussian gjf文件

使用方法:
    python extract_dft.py <pdf_file_or_directory> [options]

示例:
    python extract_dft.py paper.pdf
    python extract_dft.py ./pdfs/ -o ./output/ --cpu 64 --mem 128GB
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Tuple, Dict, Optional

# 添加MinerU skill的路径
sys.path.insert(0, os.path.expanduser('~/.config/agents/skills/mineru-pdf-converter/scripts'))

try:
    from pdf_to_markdown import convert_large_pdf, get_api_token
except ImportError:
    print("错误: 未找到MinerU PDF Converter。请确保已安装该skill。")
    sys.exit(1)


def extract_molecules_from_markdown(md_content: str) -> List[Tuple[str, str]]:
    """
    从markdown内容中提取分子坐标
    
    Args:
        md_content: markdown文件内容
        
    Returns:
        列表，每个元素为(分子名称, 坐标文本)的元组
    """
    molecules = []
    
    # 找到计算坐标部分 (从 "Computed coordinates" 开始)
    if "Computed coordinates" in md_content:
        computed_section = md_content.split("Computed coordinates")[1]
    else:
        # 尝试其他可能的标题
        for marker in ["Coordinates", "Cartesian coordinates", "XYZ coordinates"]:
            if marker in md_content:
                computed_section = md_content.split(marker)[1]
                break
        else:
            # 如果没有找到标记，尝试在整个文档中搜索
            computed_section = md_content
    
    # 模式: 查找所有.log文件名和随后的坐标表格
    # 只允许字母、数字、下划线、连字符
    log_pattern = r'([A-Za-z0-9][\w\-]*_b3pw91|[A-Za-z0-9][\w\-]*_pbe0|[A-Za-z0-9][\w\-]*_wb97xd)\.log'
    log_matches = list(re.finditer(log_pattern, computed_section, re.IGNORECASE))
    
    for i, match in enumerate(log_matches):
        mol_name = match.group(1)
        start_pos = match.end()
        end_pos = log_matches[i+1].start() if i+1 < len(log_matches) else len(computed_section)
        section = computed_section[start_pos:end_pos]
        
        coords = []
        
        # 方法1: 从HTML表格提取
        table_pattern = r'<tr><td>([C HFKN Si O S Cl Br I]{1,2})</td><td>([-\d\.]+)</td><td>([-\d\.]+)</td><td>([-\d\.]+)</td></tr>'
        table_matches = re.findall(table_pattern, section, re.IGNORECASE)
        
        for m in table_matches:
            element, x, y, z = m
            element = element.strip()
            # 标准化元素符号
            element = element[0].upper() + element[1:].lower() if len(element) > 1 else element.upper()
            coords.append(f"{element:>2}  {float(x):16.8f}{float(y):16.8f}{float(z):16.8f}")
        
        # 方法2: 从CSV格式提取
        if not coords:
            csv_pattern = r'^([C HFKN Si O S Cl Br I]{1,2})\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)'
            csv_matches = re.findall(csv_pattern, section, re.MULTILINE | re.IGNORECASE)
            for m in csv_matches:
                element, x, y, z = m
                element = element.strip()
                element = element[0].upper() + element[1:].lower() if len(element) > 1 else element.upper()
                coords.append(f"{element:>2}  {float(x):16.8f}{float(y):16.8f}{float(z):16.8f}")
        
        # 过滤掉不合理的分子名称和坐标
        if coords and len(coords) < 10000:  # 过滤异常大的结构
            # 清理分子名称
            mol_name_clean = re.sub(r'[<>":/\\|?*\x00-\x1f]', '_', mol_name)
            # 限制文件名长度
            if len(mol_name_clean) > 100:
                mol_name_clean = mol_name_clean[:100]
            # 过滤掉包含HTML标签或明显错误的名称
            if '<' in mol_name_clean or '>' in mol_name_clean or 'td_' in mol_name_clean:
                continue
            molecules.append((mol_name_clean, '\n'.join(coords)))
    
    return molecules


def write_gjf(
    output_path: str,
    molecule_name: str, 
    coords_text: str, 
    charge: int = 0, 
    multiplicity: int = 1,
    cpu: int = 64,
    mem: str = "128GB",
    method: str = "B3PW91/def2TZVP em=d3bj",
    solvent: str = "SMD(toluene)",
    keywords: str = "opt freq"
) -> str:
    """
    写入gjf文件
    
    Args:
        output_path: 输出文件路径
        molecule_name: 分子名称
        coords_text: 坐标文本
        charge: 电荷
        multiplicity: 自旋多重度
        cpu: CPU核数
        mem: 内存
        method: 计算方法
        solvent: 溶剂模型
        keywords: 计算关键词
        
    Returns:
        生成的文件路径
    """
    # 清理文件名
    safe_name = re.sub(r'[<>":/\\|?*\x00-\x1f]', '_', molecule_name)
    
    content = f"%chk={safe_name}.chk\n"
    content += f"%mem={mem}\n"
    content += f"%nprocshared={cpu}\n"
    content += f"# {method} nosymm int=ultrafine {solvent} {keywords}\n\n"
    content += f"{molecule_name}\n\n"
    content += f"{charge} {multiplicity}\n"
    content += coords_text + "\n\n"
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    return output_path


def generate_readme(
    output_dir: str,
    pdf_name: str,
    molecules: List[Tuple[str, str]],
    cpu: int,
    mem: str,
    method: str
) -> str:
    """生成README文件"""
    readme_path = os.path.join(output_dir, "README.txt")
    
    content = f"DFT计算分子gjf文件\n"
    content += "=" * 50 + "\n\n"
    content += f"来源PDF: {pdf_name}\n\n"
    content += f"计算方法: {method}\n"
    content += f"CPU核数: {cpu}\n"
    content += f"内存: {mem}\n\n"
    content += f"共提取 {len(molecules)} 个分子结构\n\n"
    content += "文件列表:\n"
    content += "-" * 50 + "\n"
    
    for mol_name, _ in molecules:
        gjf_name = f"{mol_name}.gjf"
        content += f"  - {gjf_name}\n"
    
    with open(readme_path, 'w') as f:
        f.write(content)
    
    return readme_path


def process_pdf(
    pdf_path: str,
    output_dir: Optional[str] = None,
    cpu: int = 64,
    mem: str = "128GB",
    method: str = "B3PW91/def2TZVP em=d3bj",
    solvent: str = "SMD(toluene)",
    charge: int = 0,
    multiplicity: int = 1,
    keywords: str = "opt freq",
    keep_temp: bool = False
) -> Dict:
    """
    处理单个PDF文件
    
    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录，默认为PDF文件名
        cpu: CPU核数
        mem: 内存
        method: 计算方法
        solvent: 溶剂模型
        charge: 电荷
        multiplicity: 自旋多重度
        keywords: 计算关键词
        keep_temp: 是否保留临时文件
        
    Returns:
        处理结果字典
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        return {"success": False, "error": f"文件不存在: {pdf_path}"}
    
    # 确定输出目录
    if output_dir is None:
        output_dir = pdf_path.stem
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"\n处理: {pdf_path.name}")
    print(f"输出目录: {output_path.absolute()}")
    
    try:
        # 1. 使用MinerU转换PDF到Markdown
        print("  正在转换PDF到Markdown...")
        token = get_api_token()
        temp_output = output_path / "temp_mineru"
        
        result = convert_large_pdf(
            token=token,
            pdf_path=str(pdf_path),
            output_dir=str(temp_output),
            model_version="vlm"
        )
        
        md_file = temp_output / pdf_path.stem / "full.md"
        if not md_file.exists():
            # 尝试查找任何.md文件
            md_files = list(temp_output.rglob("*.md"))
            if md_files:
                md_file = md_files[0]
            else:
                return {"success": False, "error": "未找到转换后的markdown文件"}
        
        # 2. 读取markdown内容
        with open(md_file, 'r', encoding='utf-8') as f:
            md_content = f.read()
        
        # 3. 提取分子坐标
        print("  正在提取分子坐标...")
        molecules = extract_molecules_from_markdown(md_content)
        
        if not molecules:
            return {"success": False, "error": "未找到DFT计算坐标"}
        
        print(f"  找到 {len(molecules)} 个分子")
        
        # 4. 生成gjf文件
        print("  正在生成gjf文件...")
        generated_files = []
        
        for mol_name, coords in molecules:
            gjf_path = output_path / f"{mol_name}.gjf"
            try:
                write_gjf(
                    str(gjf_path),
                    mol_name,
                    coords,
                    charge=charge,
                    multiplicity=multiplicity,
                    cpu=cpu,
                    mem=mem,
                    method=method,
                    solvent=solvent,
                    keywords=keywords
                )
                generated_files.append(gjf_path.name)
            except Exception as e:
                print(f"    警告: 生成 {mol_name} 时出错: {e}")
        
        # 5. 生成README
        readme_path = generate_readme(
            str(output_path),
            pdf_path.name,
            molecules,
            cpu,
            mem,
            method
        )
        
        # 6. 清理临时文件
        if not keep_temp and temp_output.exists():
            import shutil
            shutil.rmtree(temp_output, ignore_errors=True)
        
        return {
            "success": True,
            "pdf": pdf_path.name,
            "output_dir": str(output_path.absolute()),
            "molecule_count": len(molecules),
            "generated_files": generated_files,
            "readme": readme_path
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


def batch_process(
    pdf_dir: str,
    output_base_dir: str = "./dft_output",
    **kwargs
) -> List[Dict]:
    """
    批量处理PDF文件
    
    Args:
        pdf_dir: PDF文件所在目录
        output_base_dir: 基础输出目录
        **kwargs: 传递给process_pdf的其他参数
        
    Returns:
        处理结果列表
    """
    pdf_dir = Path(pdf_dir)
    output_base = Path(output_base_dir)
    output_base.mkdir(parents=True, exist_ok=True)
    
    # 查找所有PDF文件
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"在 {pdf_dir} 中未找到PDF文件")
        return []
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    print("=" * 60)
    
    results = []
    for pdf_file in pdf_files:
        # 为每个PDF创建单独的输出文件夹
        pdf_output_dir = output_base / pdf_file.stem
        result = process_pdf(
            str(pdf_file),
            output_dir=str(pdf_output_dir),
            **kwargs
        )
        results.append(result)
        
        if result["success"]:
            print(f"✓ 成功: {result['molecule_count']} 个分子")
        else:
            print(f"✗ 失败: {result.get('error', '未知错误')}")
    
    # 打印总结
    print("\n" + "=" * 60)
    print("处理完成!")
    print(f"总计: {len(pdf_files)} 个PDF文件")
    print(f"成功: {sum(1 for r in results if r['success'])} 个")
    print(f"失败: {sum(1 for r in results if not r['success'])} 个")
    print(f"输出目录: {output_base.absolute()}")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="从PDF中提取DFT计算坐标并生成Gaussian gjf文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s paper.pdf
  %(prog)s ./pdfs/ -o ./output/
  %(prog)s paper.pdf --cpu 64 --mem 128GB --method "B3LYP/6-31G(d)"
        """
    )
    
    parser.add_argument("input", help="PDF文件或包含PDF文件的目录")
    parser.add_argument("-o", "--output", default="./dft_output", 
                       help="输出目录 (默认: ./dft_output)")
    parser.add_argument("--cpu", type=int, default=64,
                       help="CPU核数 (默认: 64)")
    parser.add_argument("--mem", default="128GB",
                       help="内存 (默认: 128GB)")
    parser.add_argument("--method", default="B3PW91/def2TZVP em=d3bj",
                       help="计算方法 (默认: B3PW91/def2TZVP em=d3bj)")
    parser.add_argument("--solvent", default="SMD(toluene)",
                       help="溶剂模型 (默认: SMD(toluene))")
    parser.add_argument("--charge", type=int, default=0,
                       help="电荷 (默认: 0)")
    parser.add_argument("--multiplicity", type=int, default=1,
                       help="自旋多重度 (默认: 1)")
    parser.add_argument("--keywords", default="opt freq",
                       help="计算关键词 (默认: 'opt freq')")
    parser.add_argument("--keep-temp", action="store_true",
                       help="保留临时文件")
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    # 设置处理参数
    process_kwargs = {
        "cpu": args.cpu,
        "mem": args.mem,
        "method": args.method,
        "solvent": args.solvent,
        "charge": args.charge,
        "multiplicity": args.multiplicity,
        "keywords": args.keywords,
        "keep_temp": args.keep_temp
    }
    
    if input_path.is_dir():
        # 批量处理
        batch_process(
            str(input_path),
            output_base_dir=args.output,
            **process_kwargs
        )
    else:
        # 单个文件处理
        result = process_pdf(
            str(input_path),
            output_dir=args.output,
            **process_kwargs
        )
        
        if result["success"]:
            print(f"\n处理成功!")
            print(f"  PDF: {result['pdf']}")
            print(f"  输出: {result['output_dir']}")
            print(f"  分子数: {result['molecule_count']}")
            print(f"  文件列表: {result['generated_files']}")
        else:
            print(f"\n处理失败: {result.get('error', '未知错误')}")
            sys.exit(1)


if __name__ == "__main__":
    main()
