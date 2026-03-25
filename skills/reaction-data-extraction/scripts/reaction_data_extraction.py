#!/usr/bin/env python3
"""
Reaction Data Extraction Script using MinerU + NLP
从化学文献 PDF 中提取化学反应数据
"""

import argparse
import json
import os
import re
import subprocess
import sys
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def run_mineru(input_pdf: str, output_dir: str, method: str = "auto", 
               lang: str = "en", device: str = "cpu") -> dict:
    """
    运行 MinerU 进行 PDF 转换
    
    Args:
        input_pdf: 输入 PDF 文件路径
        output_dir: 输出目录
        method: 解析方法 (auto/txt/ocr)
        lang: OCR 语言
        device: 设备 (cpu/cuda)
    
    Returns:
        转换结果信息
    """
    input_path = Path(input_pdf).resolve()
    output_path = Path(output_dir).resolve()
    
    # 创建输出目录
    output_path.mkdir(parents=True, exist_ok=True)
    
    # 构建命令
    cmd = [
        "mineru",
        "-p", str(input_path),
        "-o", str(output_path),
        "-m", method,
        "-l", lang,
        "--backend", "pipeline",
        "-d", device
    ]
    
    print(f"  [1/3] 解析 PDF...")
    print(f"    命令：{' '.join(cmd)}")
    
    # 运行 MinerU
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 分钟超时
        )
        
        if result.returncode != 0:
            print(f"    ✗ MinerU 执行失败：{result.stderr}")
            return {"success": False, "error": result.stderr}
            
    except subprocess.TimeoutExpired:
        print("    ✗ 处理超时（超过 10 分钟）")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"    ✗ 执行错误：{e}")
        return {"success": False, "error": str(e)}
    
    # 查找输出文件
    pdf_name = input_path.stem
    txt_dir = output_path / pdf_name / "txt"
    
    if not txt_dir.exists():
        txt_dir = output_path
    
    # 查找 markdown 文件
    md_files = list(txt_dir.glob("*.md"))
    if not md_files:
        print("    ✗ 未找到生成的 Markdown 文件")
        return {"success": False, "error": "No markdown file found"}
    
    md_file = md_files[0]
    
    # 读取 Markdown 内容
    with open(md_file, 'r', encoding='utf-8') as f:
        text_content = f.read()
    
    # 查找表格
    tables = []
    table_pattern = r'\|.*?\|.*?\|.*?\n\|[-\| ]+\|\n((?:\|.*?\|\n)+)'
    for match in re.finditer(table_pattern, text_content, re.MULTILINE):
        tables.append(match.group(0))
    
    print(f"    ✓ PDF 解析完成，文本长度：{len(text_content)} 字符")
    print(f"    检测到表格：{len(tables)} 个")
    
    return {
        "success": True,
        "markdown_file": str(md_file),
        "text_content": text_content,
        "tables": tables,
        "images_dir": str(txt_dir / "images") if (txt_dir / "images").exists() else None
    }


def parse_reaction_table(table_text: str, entry_num: int = 0) -> List[Dict[str, Any]]:
    """
    解析反应条件表格
    
    Args:
        table_text: Markdown 格式的表格文本
        entry_num: 表格编号
    
    Returns:
        反应数据列表
    """
    reactions = []
    lines = table_text.strip().split('\n')
    
    if len(lines) < 3:
        return reactions
    
    # 解析表头
    headers = [h.strip() for h in lines[0].split('|') if h.strip()]
    
    # 解析数据行
    for line in lines[2:]:  # 跳过表头和分隔线
        if not line.strip():
            continue
        
        values = [v.strip() for v in line.split('|') if v.strip()]
        
        if len(values) != len(headers):
            continue
        
        # 构建反应数据
        reaction = {}
        for header, value in zip(headers, values):
            header_lower = header.lower()
            
            # 映射列名
            if 'entry' in header_lower or 'no' in header_lower:
                reaction['entry'] = value
            elif 'yield' in header_lower:
                # 提取产率数值
                yield_match = re.search(r'(\d+)', value)
                if yield_match:
                    reaction['yield_value'] = int(yield_match.group(1))
                reaction['yield_raw'] = value
            elif 'ee' in header_lower or 'e.e.' in header_lower or 'enantio' in header_lower:
                reaction['ee_value'] = value
            elif 'catalyst' in header_lower or 'cat' in header_lower:
                reaction['catalyst'] = value
            elif 'ligand' in header_lower:
                reaction['ligand'] = value
            elif 'solvent' in header_lower or 'solv' in header_lower:
                reaction['solvent'] = value
            elif 'temp' in header_lower:
                reaction['temperature'] = value
            elif 'time' in header_lower:
                reaction['time'] = value
            elif 'oxidant' in header_lower or 'additive' in header_lower:
                reaction['oxidant'] = value
            else:
                reaction[header] = value
        
        if reaction:
            reactions.append(reaction)
    
    return reactions


