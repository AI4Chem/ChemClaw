#!/usr/bin/env python3
"""
Batch Chemistry Data Extractor
Process multiple PDF files, create folder for each, and extract all compound data.
"""

import os
import sys
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime


def find_mineru_script():
    """Find the mineru-pdf-converter script."""
    possible_paths = [
        Path.home() / ".config/agents/skills/mineru-pdf-converter/scripts/pdf_to_markdown.py",
        Path.home() / ".kimi/skills/mineru-pdf-converter/scripts/pdf_to_markdown.py",
        Path.home() / ".claude/skills/mineru-pdf-converter/scripts/pdf_to_markdown.py",
    ]
    for path in possible_paths:
        if path.exists():
            return str(path)
    return None


def convert_pdf(pdf_path: Path, output_base: Path) -> Path:
    """
    Convert PDF to Markdown using mineru-pdf-converter.
    Returns path to the generated full.md file.
    """
    mineru_script = find_mineru_script()
    if not mineru_script:
        raise RuntimeError("mineru-pdf-converter not found. Please install it first.")
    
    pdf_name = pdf_path.stem
    pdf_output_dir = output_base / pdf_name
    
    print(f"[Batch] Converting PDF: {pdf_path.name}")
    
    # Run mineru converter
    cmd = [
        sys.executable, mineru_script,
        str(pdf_path),
        "-o", str(output_base),
        "-m", "vlm"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[Error] Failed to convert {pdf_path.name}: {result.stderr}")
        return None
    
    # Find the generated full.md
    expected_md = pdf_output_dir / "full.md"
    if expected_md.exists():
        return expected_md
    
    # Try to find full.md in subdirectories
    for md_file in pdf_output_dir.rglob("full.md"):
        return md_file
    
    return None


def extract_compounds(md_path: Path) -> list:
    """
    Extract all compounds from markdown file.
    """
    script_dir = Path(__file__).parent
    extract_script = script_dir / "extract_chem_data.py"
    
    cmd = [
        sys.executable, str(extract_script),
        str(md_path),
        "--compact"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"[Error] Failed to extract compounds from {md_path}: {result.stderr}")
        return []
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"[Error] Failed to parse JSON: {e}")
        return []


