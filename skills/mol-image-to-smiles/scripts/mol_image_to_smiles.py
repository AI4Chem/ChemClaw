#!/usr/bin/env python3
"""
Mol Image to SMILES Converter
将分子结构图片转换为 SMILES 字符串
使用 DECIMER 和 MolNextR 模型
"""

import argparse
import base64
import json
import os
import sys
from pathlib import Path
from datetime import datetime

try:
    from DECIMER import predict_SMILES
    DECIMER_AVAILABLE = True
except ImportError:
    DECIMER_AVAILABLE = False
    print("⚠️  DECIMER 未安装，将使用 API 模式")

import requests


def image_to_base64(image_path: str) -> str:
    """将图片转换为 base64 编码"""
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")
    return image_data


def predict_with_decimer(image_path: str) -> dict:
    """
    使用本地 DECIMER 模型预测 SMILES
    
    Args:
        image_path: 分子图片路径
    
    Returns:
        预测结果字典
    """
    try:
        smiles = predict_SMILES(image_path)
        return {
            "status": "success",
            "smiles": smiles,
            "model": "DECIMER",
            "source": "local"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "model": "DECIMER",
            "source": "local"
        }


def predict_with_decimer_api(image_path: str) -> dict:
    """
    使用 DECIMER API 预测 SMILES
    
    Args:
        image_path: 分子图片路径
    
    Returns:
        预测结果字典
    """
    try:
        # DECIMER 没有官方公开 API，这里预留接口
        # 可以使用本地部署的 DECIMER 服务
        return {
            "status": "error",
            "error": "DECIMER API 未配置，请使用本地模型"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "model": "DECIMER",
            "source": "api"
        }


def predict_with_molnextr(image_path: str) -> dict:
    """
    使用 MolNextR 模型预测 SMILES
    
    Args:
        image_path: 分子图片路径
    
    Returns:
        预测结果字典
    """
    try:
        # MolNextR 目前主要通过 HuggingFace 或本地部署
        # 这里使用 HuggingFace Inference API
        from huggingface_hub import InferenceClient
        
        client = InferenceClient()
        
        # 读取图片
        with open(image_path, "rb") as f:
            image_data = f.read()
        
        # 调用 MolNextR 模型
        # 注意：MolNextR 模型路径可能需要更新
        response = client.image_to_text(
            image=image_data,
            model="MolecularAI/MolNextR"
        )
        
        return {
            "status": "success",
            "smiles": response.strip(),
            "model": "MolNextR",
            "source": "huggingface"
        }
    except ImportError:
        return {
            "status": "error",
            "error": "huggingface_hub 未安装",
            "model": "MolNextR"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "model": "MolNextR",
            "source": "huggingface"
        }


def convert_image_to_smiles(
    image_path: str,
    model: str = "auto",
    output_dir: str = None
) -> dict:
    """
    将分子图片转换为 SMILES
    
    Args:
        image_path: 输入图片路径
        model: 使用的模型 (auto/decimer/molnextr)
        output_dir: 输出目录
    
    Returns:
        转换结果
    """
    image_file = Path(image_path).resolve()
    
    if not image_file.exists():
        return {
            "status": "error",
            "error": f"文件不存在：{image_path}"
        }
    
    print(f"✓ 处理中：{image_file.name}")
    
    result = {
        "input_image": str(image_file),
        "timestamp": datetime.now().isoformat(),
        "results": []
    }
    
    # 根据模型选择进行预测
    if model == "auto":
        # 优先使用本地 DECIMER
        if DECIMER_AVAILABLE:
            print("  使用模型：DECIMER (本地)")
            decimer_result = predict_with_decimer(str(image_file))
            result["results"].append(decimer_result)
            
            if decimer_result["status"] == "success":
                result["best_result"] = decimer_result
            else:
                # 尝试 MolNextR
                print("  尝试 MolNextR...")
                molnextr_result = predict_with_molnextr(str(image_file))
                result["results"].append(molnextr_result)
                if molnextr_result["status"] == "success":
                    result["best_result"] = molnextr_result
        else:
            # 尝试 MolNextR
            print("  使用模型：MolNextR (HuggingFace)")
            molnextr_result = predict_with_molnextr(str(image_file))
            result["results"].append(molnextr_result)
            if molnextr_result["status"] == "success":
                result["best_result"] = molnextr_result
    
    elif model == "decimer":
        print("  使用模型：DECIMER")
        if DECIMER_AVAILABLE:
            decimer_result = predict_with_decimer(str(image_file))
        else:
            decimer_result = predict_with_decimer_api(str(image_file))
        result["results"].append(decimer_result)
        result["best_result"] = decimer_result
    
    elif model == "molnextr":
        print("  使用模型：MolNextR")
        molnextr_result = predict_with_molnextr(str(image_file))
        result["results"].append(molnextr_result)
        result["best_result"] = molnextr_result
    
    else:
        return {
            "status": "error",
            "error": f"未知的模型：{model}"
        }
    
    # 保存结果
    if output_dir:
        output_path = Path(output_dir).resolve()
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 保存 JSON 结果
        output_file = output_path / f"{image_file.stem}_smiles.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        result["output_file"] = str(output_file)
        print(f"  结果已保存：{output_file}")
    
    # 打印结果
    if result.get("best_result") and result["best_result"]["status"] == "success":
        print(f"  ✓ SMILES: {result['best_result']['smiles']}")
        print(f"  ✓ 模型：{result['best_result']['model']}")
    else:
        print("  ✗ 转换失败")
        if result.get("results"):
            for r in result["results"]:
                if r["status"] == "error":
                    print(f"    - {r['model']}: {r.get('error', 'Unknown error')}")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="将分子结构图片转换为 SMILES 字符串 (使用 DECIMER/MolNextR)"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="输入分子图片路径 (支持 png/jpg/jpeg)"
    )
    parser.add_argument(
        "-o", "--output",
        default="~/.openclaw/media/mol-image-to-smiles",
        help="输出目录"
    )
    parser.add_argument(
        "-m", "--model",
        choices=["auto", "decimer", "molnextr"],
        default="auto",
        help="使用的模型 (默认：auto)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="安静模式"
    )
    
    args = parser.parse_args()
    
    # 扩展路径
    input_file = os.path.expanduser(args.input)
    output_dir = os.path.expanduser(args.output)
    
    # 检查输入文件
    if not os.path.exists(input_file):
        print(f"✗ 文件不存在：{input_file}")
        sys.exit(1)
    
    # 检查文件类型
    allowed_extensions = [".png", ".jpg", ".jpeg", ".gif", ".bmp"]
    if Path(input_file).suffix.lower() not in allowed_extensions:
        print(f"⚠️  警告：文件类型可能不支持 ({Path(input_file).suffix})")
    
    # 转换
    result = convert_image_to_smiles(
        input_file,
        model=args.model,
        output_dir=output_dir
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
        print(f"📊 SMILES: {result['best_result']['smiles']}")
        print(f"🤖 模型：{result['best_result']['model']}")
    if result.get("output_file"):
        print(f"📁 结果：{result['output_file']}")


if __name__ == "__main__":
    main()