def extract_reactions_from_text(text: str) -> List[Dict[str, Any]]:
    """
    从文本中提取反应数据
    
    Args:
        text: Markdown 文本
    
    Returns:
        反应数据列表
    """
    reactions = []
    
    # 反应条件模式
    patterns = {
        'temperature': r'(\d+\s*°C|rt|reflux|room temperature|ambient)',
        'time': r'(\d+\s*(h|hr|hour|min|minute)s?)',
        'yield': r'(\d+\s*%|yield.*?(\d+\s*%))',
        'catalyst': r'(Pd\([^)]+\)|Ni\([^)]+\)|Cu\([^)]+\)|Pd₂\(dba\)₃|Pd\(OAc\)₂)',
        'ligand': r'(L\d+|PPh3|dppf|BINAP|XPhos|SPhos)',
        'oxidant': r'(DTBQ|DMBQ|DQ|TBHP|BQ|DDQ)',
        'solvent': r'(MeOH|EtOH|DMF|DMSO|THF|Toluene|acetone|DCM|CH3CN)',
    }
    
    # 按段落分割
    paragraphs = text.split('\n\n')
    
    for i, para in enumerate(paragraphs):
        if len(para) < 50:  # 跳过太短的段落
            continue
        
        # 检查是否包含反应相关关键词
        if not any(kw in para.lower() for kw in ['reaction', 'yield', 'catalyst', 'condition', 'optimized']):
            continue
        
        reaction = {
            'reaction_id': f'RXN_TEXT_{i:03d}',
            'source': 'text',
            'confidence': 0.5,  # 文本提取的置信度较低
            'raw_text': para[:200]  # 只保留前 200 字符
        }
        
        # 提取条件
        for key, pattern in patterns.items():
            match = re.search(pattern, para, re.IGNORECASE)
            if match:
                reaction[key] = match.group(1)
        
        # 只保留提取到至少一个条件的反应
        extracted_keys = [k for k in patterns.keys() if k in reaction]
        if len(extracted_keys) >= 2:
            reactions.append(reaction)
    
    return reactions