def process_single_pdf(pdf_path: Path, output_base: Path, keep_md: bool = False) -> dict:
    """
    Process a single PDF file:
    1. Create folder for this PDF
    2. Convert to Markdown
    3. Extract all compounds
    4. Save JSON results
    
    Returns summary dict.
    """
    pdf_name = pdf_path.stem
    pdf_output_dir = output_base / pdf_name
    
    result = {
        "pdf_name": pdf_path.name,
        "pdf_path": str(pdf_path),
        "output_dir": str(pdf_output_dir),
        "status": "pending",
        "compounds_count": 0,
        "compounds_file": None,
        "errors": []
    }
    
    print(f"\n{'='*60}")
    print(f"Processing: {pdf_path.name}")
    print(f"Output folder: {pdf_output_dir}")
    print(f"{'='*60}")
    
    # Create output directory
    pdf_output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Step 1: Convert PDF to Markdown
        md_path = convert_pdf(pdf_path, output_base)
        if not md_path:
            result["status"] = "failed"
            result["errors"].append("PDF conversion failed")
            return result
        
        print(f"[Batch] Markdown generated: {md_path}")
        
        # Step 2: Extract compounds
        compounds = extract_compounds(md_path)
        result["compounds_count"] = len(compounds)
        
        if not compounds:
            print(f"[Warning] No compounds found in {pdf_path.name}")
            result["status"] = "warning"
            result["errors"].append("No compounds found")
        else:
            print(f"[Batch] Extracted {len(compounds)} compounds")
        
        # Step 3: Save JSON results
        json_file = pdf_output_dir / "compounds.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(compounds, f, indent=2, ensure_ascii=False)
        
        result["compounds_file"] = str(json_file)
        result["status"] = "success"
        print(f"[Batch] Saved to: {json_file}")
        
        # Step 4: Create summary file
        summary = {
            "pdf_name": pdf_path.name,
            "processed_at": datetime.now().isoformat(),
            "compounds_count": len(compounds),
            "compounds_file": "compounds.json",
            "compound_list": [c.get("compound_name", "Unknown") for c in compounds]
        }
        
        summary_file = pdf_output_dir / "summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        # Cleanup: Remove markdown and images if not keeping
        if not keep_md:
            # Keep only the JSON files
            for item in pdf_output_dir.iterdir():
                if item.is_dir() and item.name == "images":
                    import shutil
                    shutil.rmtree(item)
                elif item.suffix in ['.md', '.pdf'] and item.name != pdf_path.name:
                    item.unlink()
    
    except Exception as e:
        result["status"] = "error"
        result["errors"].append(str(e))
        print(f"[Error] Exception processing {pdf_path.name}: {e}")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description='Batch extract chemistry compound data from PDF files.'
    )
    parser.add_argument('input', help='Input PDF file or directory containing PDFs')
    parser.add_argument('-o', '--output', default='./chem_extract_output',
                       help='Output base directory (default: ./chem_extract_output)')
    parser.add_argument('--keep-md', action='store_true',
                       help='Keep intermediate markdown files')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip PDFs that already have output folders')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_base = Path(args.output)
    output_base.mkdir(parents=True, exist_ok=True)
    
    # Collect PDF files
    if input_path.is_file():
        if input_path.suffix.lower() != '.pdf':
            print(f"Error: Input file must be PDF: {input_path}")
            sys.exit(1)
        pdf_files = [input_path]
    elif input_path.is_dir():
        pdf_files = sorted(input_path.glob("*.pdf"))
        if not pdf_files:
            print(f"Error: No PDF files found in: {input_path}")
            sys.exit(1)
    else:
        print(f"Error: Input path does not exist: {input_path}")
        sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Batch Chemistry Data Extractor")
    print(f"{'='*60}")
    print(f"Found {len(pdf_files)} PDF file(s)")
    print(f"Output directory: {output_base.absolute()}")
    print(f"{'='*60}\n")
    
    # Process each PDF
    results = []
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"\n[{i}/{len(pdf_files)}] Processing: {pdf_file.name}")
        
        # Check if already processed
        if args.skip_existing:
            expected_output = output_base / pdf_file.stem
            if expected_output.exists() and (expected_output / "compounds.json").exists():
                print(f"[Skip] Already processed: {pdf_file.name}")
                with open(expected_output / "summary.json") as f:
                    summary = json.load(f)
                results.append({
                    "pdf_name": pdf_file.name,
                    "status": "skipped",
                    "compounds_count": summary.get("compounds_count", 0)
                })
                continue
        
        result = process_single_pdf(pdf_file, output_base, args.keep_md)
        results.append(result)
    
    # Generate batch summary
    batch_summary = {
        "processed_at": datetime.now().isoformat(),
        "total_pdfs": len(pdf_files),
        "successful": sum(1 for r in results if r["status"] == "success"),
        "failed": sum(1 for r in results if r["status"] in ["failed", "error"]),
        "skipped": sum(1 for r in results if r["status"] == "skipped"),
        "total_compounds": sum(r.get("compounds_count", 0) for r in results),
        "results": results
    }
    
    summary_file = output_base / "batch_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(batch_summary, f, indent=2, ensure_ascii=False)
    
    # Print final summary
    print(f"\n{'='*60}")
    print(f"Batch Processing Complete!")
    print(f"{'='*60}")
    print(f"Total PDFs: {batch_summary['total_pdfs']}")
    print(f"Successful: {batch_summary['successful']}")
    print(f"Failed: {batch_summary['failed']}")
    print(f"Skipped: {batch_summary['skipped']}")
    print(f"Total compounds extracted: {batch_summary['total_compounds']}")
    print(f"Summary file: {summary_file}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
