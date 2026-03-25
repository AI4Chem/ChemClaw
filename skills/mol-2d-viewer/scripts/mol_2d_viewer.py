#!/usr/bin/env python3
"""
Molecular Structure Visualizer

将 SMILES 字符串或化学名称转换为分子结构图
支持聚合物 2D 结构绘制
使用 RDKit 生成图片
"""

import argparse
import json
import sys
import base64
import io
import re
from pathlib import Path
from typing import Optional, List, Dict, Any

def import_dependencies():
    global Chem, Draw, rdMolDescriptors
    try:
        from rdkit import Chem
        from rdkit.Chem import Draw, rdMolDescriptors
    except ImportError:
        print("错误：请安装 rdkit: pip install rdkit", file=sys.stderr)
        sys.exit(1)

import_dependencies()


class PolymerHandler:
    """聚合物 SMILES 处理器"""
    
    def __init__(self):
        pass
    
    def is_polymer_smiles(self, smiles: str) -> bool:
        """检查 SMILES 是否为聚合物"""
        # 聚合物标记：* (连接点), [n], 重复单元
        polymer_markers = ['*', '[n]', '[[', ']]']
        return any(marker in smiles for marker in polymer_markers)
    
    def parse_polymer_smiles(self, smiles: str) -> Dict[str, Any]:
        """
        解析聚合物 SMILES，提取重复单元
        
        Args:
            smiles: 聚合物 SMILES
        
        Returns:
            解析结果
        """
        result = {
            'is_polymer': True,
            'original_smiles': smiles,
            'repeat_unit': None,
            'linkers': [],
        }
        
        # 尝试提取重复单元
        # 格式：*monomer* 或 *[linker]monomer*
        match = re.search(r'\*(.+?)\*', smiles)
        if match:
            result['repeat_unit'] = match.group(1)
        
        return result
    
    def create_polymer_mol(self, smiles: str) -> Optional[Any]:
        """
        从聚合物 SMILES 创建 RDKit Mol 对象
        
        Args:
            smiles: 聚合物 SMILES
        
        Returns:
            RDKit Mol 对象或 None
        """
        try:
            # 清理聚合物标记，创建可渲染的结构
            clean_smiles = self._clean_polymer_smiles(smiles)
            
            if clean_smiles:
                mol = Chem.MolFromSmiles(clean_smiles)
                if mol:
                    return mol
            
            # 如果清理后仍失败，尝试原始 SMILES
            return Chem.MolFromSmiles(smiles)
        except Exception:
            return None
    
    def _clean_polymer_smiles(self, smiles: str) -> Optional[str]:
        """
        清理聚合物 SMILES 以便渲染
        支持 OPSIN 格式：O(C(C[*:2])C)[*:1]
        
        Args:
            smiles: 聚合物 SMILES
        
        Returns:
            清理后的 SMILES
        """
        import re
        
        # 移除连接点标记 [*:1], [*:2], * 等
        clean = re.sub(r'\[\*:\d+\]', '', smiles)  # 移除 [*:1], [*:2] 等
        clean = clean.replace('*', '')  # 移除剩余的 *
        
        # 移除重复计数 [n]
        clean = re.sub(r'\[n\]', '', clean)
        
        # 移除聚合物括号 [[ ]]
        clean = clean.replace('[[', '').replace(']]', '')
        
        # 如果清理后是有效的 SMILES，返回
        if clean and len(clean) > 1:
            return clean
        
        return None


