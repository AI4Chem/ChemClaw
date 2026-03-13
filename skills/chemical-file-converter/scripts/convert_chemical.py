#!/usr/bin/env python3
"""
Chemical File Converter

化学文件格式转换工具
支持 .xyz, .gjf, .mol, .sdf, .pdb, .mol2 等格式互转
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple

# 全局变量，延迟导入
rdkit_available = False
openbabel_available = False
ase_available = False

def check_dependencies():
    """检查可用的依赖库"""
    global rdkit_available, openbabel_available, ase_available
    
    try:
        from rdkit import Chem
        rdkit_available = True
    except ImportError:
        rdkit_available = False
    
    try:
        # 检查 Open Babel
        import subprocess
        result = subprocess.run(['obabel', '-V'], capture_output=True, text=True)
        openbabel_available = (result.returncode == 0)
    except:
        openbabel_available = False
    
    try:
        import ase
        ase_available = True
    except ImportError:
        ase_available = False
    
    return rdkit_available or openbabel_available

def import_dependencies():
    """导入依赖"""
    global Chem, rdMolDescriptors, Draw
    if rdkit_available:
        try:
            from rdkit import Chem
            from rdkit.Chem import rdMolDescriptors, Draw
            return True
        except Exception as e:
            print(f"RDKit 导入失败：{e}", file=sys.stderr)
            return False
    return False

check_dependencies()

# 文件格式映射
FORMAT_MAP = {
    '.xyz': 'xyz',
    '.gjf': 'gaussian',
    '.com': 'gaussian',
    '.mol': 'mdl',
    '.sdf': 'sdf',
    '.sd': 'sdf',
    '.pdb': 'pdb',
    '.mol2': 'mol2',
    '.smi': 'smiles',
    '.smiles': 'smiles',
    '.cml': 'cml',
    '.mop': 'mopac',
    '.zmt': 'mopac',
}

class ChemicalFileConverter:
    """化学文件转换器"""
    
    def __init__(self, use_openbabel: bool = False, use_rdkit: bool = False):
        self.use_openbabel = use_openbabel
        self.use_rdkit = use_rdkit
        self.mol = None  # RDKit mol object
        self.atoms = []  # 原子列表 [(element, x, y, z), ...]
        self.title = ""
        self.charge = 0
        self.multiplicity = 1
        
    def read_file(self, filepath: str) -> bool:
        """读取化学文件"""
        filepath = Path(filepath)
        if not filepath.exists():
            print(f"✗ 错误：文件不存在：{filepath}", file=sys.stderr)
            return False
        
        ext = filepath.suffix.lower()
        format_name = FORMAT_MAP.get(ext, ext[1:])
        
        print(f"✓ 读取文件：{filepath} (格式：{format_name})")
        
        # 优先使用 RDKit
        if rdkit_available and not self.use_openbabel:
            try:
                if ext in ['.xyz', '.mol', '.sdf', '.pdb', '.mol2']:
                    self.mol = Chem.MolFromMolFile(str(filepath), removeHs=False)
                    if self.mol is not None:
                        # 提取 3D 坐标
                        conf = self.mol.GetConformer()
                        self.atoms = []
                        for atom in self.mol.GetAtoms():
                            idx = atom.GetIdx()
                            pos = conf.GetAtomPosition(idx)
                            self.atoms.append((atom.GetSymbol(), pos.x, pos.y, pos.z))
                        self.title = filepath.stem
                        print(f"✓ RDKit 成功读取：{len(self.atoms)} 个原子")
                        return True
            except Exception as e:
                print(f"  RDKit 读取失败：{e}", file=sys.stderr)
        
        # 尝试 Open Babel
        if openbabel_available:
            try:
                return self._read_with_openbabel(filepath)
            except Exception as e:
                print(f"  Open Babel 读取失败：{e}", file=sys.stderr)
        
        # 手动解析 XYZ 格式
        if ext == '.xyz':
            return self._read_xyz(filepath)
        
        # 手动解析 SDF/MOL 格式
        if ext in ['.sdf', '.sd', '.mol']:
            return self._read_sdf(filepath)
        
        # 手动解析 Gaussian 格式
        if ext in ['.gjf', '.com']:
            return self._read_gaussian(filepath)
        
        print(f"✗ 无法读取文件格式：{ext}", file=sys.stderr)
        return False
    
    def _read_with_openbabel(self, filepath: Path) -> bool:
        """使用 Open Babel 读取文件"""
        import subprocess
        import tempfile
        
        # 转换为 XYZ 格式作为中间格式
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as tmp:
            tmp_xyz = tmp.name
        
        try:
            cmd = ['obabel', str(filepath), '-oxyz', '-O', tmp_xyz]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return self._read_xyz(Path(tmp_xyz))
        finally:
            if os.path.exists(tmp_xyz):
                os.unlink(tmp_xyz)
        
        return False
    
    def _read_xyz(self, filepath: Path) -> bool:
        """手动解析 XYZ 文件"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        if len(lines) < 2:
            print("✗ XYZ 文件格式错误", file=sys.stderr)
            return False
        
        try:
            n_atoms = int(lines[0].strip())
        except ValueError:
            print("✗ XYZ 文件第一行必须是原子数", file=sys.stderr)
            return False
        
        self.title = lines[1].strip() if len(lines) > 1 else ""
        self.atoms = []
        
        for i, line in enumerate(lines[2:2+n_atoms], 1):
            parts = line.split()
            if len(parts) >= 4:
                element = parts[0]
                try:
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    self.atoms.append((element, x, y, z))
                except ValueError:
                    continue
        
        print(f"✓ XYZ 解析成功：{len(self.atoms)} 个原子")
        return len(self.atoms) > 0
    
    def _read_sdf(self, filepath: Path) -> bool:
        """手动解析 SDF/MOL 文件"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        self.title = lines[0].strip() if len(lines) > 0 else ""
        self.atoms = []
        
        # 查找计数块（包含原子数的行，格式：nnn  mmm ...）
        n_atoms = 0
        start_line = 0
        
        for i, line in enumerate(lines):
            if len(line) >= 6 and 'V2000' in line:
                try:
                    n_atoms = int(line[:3].strip())
                    start_line = i + 1
                    break
                except ValueError:
                    pass
        
        if n_atoms == 0:
            print("✗ 无法找到原子数", file=sys.stderr)
            return False
        
        # 解析原子块
        for i in range(start_line, min(start_line + n_atoms, len(lines))):
            line = lines[i]
            if len(line) >= 54:
                try:
                    x = float(line[:10].strip())
                    y = float(line[10:20].strip())
                    z = float(line[20:30].strip())
                    element = line[31:34].strip()
                    if element:
                        self.atoms.append((element, x, y, z))
                except ValueError:
                    pass
        
        print(f"✓ SDF 解析成功：{len(self.atoms)} 个原子")
        return len(self.atoms) > 0
    
    def _read_gaussian(self, filepath: Path) -> bool:
        """手动解析 Gaussian 输入文件"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        self.atoms = []
        in_coordinates = False
        charge_line_passed = False
        
        for line in lines:
            line = line.strip()
            
            # 跳过 Link0 命令和路由部分
            if line.startswith('%') or line.startswith('#'):
                continue
            
            # 空行可能是坐标开始的标志
            if not line:
                if charge_line_passed:
                    in_coordinates = True
                continue
            
            if in_coordinates:
                # 检查是否是电荷/多重度行
                if not charge_line_passed:
                    parts = line.split()
                    if len(parts) == 2:
                        try:
                            self.charge = int(parts[0])
                            self.multiplicity = int(parts[1])
                            charge_line_passed = True
                            continue
                        except ValueError:
                            pass
                
                # 解析原子坐标
                parts = line.split()
                if len(parts) >= 4:
                    element = parts[0]
                    # 检查是否是元素符号（不是数字）
                    if not element[0].isdigit():
                        try:
                            x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                            self.atoms.append((element, x, y, z))
                        except ValueError:
                            pass
        
        self.title = filepath.stem
        print(f"✓ Gaussian 解析成功：{len(self.atoms)} 个原子")
        return len(self.atoms) > 0
    
    def write_file(self, output_path: str, format_name: str = None,
                   method: str = 'B3LYP', basis: str = '6-31G*',
                   charge: int = 0, multiplicity: int = 1,
                   link0: str = None) -> bool:
        """写入化学文件"""
        output_path = Path(output_path)
        
        if format_name is None:
            ext = output_path.suffix.lower()
            format_name = FORMAT_MAP.get(ext, ext[1:])
        
        print(f"✓ 生成文件：{output_path} (格式：{format_name})")
        
        # 根据格式选择写入方法
        if format_name == 'xyz':
            return self._write_xyz(output_path)
        elif format_name == 'gaussian':
            return self._write_gaussian(output_path, method, basis, charge, multiplicity, link0)
        elif format_name == 'mdl':
            return self._write_mdl(output_path)
        elif format_name == 'sdf':
            return self._write_sdf(output_path)
        elif format_name == 'pdb':
            return self._write_pdb(output_path)
        elif format_name == 'mol2':
            return self._write_mol2(output_path)
        elif format_name == 'smiles':
            return self._write_smiles(output_path)
        else:
            print(f"✗ 不支持的输出格式：{format_name}", file=sys.stderr)
            return False
    
    def _write_xyz(self, output_path: Path) -> bool:
        """写入 XYZ 文件"""
        with open(output_path, 'w') as f:
            f.write(f"{len(self.atoms)}\n")
            f.write(f"{self.title}\n")
            for element, x, y, z in self.atoms:
                f.write(f"{element:2s} {x:15.8f} {y:15.8f} {z:15.8f}\n")
        return True
    
    def _write_gaussian(self, output_path: Path, method: str, basis: str,
                        charge: int, multiplicity: int, link0: str) -> bool:
        """写入 Gaussian 输入文件"""
        # 默认 Link0 命令
        if link0 is None:
            link0_lines = [
                f"%chk={output_path.stem}.chk",
                "%mem=4GB",
                "%nproc=4",
            ]
        else:
            link0_lines = [f"%{cmd.strip()}" for cmd in link0.split(',')]
        
        with open(output_path, 'w') as f:
            # Link0 命令
            for line in link0_lines:
                f.write(f"{line}\n")
            
            # 路由部分
            f.write(f"#p {method}/{basis} opt freq\n")
            f.write("\n")
            
            # 标题
            f.write(f"{self.title}\n")
            f.write("\n")
            
            # 电荷和多重度
            f.write(f"{charge} {multiplicity}\n")
            
            # 原子坐标
            for element, x, y, z in self.atoms:
                f.write(f"{element:2s} {x:15.8f} {y:15.8f} {z:15.8f}\n")
            
            f.write("\n")
        
        return True
    
    def _write_mdl(self, output_path: Path) -> bool:
        """写入 MDL Molfile 格式"""
        # 简单实现，不包含键信息
        with open(output_path, 'w') as f:
            # 标题块
            f.write(f"{self.title}\n")
            f.write("  -OpenClaw-\n")
            f.write("\n")
            
            # 计数块
            n_atoms = len(self.atoms)
            f.write(f"{n_atoms:3d}  0  0  0  0  0            999 V2000\n")
            
            # 原子块
            for element, x, y, z in self.atoms:
                f.write(f"{x:10.4f}{y:10.4f}{z:10.4f} {element:<3s} 0  0  0  0  0  0  0  0  0  0  0  0\n")
            
            # 键块（空）
            f.write("M  END\n")
        
        return True
    
    def _write_sdf(self, output_path: Path) -> bool:
        """写入 SDF 格式"""
        # SDF 与 MOL 格式类似，但支持多个分子
        return self._write_mdl(output_path)
    
    def _write_pdb(self, output_path: Path) -> bool:
        """写入 PDB 格式"""
        with open(output_path, 'w') as f:
            f.write(f"HEADER    {self.title[:40]:<40s}\n")
            f.write(f"TITLE     {self.title[:70]:<70s}\n")
            
            for i, (element, x, y, z) in enumerate(self.atoms, 1):
                # PDB ATOM 记录格式
                f.write(f"ATOM  {i:5d}  {element:<2s}   MOL A   1    {x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00          {element:>2s}\n")
            
            f.write("END\n")
        
        return True
    
    def _write_mol2(self, output_path: Path) -> bool:
        """写入 Mol2 格式"""
        with open(output_path, 'w') as f:
            f.write("@<TRIPOS>MOLECULE\n")
            f.write(f"{self.title}\n")
            f.write(f"{len(self.atoms):6d}    0    0     0     0\n")
            f.write("SMALL\n")
            f.write("NO_CHARGES\n")
            f.write("\n")
            
            f.write("@<TRIPOS>ATOM\n")
            for i, (element, x, y, z) in enumerate(self.atoms, 1):
                f.write(f"{i:7d} {element:<3s} {x:10.4f} {y:10.4f} {z:10.4f} {element}\n")
            
            f.write("@<TRIPOS>BOND\n")
            # 键信息（空）
        
        return True
    
    def _write_smiles(self, output_path: Path) -> bool:
        """写入 SMILES 格式"""
        # 如果没有 RDKit，只能输出占位符
        if rdkit_available and self.mol:
            smiles = Chem.MolToSmiles(self.mol)
            with open(output_path, 'w') as f:
                f.write(f"{smiles}  {self.title}\n")
            return True
        else:
            print("⚠ 警告：没有 RDKit，无法生成准确的 SMILES", file=sys.stderr)
            with open(output_path, 'w') as f:
                f.write(f"# 需要 RDKit 生成 SMILES\n")
            return False


