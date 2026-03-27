#!/usr/bin/env python3
"""
MinerU PDF to Markdown Converter
使用 MinerU API 将 PDF 文件转换为 Markdown 格式，保留所有图片和元数据
支持超过600页的大文件分批处理
"""

import os
import sys
import json
import time
import zipfile
import tempfile
import subprocess
import re
from pathlib import Path
from typing import List, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# API 配置
MINERU_API_BASE = "https://mineru.net/api/v4"
MAX_PAGES_PER_BATCH = 600  # MinerU 单文件最大页数限制


def get_api_token():
    """
    获取 API Token，按优先级：
    1. 环境变量 MINERU_API_TOKEN
    2. Skill 目录下的 API_KEY 文件
    3. 用户目录 ~/.config/agents/skills/mineru-pdf-converter/API_KEY
    """
    # 1. 环境变量
    token = os.environ.get('MINERU_API_TOKEN')
    if token:
        return token.strip()
    
    # 2. Skill 目录下的 API_KEY 文件（相对脚本路径）
    skill_dir = Path(__file__).parent.parent
    api_key_file = skill_dir / "API_KEY"
    if api_key_file.exists():
        return api_key_file.read_text().strip()
    
    # 3. 用户目录
    user_key_file = Path.home() / ".config/agents/skills/mineru-pdf-converter/API_KEY"
    if user_key_file.exists():
        return user_key_file.read_text().strip()
    
    return None


def create_session():
    """创建带重试的 HTTP session"""
    session = requests.Session()
    retry = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session


session = create_session()


def get_pdf_page_count(pdf_path: str) -> int:
    """获取 PDF 文件的总页数"""
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        count = len(doc)
        doc.close()
        return count
    except ImportError:
        # 如果没有 PyMuPDF，使用 pdfinfo 命令
        try:
            result = subprocess.run(
                ['pdfinfo', pdf_path],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.split('\n'):
                if line.startswith('Pages:'):
                    return int(line.split(':')[1].strip())
        except:
            pass
        return -1


def split_pdf_by_pages(pdf_path: str, output_dir: str, pages_per_batch: int = MAX_PAGES_PER_BATCH) -> List[str]:
    """
    按页数拆分 PDF 文件
    
    Returns:
        List[str]: 拆分后的 PDF 文件路径列表
    """
    import fitz  # PyMuPDF
    
    pdf_path = Path(pdf_path)
    doc = fitz.open(str(pdf_path))
    total_pages = len(doc)
    
    if total_pages <= pages_per_batch:
        doc.close()
        return [str(pdf_path)]
    
    os.makedirs(output_dir, exist_ok=True)
    split_files = []
    
    num_batches = (total_pages + pages_per_batch - 1) // pages_per_batch
    print(f"[Split] PDF 共 {total_pages} 页，将拆分为 {num_batches} 个批次（每批最多 {pages_per_batch} 页）")
    
    for i in range(num_batches):
        start_page = i * pages_per_batch
        end_page = min((i + 1) * pages_per_batch, total_pages)
        
        new_doc = fitz.open()
        new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page - 1)
        
        output_filename = f"{pdf_path.stem}_part{i+1:03d}.pdf"
        output_path = Path(output_dir) / output_filename
        new_doc.save(str(output_path))
        new_doc.close()
        
        split_files.append(str(output_path))
        print(f"[Split] 批次 {i+1}/{num_batches}: 第 {start_page+1}-{end_page} 页 -> {output_filename}")
    
    doc.close()
    return split_files


def get_upload_urls(token: str, file_names: list, model_version: str = "vlm"):
    """获取批量文件上传 URL"""
    url = f"{MINERU_API_BASE}/file-urls/batch"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    files_info = [{"name": name} for name in file_names]
    data = {
        "files": files_info,
        "model_version": model_version
    }
    
    response = session.post(url, headers=headers, json=data)
    result = response.json()
    
    if result.get("code") == 0:
        return result["data"]["batch_id"], result["data"]["file_urls"]
    else:
        raise Exception(f"获取上传链接失败: {result}")


def upload_file(file_path: str, upload_url: str):
    """上传单个文件到指定 URL"""
    with open(file_path, 'rb') as f:
        response = session.put(upload_url, data=f)
        return response.status_code == 200


def check_batch_result(token: str, batch_id: str):
    """查询批量任务处理结果"""
    url = f"{MINERU_API_BASE}/extract-results/batch/{batch_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    response = session.get(url, headers=headers)
    return response.json()