class MolVisualizer:
    """分子结构可视化器"""
    
    def __init__(self, width: int = 400, height: int = 300, kekulize: bool = False):
        self.width = width
        self.height = height
        self.kekulize = kekulize
        self.polymer_handler = PolymerHandler()
    
    def smiles_to_mol(self, smiles: str) -> Optional[Any]:
        """
        SMILES 转 RDKit Mol 对象
        支持聚合物 SMILES
        
        Args:
            smiles: SMILES 字符串
        
        Returns:
            RDKit Mol 对象或 None
        """
        try:
            # 检查是否为聚合物
            if self.polymer_handler.is_polymer_smiles(smiles):
                mol = self.polymer_handler.create_polymer_mol(smiles)
                if mol:
                    return mol
            
            # 普通分子
            mol = Chem.MolFromSmiles(smiles)
            if mol and self.kekulize:
                Chem.Kekulize(mol)
            return mol
        except Exception:
            return None
    
    def name_to_smiles(self, name: str) -> Optional[str]:
        """
        IUPAC 名称转 SMILES（使用 OPSIN API）
        
        Args:
            name: IUPAC 名称
        
        Returns:
            SMILES 字符串或 None
        """
        try:
            import requests
            # OPSIN API (剑桥大学，重定向到 EBI)
            url = f"https://opsin.ch.cam.ac.uk/opsin/{requests.utils.quote(name)}"
            response = requests.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            
            data = response.json()
            if isinstance(data, dict) and data.get("smiles"):
                return data["smiles"]
            elif isinstance(data, dict) and data.get("status") == "SUCCESS":
                # 从 CML 提取 SMILES
                import re
                match = re.search(r'<smiles[^>]*>([^<]+)</smiles>', data.get("cml", ""))
                if match:
                    return match.group(1)
            return None
        except Exception as e:
            import sys
            print(f"DEBUG name_to_smiles error: {e}", file=sys.stderr)
            return None
    
    def visualize(self, smiles: str, output_file: Optional[str] = None, 
                  format: str = 'png', to_stdout: bool = False,
                  title: Optional[str] = None) -> Dict[str, Any]:
        """
        可视化分子结构
        支持普通分子和聚合物
        
        Args:
            smiles: SMILES 字符串
            output_file: 输出文件路径（可选）
            format: 输出格式（png/svg）
            to_stdout: 是否输出 base64 到 stdout
            title: 图片标题
        
        Returns:
            生成结果
        """
        mol = self.smiles_to_mol(smiles)
        
        if mol is None:
            return {
                "smiles": smiles,
                "status": "error",
                "error": "Invalid SMILES",
                "message": f"无法解析 SMILES: {smiles}"
            }
        
        # 检查是否为聚合物
        is_polymer = self.polymer_handler.is_polymer_smiles(smiles)
        
        try:
            # 准备渲染选项
            draw_options = {
                'size': (self.width, self.height),
                'kekulize': self.kekulize,
            }
            
            if format.lower() == 'svg':
                # SVG 格式
                if is_polymer:
                    # 聚合物添加标题
                    svg_data = Draw.MolToSVG(mol, title=title or "Polymer Structure")
                else:
                    svg_data = Draw.MolToSVG(mol)
                
                if to_stdout:
                    svg_base64 = base64.b64encode(svg_data.encode('utf-8')).decode('utf-8')
                    return {
                        "smiles": smiles,
                        "status": "success",
                        "format": "svg",
                        "base64": svg_base64,
                        "mime_type": "image/svg+xml",
                        "is_polymer": is_polymer
                    }
                elif output_file:
                    Path(output_file).write_text(svg_data, encoding='utf-8')
            else:
                # PNG 格式
                if is_polymer:
                    # 聚合物使用特殊渲染
                    img = self._render_polymer_png(mol, smiles, title)
                else:
                    img = Draw.MolToImage(mol, **draw_options)
                
                if to_stdout:
                    img_bytes = io.BytesIO()
                    img.save(img_bytes, format='PNG')
                    img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')
                    return {
                        "smiles": smiles,
                        "status": "success",
                        "format": "png",
                        "base64": img_base64,
                        "mime_type": "image/png",
                        "size": f"{self.width}x{self.height}",
                        "is_polymer": is_polymer
                    }
                elif output_file:
                    output_path = Path(output_file)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    img.save(output_file)
            
            return {
                "smiles": smiles,
                "status": "success",
                "output_file": str(output_file) if output_file else None,
                "format": format.lower(),
                "size": f"{self.width}x{self.height}",
                "is_polymer": is_polymer
            }
            
        except Exception as e:
            return {
                "smiles": smiles,
                "status": "error",
                "error": type(e).__name__,
                "message": str(e)
            }
    
    def _render_polymer_png(self, mol: Any, smiles: str, title: Optional[str] = None) -> Any:
        """
        渲染聚合物为 PNG
        
        Args:
            mol: RDKit Mol 对象
            smiles: 原始 SMILES
            title: 标题
        
        Returns:
            PIL Image 对象
        """
        # 使用标准 RDKit 绘图
        img = Draw.MolToImage(mol, size=(self.width, self.height), kekulize=self.kekulize)
        return img
    
    def visualize_from_name(self, name: str, output_file: str, format: str = 'png') -> Dict[str, Any]:
        """
        从 IUPAC 名称可视化
        
        Args:
            name: IUPAC 名称
            output_file: 输出文件路径
            format: 输出格式
        
        Returns:
            生成结果
        """
        smiles = self.name_to_smiles(name)
        
        if smiles is None:
            return {
                "input_name": name,
                "status": "error",
                "error": "Name not found",
                "message": f"OPSIN 无法识别：{name}"
            }
        
        result = self.visualize(smiles, output_file, format, title=name)
        result["input_name"] = name
        result["smiles"] = smiles
        
        return result
    
    def batch_visualize(self, smiles_list: List[str], output_dir: str, 
                        format: str = 'png') -> Dict[str, Any]:
        """
        批量可视化
        
        Args:
            smiles_list: SMILES 列表
            output_dir: 输出目录
            format: 输出格式
        
        Returns:
            批量生成结果
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        success_count = 0
        
        for i, smiles in enumerate(smiles_list):
            smiles = smiles.strip()
            if not smiles:
                continue
            
            output_file = output_path / f"mol_{i+1}.{format.lower()}"
            result = self.visualize(smiles, str(output_file), format)
            results.append(result)
            
            if result["status"] == "success":
                success_count += 1
        
        return {
            "status": "completed",
            "total": len(smiles_list),
            "success": success_count,
            "output_dir": str(output_dir),
            "format": format,
            "results": results
        }


def main():
    import requests  # 用于 name_to_smiles
    
    parser = argparse.ArgumentParser(
        description='分子结构可视化器（支持聚合物）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 从 SMILES 生成
  %(prog)s --smiles "CCO" --output ethanol.png
  
  # 聚合物 SMILES
  %(prog)s --smiles "*OCC*" --output polymer.png
  
  # 从名称生成
  %(prog)s --name "aspirin" --output aspirin.svg
  
  # 聚合物名称
  %(prog)s --name "poly[oxy(1-methylethylene)]" --output ppo.png
  
  # 批量生成
  %(prog)s --smiles "CCO,C1=CC=CC=C1" --output-dir ./molecules
  
  # 自定义尺寸
  %(prog)s --smiles "CCO" --width 400 --height 300 --output ethanol.png
        '''
    )
    
    parser.add_argument('--smiles', '-s', help='SMILES 字符串（可多个，逗号分隔）')
    parser.add_argument('--name', '-n', help='IUPAC 名称')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--output-dir', '-d',
                        default=str(Path.home() / '.openclaw' / 'media' / 'mol-2d-viewer'),
                        help='输出目录（批量模式，默认：~/.openclaw/media/mol-2d-viewer）')
    parser.add_argument('--format', '-f', choices=['png', 'svg'], default='png',
                        help='输出格式（默认：png）')
    parser.add_argument('--width', '-W', type=int, default=400,
                        help='图片宽度（默认：400）')
    parser.add_argument('--height', '-H', type=int, default=300,
                        help='图片高度（默认：300）')
    parser.add_argument('--kekulize', '-k', action='store_true',
                        help='凯库勒化（显示双键）')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='安静模式，只输出结果')
    parser.add_argument('--stdout', action='store_true',
                        help='输出 base64 编码的图片到 stdout（不保存文件）')
    
    args = parser.parse_args()
    
    visualizer = MolVisualizer(
        width=args.width,
        height=args.height,
        kekulize=args.kekulize
    )
    
    try:
        results = None
        
        if args.smiles:
            smiles_list = [s.strip() for s in args.smiles.split(',')]
            
            if len(smiles_list) > 1:
                results = visualizer.batch_visualize(
                    smiles_list, 
                    args.output_dir,
                    args.format
                )
            else:
                if args.stdout:
                    result = visualizer.visualize(smiles_list[0], None, args.format, to_stdout=True)
                else:
                    if not args.output:
                        args.output = f"mol_{smiles_list[0]}.{args.format}"
                    result = visualizer.visualize(smiles_list[0], args.output, args.format)
                results = {"status": "success", "results": [result]}
        
        elif args.name:
            smiles = visualizer.name_to_smiles(args.name)
            if smiles is None:
                results = {"status": "error", "results": [{"input_name": args.name, "status": "error", "error": "Name not found", "message": f"OPSIN 无法识别：{args.name}"}]}
            elif args.stdout:
                result = visualizer.visualize(smiles, None, args.format, to_stdout=True, title=args.name)
                result["input_name"] = args.name
                results = {"status": "success", "results": [result]}
            else:
                if not args.output:
                    safe_name = "".join(c for c in args.name if c.isalnum() or c in '-_').strip()
                    args.output = f"{safe_name}.{args.format}"
                result = visualizer.visualize_from_name(args.name, args.output, args.format)
                results = {"status": "success", "results": [result]}
        
        else:
            parser.error("必须指定 --smiles 或 --name")
        
        # 输出结果
        if args.stdout:
            if results.get("results") and results["results"][0].get("base64"):
                r = results["results"][0]
                print(f"data:{r.get('mime_type', 'image/png')};base64,{r['base64']}")
            else:
                print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            if not args.quiet:
                if results.get("results"):
                    for r in results["results"]:
                        if r.get("status") == "success":
                            polymer_tag = " [聚合物]" if r.get("is_polymer") else ""
                            if r.get('output_file'):
                                print(f"✓ 已生成：{r.get('output_file')} ({r.get('size', 'N/A')}, {r.get('format', 'N/A').upper()}){polymer_tag}")
                            else:
                                print(f"✓ 已生成：{r.get('format', 'N/A').upper()} ({r.get('size', 'N/A')}){polymer_tag}")
                        else:
                            print(f"✗ 失败：{r.get('input_name', r.get('smiles', 'Unknown'))} - {r.get('message', 'Unknown error')}")
                    
                    if results.get("total"):
                        print(f"\n完成：{results['success']}/{results['total']} 成功")
                else:
                    print(json.dumps(results, indent=2, ensure_ascii=False))
            else:
                print(json.dumps(results, indent=2, ensure_ascii=False))
    
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
