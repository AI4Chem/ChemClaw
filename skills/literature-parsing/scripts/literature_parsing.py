#!/usr/bin/env python3
"""
Literature Parsing Script using MinerU
将 PDF 文献转换为 Markdown 并提取图片
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from datetime import datetime


def run_mineru(input_pdf: str, output_dir: str, method: str = "auto", 
               lang: str = "ch", device: str = "cpu") -> dict:
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
    
    print(f"✓ 开始处理：{input_path.name}")
    print(f"  输出目录：{output_path}")
    print(f"  解析方法：{method}")
    print(f"  设备：{device}")
    
    # 运行 MinerU
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 分钟超时
        )
        
        if result.returncode != 0:
            print(f"✗ MinerU 执行失败：{result.stderr}")
            return {"success": False, "error": result.stderr}
            
    except subprocess.TimeoutExpired:
        print("✗ 处理超时（超过 10 分钟）")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        print(f"✗ 执行错误：{e}")
        return {"success": False, "error": str(e)}
    
    # 查找输出文件
    # MinerU 输出结构：output_dir/<pdf_name>/txt/
    pdf_name = input_path.stem
    txt_dir = output_path / pdf_name / "txt"
    
    if not txt_dir.exists():
        # 尝试直接输出到 output_dir
        txt_dir = output_path
    
    # 查找 markdown 文件
    md_files = list(txt_dir.glob("*.md"))
    if not md_files:
        print("✗ 未找到生成的 Markdown 文件")
        return {"success": False, "error": "No markdown file found"}
    
    md_file = md_files[0]
    
    # 查找图片目录
    images_dir = txt_dir / "images"
    
    # 统计结果
    result_info = {
        "success": True,
        "input_file": str(input_path),
        "markdown_file": str(md_file),
        "images_dir": str(images_dir) if images_dir.exists() else None,
        "images_count": 0,
        "output_dir": str(txt_dir)
    }
    
    # 统计图片数量
    if images_dir.exists():
        images = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))
        result_info["images_count"] = len(images)
        result_info["images"] = [str(img) for img in images]
    
    print(f"✓ 处理完成：{input_path.name}")
    print(f"  Markdown: {md_file.name}")
    print(f"  图片数量：{result_info['images_count']} 张")
    
    return result_info


def organize_output(result: dict, final_output_dir: str) -> dict:
    """
    整理输出文件到统一目录
    
    Args:
        result: MinerU 转换结果
        final_output_dir: 最终输出目录
    
    Returns:
        整理后的结果
    """
    if not result.get("success"):
        return result
    
    final_path = Path(final_output_dir).resolve()
    final_path.mkdir(parents=True, exist_ok=True)
    
    # 复制 Markdown 文件
    md_src = Path(result["markdown_file"])
    md_dst = final_path / md_src.name
    
    shutil.copy2(md_src, md_dst)
    
    # 复制图片目录
    images_final = final_path / "images"
    if result.get("images_dir") and Path(result["images_dir"]).exists():
        if images_final.exists():
            shutil.rmtree(images_final)
        shutil.copytree(result["images_dir"], images_final)
    
    # 生成元数据
    metadata = {
        "input_file": result["input_file"],
        "output_dir": str(final_path),
        "markdown_file": str(md_dst),
        "images_count": result["images_count"],
        "converted_at": datetime.now().isoformat(),
        "tool": "MinerU"
    }
    
    # 保存元数据
    meta_file = final_path / f"{md_src.stem}_metadata.json"
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✓ 文件已整理到：{final_path}")
    
    return {
        "success": True,
        "output_dir": str(final_path),
        "markdown_file": str(md_dst),
        "images_dir": str(images_final) if images_final.exists() else None,
        "metadata_file": str(meta_file),
        **metadata
    }


def main():
    parser = argparse.ArgumentParser(
        description="将 PDF 文献转换为 Markdown 并提取图片 (使用 MinerU)"
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="输入 PDF 文件路径"
    )
    parser.add_argument(
        "-o", "--output",
        default="~/.openclaw/media/literature-parsing",
        help="输出目录"
    )
    parser.add_argument(
        "-m", "--method",
        choices=["auto", "txt", "ocr"],
        default="auto",
        help="解析方法：auto(自动)/txt(文本)/ocr(扫描版)"
    )
    parser.add_argument(
        "-l", "--lang",
        default="ch",
        help="OCR 语言 (默认：ch)"
    )
    parser.add_argument(
        "-d", "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="计算设备 (默认：cpu)"
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
    
    # 运行 MinerU
    temp_output = Path(output_dir) / "temp"
    result = run_mineru(
        input_file,
        str(temp_output),
        method=args.method,
        lang=args.lang,
        device=args.device
    )
    
    if not result.get("success"):
        print(f"✗ 转换失败：{result.get('error', 'Unknown error')}")
        sys.exit(1)
    
    # 整理输出
    final_output = Path(output_dir) / Path(input_file).stem
    final_result = organize_output(result, str(final_output))
    
    # 清理临时目录
    if temp_output.exists():
        shutil.rmtree(temp_output)
    
    if not final_result.get("success"):
        print("✗ 整理输出失败")
        sys.exit(1)
    
    print("\n✅ 转换完成！")
    print(f"📄 Markdown: {final_result['markdown_file']}")
    if final_result.get('images_dir'):
        print(f"🖼️  图片：{final_result['images_dir']} ({final_result['images_count']} 张)")
    print(f"📊 元数据：{final_result['metadata_file']}")
    
    # 输出 JSON（用于程序调用）
    if args.quiet:
        print(json.dumps(final_result, ensure_ascii=False))


if __name__ == "__main__":
    main()