def download_and_extract(zip_url: str, output_dir: str, timeout: int = 180):
    """下载结果 zip 并解压到指定目录"""
    # 清除代理环境变量以避免 SSL 问题
    env = os.environ.copy()
    for key in ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']:
        env.pop(key, None)
    
    with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        result = subprocess.run(
            ['curl', '-L', '-k', '-o', tmp_path, zip_url],
            capture_output=True, text=True, timeout=timeout, env=env
        )
        if result.returncode != 0:
            raise Exception(f"下载失败: {result.stderr[:200]}")
        
        if not os.path.exists(tmp_path) or os.path.getsize(tmp_path) == 0:
            raise Exception("下载文件为空")
        
        os.makedirs(output_dir, exist_ok=True)
        with zipfile.ZipFile(tmp_path, 'r') as z:
            z.extractall(output_dir)
            return z.namelist()
        
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def convert_pdf(token: str, pdf_path: str, output_dir: str, 
                model_version: str = "vlm", 
                max_wait: int = 600,
                poll_interval: int = 5) -> dict:
    """
    转换单个 PDF 文件为 Markdown
    
    Args:
        token: MinerU API Token
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        model_version: 模型版本 (vlm, pipeline, MinerU-HTML)
        max_wait: 最大等待时间(秒)
        poll_interval: 轮询间隔(秒)
    
    Returns:
        dict: 转换结果，包含 output_dir, files, status 等
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
    
    file_name = pdf_path.name
    print(f"[MinerU] 开始处理: {file_name}")
    
    # 1. 获取上传链接
    batch_id, upload_urls = get_upload_urls(token, [file_name], model_version)
    print(f"[MinerU] 获取上传链接成功, batch_id: {batch_id}")
    
    # 2. 上传文件
    if not upload_file(str(pdf_path), upload_urls[0]):
        raise Exception("文件上传失败")
    print(f"[MinerU] 文件上传成功")
    
    # 3. 轮询等待处理完成
    print(f"[MinerU] 等待解析完成...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        result = check_batch_result(token, batch_id)
        
        if result.get("code") != 0:
            raise Exception(f"查询任务失败: {result}")
        
        extract_result = result["data"].get("extract_result", [])
        if not extract_result:
            time.sleep(poll_interval)
            continue
        
        status = extract_result[0]["state"]
        
        if status == "done":
            zip_url = extract_result[0].get("full_zip_url")
            if zip_url:
                print(f"[MinerU] 解析完成，正在下载结果...")
                files = download_and_extract(zip_url, output_dir)
                print(f"[MinerU] 转换成功! 输出目录: {output_dir}")
                return {
                    "status": "success",
                    "output_dir": output_dir,
                    "files": files,
                    "batch_id": batch_id
                }
        
        elif status == "failed":
            err_msg = extract_result[0].get("err_msg", "未知错误")
            raise Exception(f"解析失败: {err_msg}")
        
        elif status in ["pending", "running", "converting"]:
            elapsed = int(time.time() - start_time)
            if elapsed % 30 == 0:
                print(f"[MinerU] 状态: {status}, 已等待 {elapsed}s...")
        
        time.sleep(poll_interval)
    
    raise TimeoutError(f"等待超时，超过 {max_wait} 秒")


def merge_markdown_files(md_files: List[str], output_path: str) -> str:
    """
    合并多个 Markdown 文件
    
    Args:
        md_files: Markdown 文件路径列表（按顺序）
        output_path: 合并后的输出路径
    
    Returns:
        str: 合并后的文件路径
    """
    print(f"[Merge] 合并 {len(md_files)} 个 Markdown 文件...")
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        for i, md_file in enumerate(md_files):
            if i > 0:
                outfile.write('\n\n---\n\n')  # 添加分隔线
            
            with open(md_file, 'r', encoding='utf-8') as infile:
                content = infile.read()
                outfile.write(content)
                
            print(f"[Merge] 已合并: {Path(md_file).name}")
    
    print(f"[Merge] 合并完成: {output_path}")
    return output_path


def convert_large_pdf(token: str, pdf_path: str, output_dir: str,
                      model_version: str = "vlm",
                      max_wait: int = 600,
                      temp_dir: str = None) -> dict:
    """
    转换大 PDF 文件（支持超过 600 页的文件）
    
    Args:
        token: MinerU API Token
        pdf_path: PDF 文件路径
        output_dir: 输出目录
        model_version: 模型版本
        max_wait: 每批最大等待时间(秒)
        temp_dir: 临时目录（存放拆分后的 PDF）
    
    Returns:
        dict: 转换结果
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF 文件不存在: {pdf_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # 检查是否需要拆分
    total_pages = get_pdf_page_count(str(pdf_path))
    print(f"[LargePDF] 总页数: {total_pages}")
    
    if total_pages <= MAX_PAGES_PER_BATCH:
        # 不需要拆分，直接转换
        return convert_pdf(token, str(pdf_path), output_dir, model_version, max_wait)
    
    # 需要拆分处理
    print(f"[LargePDF] 文件超过 {MAX_PAGES_PER_BATCH} 页，需要分批处理")
    
    # 创建临时目录
    if temp_dir is None:
        temp_dir = tempfile.mkdtemp(prefix="pdf_split_")
    else:
        os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # 拆分 PDF
        split_files = split_pdf_by_pages(str(pdf_path), temp_dir, MAX_PAGES_PER_BATCH)
        
        # 分别转换每个批次
        batch_outputs = []
        all_files = []
        
        for i, split_file in enumerate(split_files):
            batch_output_dir = os.path.join(temp_dir, f"batch_{i+1:03d}")
            os.makedirs(batch_output_dir, exist_ok=True)
            
            print(f"\n[LargePDF] 处理批次 {i+1}/{len(split_files)}...")
            result = convert_pdf(token, split_file, batch_output_dir, model_version, max_wait)
            
            batch_outputs.append(batch_output_dir)
            all_files.extend(result.get("files", []))
        
        # 合并 Markdown 文件
        md_files = []
        for batch_dir in batch_outputs:
            full_md = os.path.join(batch_dir, "full.md")
            if os.path.exists(full_md):
                md_files.append(full_md)
        
        if md_files:
            merged_md_path = os.path.join(output_dir, "full.md")
            merge_markdown_files(md_files, merged_md_path)
        
        # 合并图片目录
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(images_dir, exist_ok=True)
        
        image_count = 0
        for batch_dir in batch_outputs:
            batch_images_dir = os.path.join(batch_dir, "images")
            if os.path.exists(batch_images_dir):
                for img_file in os.listdir(batch_images_dir):
                    src = os.path.join(batch_images_dir, img_file)
                    dst = os.path.join(images_dir, f"batch{image_count:04d}_{img_file}")
                    # 复制图片文件
                    import shutil
                    shutil.copy2(src, dst)
                image_count += len(os.listdir(batch_images_dir))
        
        # 复制原始 PDF
        import shutil
        shutil.copy2(str(pdf_path), os.path.join(output_dir, f"{pdf_path.stem}_origin.pdf"))
        
        print(f"\n[LargePDF] 大文件处理完成!")
        print(f"[LargePDF] 输出目录: {output_dir}")
        
        return {
            "status": "success",
            "output_dir": output_dir,
            "files": ["full.md", "images/", f"{pdf_path.stem}_origin.pdf"],
            "batches": len(split_files),
            "total_pages": total_pages
        }
        
    finally:
        # 清理临时目录
        if temp_dir and os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            print(f"[LargePDF] 清理临时文件")


def batch_convert(token: str, pdf_paths: list, output_base_dir: str,
                  model_version: str = "vlm") -> list:
    """
    批量转换多个 PDF 文件
    
    Args:
        token: MinerU API Token
        pdf_paths: PDF 文件路径列表
        output_base_dir: 输出基础目录
        model_version: 模型版本
    
    Returns:
        list: 每个文件的转换结果
    """
    results = []
    
    for pdf_path in pdf_paths:
        pdf_path = Path(pdf_path)
        # 为每个PDF创建独立子目录
        output_dir = os.path.join(output_base_dir, pdf_path.stem)
        
        try:
            result = convert_large_pdf(token, str(pdf_path), output_dir, model_version)
            results.append({
                "pdf": str(pdf_path),
                "success": True,
                **result
            })
        except Exception as e:
            results.append({
                "pdf": str(pdf_path),
                "success": False,
                "error": str(e)
            })
    
    return results


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MinerU PDF to Markdown Converter')
    parser.add_argument('pdf_path', help='PDF 文件路径或目录')
    parser.add_argument('-o', '--output', default='output', help='输出目录')
    parser.add_argument('-t', '--token', help='MinerU API Token')
    parser.add_argument('-m', '--model', default='vlm', 
                       choices=['vlm', 'pipeline', 'MinerU-HTML'],
                       help='模型版本')
    parser.add_argument('--ocr', action='store_true', help='启用 OCR')
    
    args = parser.parse_args()
    
    # 获取 API Token：参数 > 环境变量 > Skill 内置
    token = args.token or get_api_token()
    if not token:
        print("错误: 未找到 API Token")
        print("请通过以下方式之一提供：")
        print("  1. 命令行参数: -t YOUR_TOKEN")
        print("  2. 环境变量: export MINERU_API_TOKEN=YOUR_TOKEN")
        print("  3. 在 Skill 目录创建 API_KEY 文件")
        sys.exit(1)
    
    pdf_path = Path(args.pdf_path)
    
    if pdf_path.is_dir():
        # 批量处理目录
        pdf_files = list(pdf_path.glob('*.pdf'))
        if not pdf_files:
            print(f"错误: 目录 {pdf_path} 中没有 PDF 文件")
            sys.exit(1)
        
        print(f"找到 {len(pdf_files)} 个 PDF 文件")
        results = batch_convert(token, [str(p) for p in pdf_files], args.output, args.model)
        
        # 打印结果摘要
        success = sum(1 for r in results if r['success'])
        print(f"\n{'='*50}")
        print(f"转换完成: {success}/{len(results)} 成功")
        for r in results:
            status = "✓" if r['success'] else "✗"
            print(f"  {status} {r['pdf']}")
            if not r['success']:
                print(f"    错误: {r.get('error', 'Unknown')}")
    
    else:
        # 单个文件
        output_dir = os.path.join(args.output, pdf_path.stem)
        try:
            result = convert_large_pdf(token, str(pdf_path), output_dir, args.model)
            print(f"\n转换成功!")
            print(f"输出目录: {result['output_dir']}")
            if result.get('batches'):
                print(f"分批处理: {result['batches']} 批次, {result['total_pages']} 页")
            print(f"包含文件: {', '.join(result['files'][:5])}" + 
                  ("..." if len(result['files']) > 5 else ""))
        except Exception as e:
            print(f"转换失败: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