def batch_convert(input_pattern: str, output_dir: str, format_name: str,
                  method: str, basis: str, charge: int, multiplicity: int,
                  link0: str, use_openbabel: bool) -> Tuple[int, int]:
    """批量转换文件"""
    import glob
    
    input_files = glob.glob(input_pattern)
    if not input_files:
        print(f"✗ 未找到匹配的文件：{input_pattern}", file=sys.stderr)
        return 0, 0
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    success = 0
    failed = 0
    
    for input_file in input_files:
        try:
            converter = ChemicalFileConverter(use_openbabel=use_openbabel)
            if not converter.read_file(input_file):
                failed += 1
                continue
            
            input_path = Path(input_file)
            output_file = output_dir / f"{input_path.stem}{format_name}"
            
            if converter.write_file(output_file, method=method, basis=basis,
                                   charge=charge, multiplicity=multiplicity, link0=link0):
                print(f"✓ 已转换：{input_file} → {output_file}")
                success += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ 转换失败 {input_file}: {e}", file=sys.stderr)
            failed += 1
    
    return success, failed


def main():
    parser = argparse.ArgumentParser(
        description='化学文件格式转换工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s input.xyz -o output.gjf
  %(prog)s molecule.mol --format sdf
  %(prog)s *.xyz --output-dir ./converted
  %(prog)s input.xyz -o gaussian.gjf --method B3LYP --basis 6-31G*
        """
    )
    
    parser.add_argument('input', nargs='?', help='输入文件路径')
    parser.add_argument('--input', '-i', dest='input_opt', help='输入文件路径（替代位置参数）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--format', '-f', dest='format', help='输出格式 (xyz/sdf/mol2/pdb/gjf 等)')
    parser.add_argument('--output-dir', '-d', dest='output_dir', help='输出目录（批量模式）')
    
    # Gaussian 参数
    parser.add_argument('--method', '-m', default='B3LYP', help='Gaussian 计算方法 (默认：B3LYP)')
    parser.add_argument('--basis', '-b', default='6-31G*', help='Gaussian 基组 (默认：6-31G*)')
    parser.add_argument('--charge', type=int, default=0, help='分子电荷 (默认：0)')
    parser.add_argument('--multiplicity', type=int, default=1, help='自旋多重度 (默认：1)')
    parser.add_argument('--link0', help='Gaussian Link0 命令 (如 "%%mem=4GB,%%nproc=4")')
    
    # 引擎选择
    parser.add_argument('--use-openbabel', action='store_true', help='强制使用 Open Babel')
    parser.add_argument('--use-rdkit', action='store_true', help='强制使用 RDKit')
    
    args = parser.parse_args()
    
    # 确定输入文件
    input_file = args.input or args.input_opt
    if not input_file:
        parser.print_help()
        sys.exit(1)
    
    # 检查依赖
    if not check_dependencies():
        print("✗ 错误：未找到可用的化学处理库", file=sys.stderr)
        print("  请安装 RDKit 或 Open Babel:", file=sys.stderr)
        print("    pip install rdkit", file=sys.stderr)
        print("    或 conda install -c conda-forge openbabel", file=sys.stderr)
        sys.exit(1)
    
    # 批量转换模式
    if args.output_dir:
        if '*' in input_file:
            # 通配符模式
            format_ext = '.' + args.format if args.format else '.xyz'
            success, failed = batch_convert(
                input_file, args.output_dir, format_ext,
                args.method, args.basis, args.charge, args.multiplicity,
                args.link0, args.use_openbabel
            )
            print(f"\n完成：{success} 成功，{failed} 失败")
            sys.exit(0 if failed == 0 else 1)
        else:
            # 单文件，输出到目录
            converter = ChemicalFileConverter(
                use_openbabel=args.use_openbabel,
                use_rdkit=args.use_rdkit
            )
            if not converter.read_file(input_file):
                sys.exit(1)
            
            output_dir = Path(args.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            format_ext = '.' + args.format if args.format else '.xyz'
            output_file = output_dir / f"{Path(input_file).stem}{format_ext}"
            
            if converter.write_file(output_file, method=args.method, basis=args.basis,
                                   charge=args.charge, multiplicity=args.multiplicity,
                                   link0=args.link0):
                print(f"✓ 已生成：{output_file}")
                sys.exit(0)
            else:
                sys.exit(1)
    
    # 单文件转换模式
    converter = ChemicalFileConverter(
        use_openbabel=args.use_openbabel,
        use_rdkit=args.use_rdkit
    )
    
    if not converter.read_file(input_file):
        sys.exit(1)
    
    output_file = args.output
    if not output_file:
        # 自动生成输出文件名
        input_path = Path(input_file)
        format_ext = '.' + args.format if args.format else '.xyz'
        output_file = input_path.parent / f"{input_path.stem}_converted{format_ext}"
    
    if converter.write_file(output_file, format_name=args.format,
                           method=args.method, basis=args.basis,
                           charge=args.charge, multiplicity=args.multiplicity,
                           link0=args.link0):
        print(f"✓ 转换成功：{output_file}")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
