#!/usr/bin/env python3
"""
IUPAC Name to SMILES Converter

将 IUPAC 化学名称转换为 SMILES 字符串
完全使用 OPSIN API，支持聚合物智能解析
"""

import argparse
import json
import sys
import csv
import re
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

def import_dependencies():
    global Chem, Descriptors, requests
    try:
        from rdkit import Chem
        from rdkit.Chem import Descriptors
    except ImportError:
        print("错误：请安装 rdkit: pip install rdkit", file=sys.stderr)
        sys.exit(1)
    try:
        import requests
    except ImportError:
        print("错误：请安装 requests: pip install requests", file=sys.stderr)
        sys.exit(1)

import_dependencies()


class PolymerParser:
    """聚合物名称解析器"""
    
    # 常见连接基团的 SMILES
    LINKER_GROUPS = {
        'oxy': 'O',           # 氧桥 -O-
        'thio': 'S',          # 硫桥 -S-
        'imino': 'NH',        # 亚氨基 -NH-
        'methylene': '',      # 亚甲基（直接连接）
        'ethylene': '',       # 乙烯基（直接连接）
        'carbonyl': 'C=O',    # 羰基
        'ester': 'C(=O)O',    # 酯基
        'amide': 'C(=O)N',    # 酰胺基
    }
    
    # 聚合物前缀模式
    POLY_PREFIXES = [
        r'poly\s*\[',         # poly[...]
        r'poly\s*\(',         # poly(...)
        r'polymethylene\s+',  # polymethylene...
        r'polyoxy\s*',        # polyoxy...
    ]
    
    def __init__(self):
        pass
    
    def is_polymer(self, name: str) -> bool:
        """检查是否为聚合物名称"""
        name_lower = name.lower().strip()
        for pattern in self.POLY_PREFIXES:
            if re.search(pattern, name_lower):
                return True
        return False
    
    def parse_polymer_name(self, name: str) -> Dict[str, Any]:
        """
        解析聚合物名称，提取单体和连接基团
        
        Args:
            name: 聚合物 IUPAC 名称
        
        Returns:
            解析结果
        """
        name_lower = name.lower().strip()
        result = {
            'is_polymer': True,
            'original_name': name,
            'monomers': [],
            'linkers': [],
            'polymer_type': None,
        }
        
        # 尝试匹配 poly[...] 或 poly(...) 格式（支持嵌套括号）
        match = re.search(r'poly\s*\[(.+)\]', name_lower)
        if not match:
            match = re.search(r'poly\s*\((.+)\)', name_lower)
        if match:
            content = match.group(1).strip()
            result['polymer_type'] = 'bracketed'
            
            # 解析括号内的内容
            # 例如：oxy(1-methylethylene) 或 oxyethylene
            self._parse_bracket_content(content, result)
        else:
            # 处理 polyoxy... 或 polymethylene... 等格式
            for prefix in ['polyoxy', 'polymethylene', 'polyethylene', 'polypropylene']:
                if name_lower.startswith(prefix):
                    result['polymer_type'] = 'prefixed'
                    remainder = name_lower[len(prefix):].strip()
                    
                    # 识别连接基团
                    if 'oxy' in prefix:
                        result['linkers'].append({'name': 'oxy', 'smiles': 'O', 'position': 'backbone'})
                    
                    # 剩余部分作为单体
                    if remainder:
                        result['monomers'].append({
                            'name': remainder,
                            'original': remainder,
                            'position': 'repeat_unit'
                        })
                    break
        
        return result
    
    def _parse_bracket_content(self, content: str, result: Dict[str, Any]):
        """解析括号内的内容"""
        # 尝试匹配 linker(monomer) 格式，如 oxy(1-methylethylene)
        match = re.match(r'(\w+)\s*\((.+)\)', content)
        if match:
            linker_name = match.group(1).strip().lower()
            monomer_name = match.group(2).strip()
            
            # 识别连接基团
            if linker_name in self.LINKER_GROUPS:
                result['linkers'].append({
                    'name': linker_name,
                    'smiles': self.LINKER_GROUPS[linker_name],
                    'position': 'backbone'
                })
            else:
                # 可能是复合名称的一部分
                result['monomers'].append({
                    'name': content,
                    'original': content,
                    'position': 'repeat_unit'
                })
            
            # 添加单体
            result['monomers'].append({
                'name': monomer_name,
                'original': monomer_name,
                'position': 'repeat_unit'
            })
        else:
            # 简单格式，如 oxyethylene
            # 尝试拆分
            parts = re.split(r'(?=[A-Z])|\s+', content)
            for part in parts:
                part = part.strip().lower()
                if not part:
                    continue
                
                if part in self.LINKER_GROUPS:
                    result['linkers'].append({
                        'name': part,
                        'smiles': self.LINKER_GROUPS[part],
                        'position': 'backbone'
                    })
                else:
                    result['monomers'].append({
                        'name': part,
                        'original': part,
                        'position': 'repeat_unit'
                    })


