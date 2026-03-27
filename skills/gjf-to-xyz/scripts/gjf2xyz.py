#!/usr/bin/env python3
"""
gjf2xyz - 将Gaussian gjf文件转换为XYZ格式

Usage:
    python gjf2xyz.py input.gjf
    python gjf2xyz.py input.gjf -o output.xyz
    python gjf2xyz.py ./gjf_directory/ -o ./xyz_directory/
"""

import argparse
import os
import re
import sys
from pathlib import Path


def parse_gjf(content: str) -> tuple[list[tuple[str, float, float, float]], str | None]:
    """
    解析gjf文件内容，提取原子坐标
    
    Returns:
        (atoms, title): atoms是(元素符号, x, y, z)的列表，title是分子标题
    """
    lines = content.strip().split('\n')
    
    # 找到电荷和多重度行（格式：整数 整数）
    charge_multiplicity_idx = -1
    for i, line in enumerate(lines):
        stripped = line.strip()
        # 匹配电荷和多重度行（如 "0 1"）
        if re.match(r'^-?\d+\s+\d+$', stripped):
            charge_multiplicity_idx = i
            break
    
    if charge_multiplicity_idx == -1:
        raise ValueError("未找到电荷和多重度行")
    
    # 坐标从电荷多重度行的下一行开始
    coord_start = charge_multiplicity_idx + 1
    
    atoms = []
    title = None
    
    # 尝试获取标题（电荷多重度行前面非空的行）
    for i in range(charge_multiplicity_idx - 1, -1, -1):
        line = lines[i].strip()
        if line and not line.startswith('#') and not line.startswith('%'):
            title = line
            break
    
    # 解析坐标
    for i in range(coord_start, len(lines)):
        line = lines[i].strip()
        
        # 空行表示坐标结束
        if not line:
            break
        
        # 跳过连接性信息（纯数字开头）
        if re.match(r'^\d+(\s+\d+\s+\d+\.\d+)*$', line):
            continue
        
        # 解析坐标行
        # 格式: 元素符号  x  y  z
        parts = line.split()
        if len(parts) >= 4:
            element = parts[0]
            try:
                x = float(parts[1])
                y = float(parts[2])
                z = float(parts[3])
                atoms.append((element, x, y, z))
            except ValueError:
                # 可能是其他格式的行，跳过
                continue
    
    return atoms, title


def write_xyz(atoms: list[tuple[str, float, float, float]], 
              output_path: str, 
              title: str | None = None) -> None:
    """
    将原子坐标写入xyz文件
    
    Args:
        atoms: (元素符号, x, y, z)的列表
        output_path: 输出文件路径
        title: 分子标题
    """
    if not title:
        title = "Generated from gjf2xyz"
    
    with open(output_path, 'w') as f:
        f.write(f"{len(atoms)}\n")
        f.write(f"{title}\n")
        for element, x, y, z in atoms:
            f.write(f"{element:>2}  {x:14.8f}  {y:14.8f}  {z:14.8f}\n")


def convert_gjf_to_xyz(input_path: str, output_path: str | None = None) -> str:
    """
    将单个gjf文件转换为xyz文件
    
    Args:
        input_path: gjf文件路径
        output_path: xyz文件路径，如果为None则自动生成
        
    Returns:
        输出文件路径
    """
    # 读取gjf文件
    with open(input_path, 'r') as f:
        content = f.read()
    
    # 解析坐标
    atoms, title = parse_gjf(content)
    
    if not atoms:
        raise ValueError(f"未在文件中找到原子坐标: {input_path}")
    
    # 确定输出路径
    if output_path is None:
        base_name = Path(input_path).stem
        output_path = str(Path(input_path).parent / f"{base_name}.xyz")
    
    # 写入xyz文件
    write_xyz(atoms, output_path, title)
    
    return output_path


def batch_convert(input_dir: str, output_dir: str | None = None) -> list[str]:
    """
    批量转换目录中的所有gjf文件
    
    Args:
        input_dir: 输入目录路径
        output_dir: 输出目录路径，如果为None则使用输入目录
        
    Returns:
        成功转换的文件列表
    """
    input_path = Path(input_dir)
    
    if output_dir is None:
        output_path = input_path
    else:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    # 查找所有gjf文件
    gjf_files = list(input_path.glob("*.gjf"))
    
    if not gjf_files:
        print(f"在 {input_dir} 中未找到.gjf文件")
        return []
    
    converted = []
    errors = []
    
    for gjf_file in sorted(gjf_files):
        try:
            output_file = output_path / f"{gjf_file.stem}.xyz"
            convert_gjf_to_xyz(str(gjf_file), str(output_file))
            converted.append(str(output_file))
            print(f"OK {gjf_file.name} -> {output_file.name}")
        except Exception as e:
            errors.append((gjf_file.name, str(e)))
            print(f"ERR {gjf_file.name}: {e}")
    
    # 打印统计
    print(f"\n转换完成: {len(converted)}/{len(gjf_files)} 成功")
    if errors:
        print(f"失败: {len(errors)}")
        for name, error in errors:
            print(f"  - {name}: {error}")
    
    return converted


def main():
    parser = argparse.ArgumentParser(
        description="将Gaussian gjf文件转换为XYZ格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python gjf2xyz.py molecule.gjf
  python gjf2xyz.py molecule.gjf -o output.xyz
  python gjf2xyz.py ./gjf_files/ -o ./xyz_files/
        """
    )
    
    parser.add_argument(
        "input",
        help="输入gjf文件或目录"
    )
    parser.add_argument(
        "-o", "--output",
        help="输出xyz文件或目录（可选，默认与输入同名）"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if not input_path.exists():
        print(f"错误: 文件或目录不存在: {args.input}")
        sys.exit(1)
    
    if input_path.is_dir():
        # 批量转换
        batch_convert(str(input_path), args.output)
    else:
        # 单文件转换
        try:
            output_file = convert_gjf_to_xyz(str(input_path), args.output)
            print(f"转换成功: {output_file}")
            # 显示原子数
            with open(output_file, 'r') as f:
                atom_count = int(f.readline().strip())
            print(f"原子数: {atom_count}")
        except Exception as e:
            print(f"转换失败: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