def save_reactions(reactions: List[Dict], output_dir: Path, output_format: str = 'csv'):
    """
    保存反应数据
    
    Args:
        reactions: 反应数据列表
        output_dir: 输出目录
        output_format: 输出格式 (csv/json)
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if output_format == 'csv':
        csv_file = output_dir / 'reaction_data.csv'
        
        if not reactions:
            print("  ⚠️  无反应数据可保存")
            return
        
        # 收集所有字段
        all_fields = set()
        for rxn in reactions:
            all_fields.update(rxn.keys())
        
        fieldnames = sorted(list(all_fields))
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for rxn in reactions:
                # 处理列表字段
                row = {}
                for k, v in rxn.items():
                    if isinstance(v, list):
                        row[k] = '; '.join(str(x) for x in v)
                    else:
                        row[k] = v
                writer.writerow(row)
        
        print(f"  ✓ CSV 已保存：{csv_file}")
    
    elif output_format == 'json':
        json_file = output_dir / 'reaction_data.json'
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'extraction_date': datetime.now().isoformat(),
                'total_reactions': len(reactions),
                'reactions': reactions
            }, f, indent=2, ensure_ascii=False)
        
        print(f"  ✓ JSON 已保存：{json_file}")


def main():
    parser = argparse.ArgumentParser(
        description='从化学文献 PDF 中提取反应数据',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s -i paper.pdf -o ./output
  %(prog)s -i paper.pdf -o ./output --tables-only
  %(prog)s -i paper.pdf -o ./output --text-only
  %(prog)s -i ./papers/ -o ./output --batch
        """
    )
    
    parser.add_argument('-i', '--input', type=str, required=True,
                       help='输入 PDF 文件或目录')
    parser.add_argument('-o', '--output', type=str, 
                       default='~/.openclaw/media/reaction-data-extraction',
                       help='输出目录')
    parser.add_argument('--tables-only', action='store_true',
                       help='只提取表格数据')
    parser.add_argument('--text-only', action='store_true',
                       help='只提取体内容反应')
    parser.add_argument('--output-format', type=str, default='csv',
                       choices=['csv', 'json'],
                       help='输出格式')
    parser.add_argument('--method', type=str, default='auto',
                       choices=['auto', 'txt', 'ocr'],
                       help='MinerU 解析方法')
    parser.add_argument('--lang', type=str, default='en',
                       help='OCR 语言')
    parser.add_argument('--device', type=str, default='cpu',
                       choices=['cpu', 'cuda'],
                       help='计算设备')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='详细输出')
    parser.add_argument('--batch', action='store_true',
                       help='批量处理模式')
    
    args = parser.parse_args()
    
    # 输出目录
    output_base = Path(args.output).expanduser()
    
    # 输入文件
    input_path = Path(args.input).expanduser()
    
    if input_path.is_dir():
        # 批量处理
        pdf_files = list(input_path.glob('*.pdf'))
        print(f"✓ 批量处理模式：发现 {len(pdf_files)} 个 PDF 文件")
        
        for pdf_file in pdf_files:
            print(f"\n处理：{pdf_file.name}")
            output_dir = output_base / pdf_file.stem
            process_single_pdf(str(pdf_file), str(output_dir), args)
    
    elif input_path.is_file():
        # 单个文件
        output_dir = output_base / input_path.stem
        process_single_pdf(str(input_path), str(output_dir), args)
    
    else:
        print(f"✗ 输入文件不存在：{input_path}")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✅ 全部完成！")
    print(f"   输出目录：{output_base}")


def process_single_pdf(input_pdf: str, output_dir: str, args):
    """处理单个 PDF 文件"""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ 输出目录：{output_path}")
    print(f"  提取模式：{'tables' if args.tables_only else 'text' if args.text_only else 'all'}")
    print(f"  输出格式：{args.output_format}")
    
    all_reactions = []
    
    # 1. PDF 解析
    mineru_result = run_mineru(
        input_pdf, 
        output_dir,
        method=args.method,
        lang=args.lang,
        device=args.device
    )
    
    if not mineru_result.get('success'):
        print(f"  ✗ PDF 解析失败：{mineru_result.get('error')}")
        return
    
    text_content = mineru_result.get('text_content', '')
    tables = mineru_result.get('tables', [])
    
    # 2. 表格数据提取
    if not args.text_only and tables:
        print(f"  [2/3] 从表格提取反应数据...")
        for i, table in enumerate(tables):
            table_reactions = parse_reaction_table(table, i)
            for rxn in table_reactions:
                rxn['source'] = f'table_{i}'
                rxn['confidence'] = 0.9  # 表格数据置信度高
            all_reactions.extend(table_reactions)
        print(f"    提取表格反应：{len([r for r in all_reactions if 'table' in r.get('source', '')])}")
    
    # 3. 文本数据提取
    if not args.tables_only and text_content:
        print(f"  [3/3] 从文本提取反应数据...")
        text_reactions = extract_reactions_from_text(text_content)
        all_reactions.extend(text_reactions)
        print(f"    从文本提取：{len(text_reactions)} 个反应")
    
    # 4. 保存结果
    print(f"\n✓ 已处理：{Path(input_pdf).name}")
    print(f"  提取反应数：{len(all_reactions)}")
    
    save_reactions(all_reactions, output_path, args.output_format)
    
    # 5. 生成日志
    log_file = output_path / 'extraction_log.txt'
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("Extraction Log\n")
        f.write("="*60 + "\n")
        f.write(f"Source: {input_pdf}\n")
        f.write(f"Date: {datetime.now().isoformat()}\n")
        f.write(f"Total reactions: {len(all_reactions)}\n\n")
        f.write("Output files:\n")
        f.write(f"  - reaction_data.{args.output_format}\n")
    
    print(f"  ✓ 日志已保存：{log_file}")


if __name__ == '__main__':
    main()