class IUPACToSMILES:
    """IUPAC 名称转 SMILES 转换器"""
    
    OPSIN_API = "https://opsin.ch.cam.ac.uk/opsin"
    
    def __init__(self):
        self.polymer_parser = PolymerParser()
    
    def opsin_name_to_smiles(self, name: str) -> Optional[str]:
        """
        使用 OPSIN API 将 IUPAC 名称转换为 SMILES
        
        Args:
            name: IUPAC 化学名称
        
        Returns:
            SMILES 字符串或 None
        """
        try:
            url = f"{self.OPSIN_API}/{requests.utils.quote(name)}"
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # OPSIN 返回的 JSON 格式
            if isinstance(data, dict):
                if data.get("smiles"):
                    return data["smiles"]
                elif data.get("error"):
                    return None
            elif isinstance(data, list) and len(data) > 0:
                if data[0].get("smiles"):
                    return data[0]["smiles"]
            
            return None
                
        except requests.exceptions.RequestException as e:
            print(f"OPSIN API 调用失败：{e}", file=sys.stderr)
            return None
        except json.JSONDecodeError:
            return None
        except Exception as e:
            print(f"OPSIN 解析错误：{e}", file=sys.stderr)
            return None
    
    def parse_and_convert(self, name: str) -> Dict[str, Any]:
        """
        智能解析并转换 IUPAC 名称
        支持聚合物、复杂名称的灵活解析
        
        Args:
            name: IUPAC 化学名称
        
        Returns:
            转换结果
        """
        name = name.strip()
        
        # 检查是否为聚合物
        if self.polymer_parser.is_polymer(name):
            return self._convert_polymer(name)
        
        # 普通化合物，直接转换
        return self._convert_simple(name)
    
    def _convert_simple(self, name: str) -> Dict[str, Any]:
        """转换简单化合物"""
        smiles = self.opsin_name_to_smiles(name)
        
        if smiles:
            result = {
                "input_name": name,
                "smiles": smiles,
                "isomeric_smiles": smiles,
                "source": "OPSIN",
                "status": "success",
                "type": "simple"
            }
            
            # 计算分子信息
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                result["molecular_formula"] = Chem.rdMolDescriptors.CalcMolFormula(mol)
                result["molecular_weight"] = round(Descriptors.MolWt(mol), 2)
        else:
            result = {
                "input_name": name,
                "status": "error",
                "error": "Name not found",
                "message": f"OPSIN 无法识别：{name}",
                "type": "simple"
            }
        
        return result
    
    def _convert_polymer(self, name: str) -> Dict[str, Any]:
        """
        转换聚合物名称
        
        Args:
            name: 聚合物 IUPAC 名称
        
        Returns:
            转换结果
        """
        parse_result = self.polymer_parser.parse_polymer_name(name)
        
        result = {
            "input_name": name,
            "status": "success",
            "type": "polymer",
            "polymer_info": parse_result,
            "monomer_results": [],
            "final_smiles": None,
            "polymer_smiles": None
        }
        
        # 解析单体 SMILES
        monomers_converted = 0
        for monomer in parse_result['monomers']:
            monomer_name = monomer['name']
            
            # 尝试直接转换单体名称
            smiles = self.opsin_name_to_smiles(monomer_name)
            
            if smiles:
                monomer['smiles'] = smiles
                monomer['status'] = 'success'
                monomers_converted += 1
                
                result['monomer_results'].append({
                    "name": monomer_name,
                    "smiles": smiles,
                    "status": "success"
                })
            else:
                monomer['status'] = 'error'
                result['monomer_results'].append({
                    "name": monomer_name,
                    "smiles": None,
                    "status": "error",
                    "message": f"OPSIN 无法识别：{monomer_name}"
                })
        
        # 构建聚合物 SMILES
        if monomers_converted > 0:
            # 获取第一个成功转换的单体 SMILES
            successful_monomers = [m for m in parse_result['monomers'] if m.get('smiles')]
            
            if successful_monomers:
                monomer_smiles = successful_monomers[0]['smiles']
                
                # 添加连接基团
                linker_smiles = ''
                for linker in parse_result['linkers']:
                    if linker.get('smiles'):
                        linker_smiles = linker['smiles']
                        break
                
                # 构建聚合物 SMILES（使用 RDKit 的重复单元表示）
                if linker_smiles:
                    # 例如：poly[oxy(1-methylethylene)] → -[O-CH(CH3)]n-
                    polymer_smiles = f'*{linker_smiles}{monomer_smiles}*'
                else:
                    polymer_smiles = f'*{monomer_smiles}*'
                
                result['polymer_smiles'] = polymer_smiles
                result['final_smiles'] = polymer_smiles
                
                # 生成说明
                result['explanation'] = self._generate_polymer_explanation(
                    parse_result, 
                    successful_monomers[0] if successful_monomers else None
                )
        
        return result
    
    def _generate_polymer_explanation(self, parse_result: Dict, monomer: Optional[Dict]) -> str:
        """生成聚合物解析说明"""
        parts = []
        
        if parse_result.get('linkers'):
            linker_names = [l['name'] for l in parse_result['linkers']]
            parts.append(f"连接基团：{', '.join(linker_names)}")
        
        if monomer:
            parts.append(f"单体 SMILES: {monomer['smiles']}")
        
        if parse_result.get('polymer_smiles'):
            parts.append(f"聚合物 SMILES: {parse_result['polymer_smiles']}")
        
        return " | ".join(parts)
    
    def batch_convert(self, names: List[str]) -> Dict[str, Any]:
        """
        批量转换
        
        Args:
            names: IUPAC 名称列表
        
        Returns:
            批量转换结果
        """
        results = []
        success_count = 0
        error_count = 0
        
        for name in names:
            name = name.strip()
            if not name:
                continue
            
            result = self.parse_and_convert(name)
            results.append(result)
            
            if result["status"] == "success":
                success_count += 1
            else:
                error_count += 1
        
        return {
            "status": "completed",
            "total": len(names),
            "success": success_count,
            "error": error_count,
            "results": results
        }
    
    def convert_from_file(self, input_file: str) -> Dict[str, Any]:
        """
        从文件读取名称并转换
        
        Args:
            input_file: 输入文件路径（每行一个名称）
        
        Returns:
            转换结果
        """
        with open(input_file, 'r', encoding='utf-8') as f:
            names = [line.strip() for line in f if line.strip()]
        
        return self.batch_convert(names)
    
    def save_results(self, results: Dict[str, Any], output_file: str, format: str = 'json'):
        """
        保存结果到文件
        
        Args:
            results: 转换结果
            output_file: 输出文件路径
            format: 输出格式（json/csv）
        """
        if format.lower() == 'json':
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        elif format.lower() == 'csv':
            if results.get("results"):
                flat_results = []
                for r in results["results"]:
                    flat = {
                        "input_name": r.get("input_name"),
                        "smiles": r.get("smiles") or r.get("polymer_smiles"),
                        "status": r.get("status"),
                        "type": r.get("type"),
                    }
                    if r.get("type") == "polymer":
                        flat["monomer_count"] = len(r.get("monomer_results", []))
                        flat["explanation"] = r.get("explanation")
                    else:
                        flat["molecular_formula"] = r.get("molecular_formula")
                        flat["molecular_weight"] = r.get("molecular_weight")
                    flat_results.append(flat)
                
                with open(output_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=flat_results[0].keys())
                    writer.writeheader()
                    writer.writerows(flat_results)
        else:
            raise ValueError(f"不支持的格式：{format}")


