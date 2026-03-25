#!/usr/bin/env python3
"""
SMILES to IUPAC Name Converter (Optimized)
将 SMILES 字符串转换为 IUPAC 化学名称
使用多种方法：PubChem API, NCI/CADD, RDKit InChI, STOUT
"""

import argparse
import json
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List

try:
    from rdkit import Chem
    from rdkit.Chem import rdMolDescriptors, Descriptors
    RDKit_AVAILABLE = True
except ImportError:
    RDKit_AVAILABLE = False
    print("⚠️  RDKit 未安装，部分功能不可用")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


def validate_smiles(smiles: str) -> bool:
    """验证 SMILES 字符串是否有效"""
    if not RDKit_AVAILABLE:
        return True  # 无法验证，假设有效
    try:
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except:
        return False


def clean_smiles(smiles: str) -> str:
    """清理 SMILES 字符串（移除聚合物标记等）"""
    # 移除聚合物标记
    cleaned = smiles.strip('*').replace('*', '')
    # 移除空格
    cleaned = cleaned.replace(' ', '')
    return cleaned


def get_molecular_properties(smiles: str) -> Dict:
    """获取分子基本性质"""
    if not RDKit_AVAILABLE:
        return {}
    
    try:
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return {}
        
        return {
            "molecular_formula": rdMolDescriptors.CalcMolFormula(mol),
            "molecular_weight": Descriptors.MolWt(mol),
            "exact_mass": Descriptors.ExactMolWt(mol),
            "num_atoms": mol.GetNumAtoms(),
            "num_heavy_atoms": mol.GetNumHeavyAtoms(),
            "num_rings": rdMolDescriptors.CalcNumRings(mol),
            "num_aromatic_rings": rdMolDescriptors.CalcNumAromaticRings(mol),
            "num_h_bond_donors": rdMolDescriptors.CalcNumHBD(mol),
            "num_h_bond_acceptors": rdMolDescriptors.CalcNumHBA(mol),
            "logp": Descriptors.MolLogP(mol),
            "tpsa": rdMolDescriptors.CalcTPSA(mol)
        }
    except Exception as e:
        return {"error": str(e)}


def convert_with_pubchem(smiles: str) -> Dict:
    """
    使用 PubChem PUG-REST API 转换
    
    Args:
        smiles: SMILES 字符串
    
    Returns:
        转换结果字典
    """
    if not REQUESTS_AVAILABLE:
        return {"status": "error", "error": "requests library not installed"}
    
    try:
        # 清理 SMILES
        clean_smiles_str = clean_smiles(smiles)
        
        # 使用 PubChem PUG-REST API
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/{clean_smiles_str}/property/IUPACName/json"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            if 'PropertyTable' in data and 'Properties' in data['PropertyTable']:
                iupac_name = data['PropertyTable']['Properties'][0]['IUPACName']
                return {
                    "status": "success",
                    "iupac_name": iupac_name,
                    "smiles": smiles,
                    "model": "PubChem",
                    "source": "api",
                    "confidence": "high"
                }
            else:
                return {
                    "status": "error",
                    "error": "No IUPAC name in response",
                    "model": "PubChem"
                }
        else:
            return {
                "status": "error",
                "error": f"PubChem API error: {response.status_code}",
                "model": "PubChem"
            }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error": "PubChem API timeout",
            "model": "PubChem"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "model": "PubChem"
        }


def convert_with_nci(smiles: str) -> Dict:
    """
    使用 NCI/CADD Chemical Identifier Resolver 转换
    
    Args:
        smiles: SMILES 字符串
    
    Returns:
        转换结果字典
    """
    if not REQUESTS_AVAILABLE:
        return {"status": "error", "error": "requests library not installed"}
    
    try:
        clean_smiles_str = clean_smiles(smiles)
        
        # 使用 NCI/CADD API
        url = f"https://cactus.nci.nih.gov/chemical/structure/{clean_smiles_str}/iupac_name"
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            iupac_name = response.text.strip()
            if iupac_name and not iupac_name.startswith('<'):
                return {
                    "status": "success",
                    "iupac_name": iupac_name,
                    "smiles": smiles,
                    "model": "NCI/CADD",
                    "source": "api",
                    "confidence": "high"
                }
            else:
                return {
                    "status": "error",
                    "error": "Invalid response from NCI API",
                    "model": "NCI/CADD"
                }
        else:
            return {
                "status": "error",
                "error": f"NCI API error: {response.status_code}",
                "model": "NCI/CADD"
            }
    except requests.exceptions.Timeout:
        return {
            "status": "error",
            "error": "NCI API timeout",
            "model": "NCI/CADD"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "model": "NCI/CADD"
        }