def main():
    parser = argparse.ArgumentParser(
        description='IUPAC 化学名称转 SMILES 转换器（完全使用 OPSIN，支持聚合物）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 单个名称转换
  %(prog)s --name "ethanol"
  
  # 聚合物转换
  %(prog)s --name "poly[oxy(1-methylethylene)]"
  
  # 批量转换
  %(prog)s --names "ethanol,benzene,poly[oxyethylene]"
  
  # 从文件读取
  %(prog)s --input names.txt --output results.json
  
  # 指定输出格式
  %(prog)s --name "aspirin" --format csv
        '''
    )
    
    parser.add_argument('--name', '-n', help='单个 IUPAC 名称')
    parser.add_argument('--names', '-N', help='多个名称（逗号分隔）')
    parser.add_argument('--input', '-i', help='输入文件（每行一个名称）')
    parser.add_argument('--output', '-o', help='输出文件路径')
    parser.add_argument('--format', '-f', choices=['json', 'csv'], default='json',
                        help='输出格式（默认：json）')
    parser.add_argument('--quiet', '-q', action='store_true',
                        help='安静模式，只输出结果')
    
    args = parser.parse_args()
    
    converter = IUPACToSMILES()
    
    try:
        results = None
        
        if args.name:
            result = converter.parse_and_convert(args.name)
            results = {"status": "success", "results": [result]}
        
        elif args.names:
            names = [n.strip() for n in args.names.split(',')]
            results = converter.batch_convert(names)
        
        elif args.input:
            if not Path(args.input).exists():
                print(f"错误：文件不存在：{args.input}", file=sys.stderr)
                sys.exit(1)
            results = converter.convert_from_file(args.input)
        
        else:
            parser.error("必须指定 --name、--names 或 --input")
        
        # 输出结果
        if args.output:
            converter.save_results(results, args.output, args.format)
            if not args.quiet:
                print(f"结果已保存到：{args.output}", file=sys.stderr)
        else:
            output = json.dumps(results, indent=2, ensure_ascii=False)
            print(output)
        
        # 显示统计信息
        if not args.quiet and results.get("total"):
            print(f"\n转换完成：{results['success']}/{results['total']} 成功", file=sys.stderr)
            if results.get("error", 0) > 0:
                print(f"失败：{results['error']}", file=sys.stderr)
    
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}, indent=2), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