def convert_with_inchi(smiles: str) -> Dict:
    """
    使用 RDKit 生成 InChI（可作为 IUPAC 的替代）
    
    Args:
        smiles: SMILES 字符串
    
    Returns:
        转换结果字典
    """
    if not RDKit_AVAILABLE:
        return {"status": "error", "error": "RDKit not installed"}
    
    try:
        clean_smiles_str = clean_smiles(smiles)
        mol = Chem.MolFromSmiles(clean_smiles_str)
        
        if not mol:
            return {
                "status": "error",
                "error": "Invalid SMILES",
                "model": "RDKit-InChI"
            }
        
        # 生成 InChI
        inchi = Chem.MolToInchi(mol)
        
        if inchi:
            return {
                "status": "success",
                "iupac_name": f"InChI: {inchi}",
                "inchi": inchi,
                "smiles": smiles,
                "model": "RDKit-InChI",
                "source": "local",
                "confidence": "medium",
                "note": "InChI is a standardized chemical identifier, can be converted to IUPAC"
            }
        else:
            return {
                "status": "error",
                "error": "Failed to generate InChI",
                "model": "RDKit-InChI"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "model": "RDKit-InChI"
        }


def convert_with_stout(smiles: str) -> Dict:
    """
    使用 STOUT Docker 容器转换
    
    Args:
        smiles: SMILES 字符串
    
    Returns:
        转换结果字典
    """
    try:
        clean_smiles_str = clean_smiles(smiles)
        
        # 创建临时 Python 脚本
        script_content = f'''
from rdkit import Chem
from rdkit.Chem import rdMolDescriptors

smiles = "{clean_smiles_str}"
mol = Chem.MolFromSmiles(smiles)

if mol:
    # 生成 InChI
    inchi = Chem.MolToInchi(mol)
    print(f"INCHI:{{inchi}}")
    
    # 获取分子式
    formula = rdMolDescriptors.CalcMolFormula(mol)
    print(f"FORMULA:{{formula}}")
    
    # 获取分子量
    mw = rdMolDescriptors.CalcExactMolWt(mol)
    print(f"MOLWT:{{mw:.4f}}")
else:
    print("ERROR:Invalid SMILES")
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            temp_script = f.name
        
        try:
            # 运行 STOUT
            result = subprocess.run(
                ['stout', 'run_script', temp_script],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                output = result.stdout.strip()
                lines = output.split('\n')
                
                inchi = None
                formula = None
                molwt = None
                
                for line in lines:
                    if line.startswith('INCHI:'):
                        inchi = line.split(':', 1)[1]
                    elif line.startswith('FORMULA:'):
                        formula = line.split(':', 1)[1]
                    elif line.startswith('MOLWT:'):
                        molwt = line.split(':', 1)[1]
                
                if inchi:
                    return {
                        "status": "success",
                        "iupac_name": f"InChI: {inchi}",
                        "inchi": inchi,
                        "molecular_formula": formula,
                        "molecular_weight": float(molwt) if molwt else None,
                        "smiles": smiles,
                        "model": "STOUT",
                        "source": "docker",
                        "confidence": "medium"
                    }
                else:
                    return {
                        "status": "error",
                        "error": "No InChI generated",
                        "model": "STOUT"
                    }
            else:
                return {
                    "status": "error",
                    "error": result.stderr or "STOUT execution failed",
                    "model": "STOUT"
                }
        finally:
            if os.path.exists(temp_script):
                os.unlink(temp_script)
                
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "STOUT timeout",
            "model": "STOUT"
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "error": "STOUT not installed or Docker not available",
            "model": "STOUT"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "model": "STOUT"
        }


def smiles_to_iupac(
    smiles: str,
    method: str = "auto",
    output_dir: str = None,
    include_properties: bool = True
) -> Dict:
    """
    将 SMILES 转换为 IUPAC 名称（多方法智能选择）
    
    Args:
        smiles: SMILES 字符串
        method: 使用的方法 (auto/pubchem/nci/stout/inchi)
        output_dir: 输出目录
        include_properties: 是否包含分子性质
    
    Returns:
        转换结果
    """
    print(f"✓ 处理中：{smiles}")
    
    result = {
        "input_smiles": smiles,
        "cleaned_smiles": clean_smiles(smiles),
        "timestamp": datetime.now().isoformat(),
        "results": [],
        "best_result": None
    }
    
    # 获取分子性质
    if include_properties and RDKit_AVAILABLE:
        properties = get_molecular_properties(result["cleaned_smiles"])
        if properties:
            result["molecular_properties"] = properties
    
    # 验证 SMILES
    if not validate_smiles(result["cleaned_smiles"]):
        return {
            "status": "error",
            "error": "Invalid SMILES string",
            "input_smiles": smiles
        }
    
    # 定义方法优先级
    methods_order = {
        "auto": ["pubchem", "nci", "stout", "inchi"],
        "pubchem": ["pubchem"],
        "nci": ["nci"],
        "stout": ["stout"],
        "inchi": ["inchi"]
    }
    
    methods_to_try = methods_order.get(method, ["pubchem", "nci", "stout", "inchi"])
    
    # 依次尝试各种方法
    for m in methods_to_try:
        if m == "pubchem":
            print(f"  尝试 PubChem API...")
            pubchem_result = convert_with_pubchem(smiles)
            result["results"].append(pubchem_result)
            
            if pubchem_result["status"] == "success":
                result["best_result"] = pubchem_result
                print(f"  ✓ 使用模型：PubChem")
                break
        
        elif m == "nci":
            print(f"  尝试 NCI/CADD API...")
            nci_result = convert_with_nci(smiles)
            result["results"].append(nci_result)
            
            if nci_result["status"] == "success":
                result["best_result"] = nci_result
                print(f"  ✓ 使用模型：NCI/CADD")
                break
        
        elif m == "stout":
            print(f"  尝试 STOUT (Docker)...")
            stout_result = convert_with_stout(smiles)
            result["results"].append(stout_result)
            
            if stout_result["status"] == "success":
                result["best_result"] = stout_result
                print(f"  ✓ 使用模型：STOUT")
                break
        
        elif m == "inchi":
            print(f"  生成 InChI...")
            inchi_result = convert_with_inchi(smiles)
            result["results"].append(inchi_result)
            
            if inchi_result["status"] == "success":
                result["best_result"] = inchi_result
                print(f"  ✓ 使用模型：RDKit-InChI")
                break
    
    # 保存结果
    if output_dir and result["best_result"]:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成安全的文件名
        safe_smiles = result["cleaned_smiles"].replace("/", "_").replace("\\", "_").replace("=", "_")
        if len(safe_smiles) > 50:
            safe_smiles = safe_smiles[:50]
        
        output_file = output_path / f"{safe_smiles}_iupac.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        result["output_file"] = str(output_file)
        print(f"  结果已保存：{output_file}")
    
    # 打印结果
    if result.get("best_result") and result["best_result"]["status"] == "success":
        iupac = result["best_result"]["iupac_name"]
        if len(iupac) > 100:
            iupac = iupac[:100] + "..."
        print(f"  ✓ IUPAC: {iupac}")
        print(f"  ✓ 模型：{result['best_result']['model']}")
        if result["best_result"].get("confidence"):
            print(f"  ✓ 置信度：{result['best_result']['confidence']}")
    else:
        print("  ✗ 转换失败")
        for r in result["results"]:
            if r["status"] == "error":
                print(f"    - {r['model']}: {r.get('error', 'Unknown error')}")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="将 SMILES 字符串转换为 IUPAC 化学名称 (优化版)"
    )
    parser.add_argument(
        "-s", "--smiles",
        required=True,
        help="输入 SMILES 字符串"
    )
    parser.add_argument(
        "-o", "--output",
        default="~/.openclaw/media/smiles-to-iupac",
        help="输出目录"
    )
    parser.add_argument(
        "-m", "--method",
        choices=["auto", "pubchem", "nci", "stout", "inchi"],
        default="auto",
        help="使用的方法 (默认：auto)"
    )
    parser.add_argument(
        "--no-properties",
        action="store_true",
        help="不计算分子性质"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="安静模式"
    )
    
    args = parser.parse_args()
    
    # 扩展路径
    output_dir = os.path.expanduser(args.output)
    
    # 转换
    result = smiles_to_iupac(
        args.smiles,
        method=args.method,
        output_dir=output_dir,
        include_properties=not args.no_properties
    )
    
    if result.get("status") == "error" or (
        result.get("best_result") and 
        result["best_result"].get("status") == "error"
    ):
        print(f"\n✗ 转换失败：{result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    # 输出 JSON（安静模式）
    if args.quiet:
        print(json.dumps(result, ensure_ascii=False))
    
    print("\n✅ 转换完成！")
    if result.get("best_result") and result["best_result"]["status"] == "success":
        print(f"📊 IUPAC: {result['best_result']['iupac_name']}")
        print(f"🤖 模型：{result['best_result']['model']}")
    if result.get("output_file"):
        print(f"📁 结果：{result['output_file']}")


if __name__ == "__main__":
    main()
