#!/usr/bin/env python3
"""
输入输出工具函数
提供文件读取、结果输出、格式化等功能
"""

import json
import csv
from typing import List, Dict, Any
from pathlib import Path


def read_smiles_file(file_path: str) -> List[Dict[str, str]]:
    """
    从文件读取 SMILES 数据

    支持格式:
    - .smi: SMILES 文件 (SMILES<tab>name)
    - .txt: 文本文件 (每行一个 SMILES 或 SMILES<tab>name)
    - .csv: CSV 文件 (需要有 smiles 列)
    - .json: JSON 文件
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"文件不存在：{file_path}")

    suffix = path.suffix.lower()

    if suffix in [".smi", ".txt"]:
        return read_smi_file(file_path)
    elif suffix == ".csv":
        return read_csv_file(file_path)
    elif suffix == ".json":
        return read_json_file(file_path)
    else:
        raise ValueError(f"不支持的文件格式：{suffix}")


def read_smi_file(file_path: str) -> List[Dict[str, str]]:
    """读取 SMILES 文件"""
    compounds = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            parts = line.split()
            if len(parts) >= 1:
                smiles = parts[0]
                name = " ".join(parts[1:]) if len(parts) > 1 else f"Compound_{line_num}"
                compounds.append({"smiles": smiles, "name": name})

    return compounds


def read_csv_file(file_path: str) -> List[Dict[str, str]]:
    """读取 CSV 文件"""
    compounds = []

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            smiles = None
            for col in ["smiles", "SMILES", "Smiles", "structure", "Structure"]:
                if col in row and row[col]:
                    smiles = row[col]
                    break

            if not smiles:
                continue

            name = None
            for col in ["name", "Name", "compound", "Compound", "id", "ID"]:
                if col in row and row[col]:
                    name = row[col]
                    break

            if not name:
                name = f"Compound_{len(compounds) + 1}"

            compounds.append({"smiles": smiles, "name": name})

    return compounds


def read_json_file(file_path: str) -> List[Dict[str, str]]:
    """读取 JSON 文件"""
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        if "compounds" in data:
            return data["compounds"]

        if "results" in data:
            out = []
            for item in data["results"]:
                smiles = item.get("smiles")
                name = item.get("name", "Unknown")
                if smiles:
                    out.append({"smiles": smiles, "name": name})
            return out

    raise ValueError("JSON 格式不正确，应为列表或包含 'compounds'/'results' 键的字典")


def write_results(results: Dict[str, Any], output_file: str, format: str = "json"):
    """
    写入预测结果到文件

    Args:
        results: 汇总结果字典
        output_file: 输出文件路径
        format: 输出格式 (json/csv/txt)
    """
    path = Path(output_file)
    path.parent.mkdir(parents=True, exist_ok=True)

    suffix = path.suffix.lower()
    if suffix:
        format = suffix[1:]

    if format == "json":
        write_json_results(results, output_file)
    elif format == "csv":
        write_csv_results(results, output_file)
    elif format == "txt":
        write_txt_results(results, output_file)
    else:
        raise ValueError(f"不支持的输出格式：{format}")


def write_json_results(results: Dict[str, Any], output_file: str):
    """写入 JSON 格式结果"""
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


def _extract_result_fields(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    统一提取 custom / unipka 两类结果的核心字段
    """
    result_block = result.get("results", {}) or {}

    strongest_acidic = result_block.get("strongest_acidic_pka")
    strongest_basic = result_block.get("strongest_basic_pka")

    # 老版 unipka 字段（兼容）
    dominant_deprotonation = result_block.get("dominant_deprotonation_pka")
    dominant_protonation = result_block.get("dominant_protonation_pka")

    # 新版 unipka 字段
    dominant_cation_to_neutral = result_block.get("dominant_cation_to_neutral_pka")
    dominant_neutral_to_anion = result_block.get("dominant_neutral_to_anion_pka")

    # 显示优先级：
    # custom -> strongest_xxx
    # unipka 新版 -> cation_to_neutral / neutral_to_anion
    # unipka 老版 -> deprotonation / protonation
    display_cation_to_neutral = (
        dominant_cation_to_neutral
        if dominant_cation_to_neutral is not None
        else dominant_protonation
    )
    display_neutral_to_anion = (
        dominant_neutral_to_anion
        if dominant_neutral_to_anion is not None
        else dominant_deprotonation
        if dominant_deprotonation is not None
        else strongest_acidic
    )

    return {
        "strongest_acidic_pka": strongest_acidic,
        "strongest_basic_pka": strongest_basic,
        "dominant_deprotonation_pka": dominant_deprotonation,
        "dominant_protonation_pka": dominant_protonation,
        "dominant_cation_to_neutral_pka": dominant_cation_to_neutral,
        "dominant_neutral_to_anion_pka": dominant_neutral_to_anion,
        "display_cation_to_neutral_pka": display_cation_to_neutral,
        "display_neutral_to_anion_pka": display_neutral_to_anion,
        "all_predictions": result_block.get("all_predictions", []),
    }


def _flatten_result_for_csv(result: Dict[str, Any]) -> Dict[str, Any]:
    fields = _extract_result_fields(result)

    flat = {
        "name": result.get("name"),
        "smiles": result.get("smiles"),
        "status": result.get("status"),
        "backend_used": result.get("backend_used"),
        "method": result.get("method"),
        "error": result.get("error"),
        "strongest_acidic_pka": fields["strongest_acidic_pka"],
        "strongest_basic_pka": fields["strongest_basic_pka"],
        "dominant_deprotonation_pka": fields["dominant_deprotonation_pka"],
        "dominant_protonation_pka": fields["dominant_protonation_pka"],
        "display_neutral_to_anion_pka": fields["display_neutral_to_anion_pka"],
        "display_cation_to_neutral_pka": fields["display_cation_to_neutral_pka"],
        "dominant_cation_to_neutral_pka": fields["dominant_cation_to_neutral_pka"],
        "dominant_neutral_to_anion_pka": fields["dominant_neutral_to_anion_pka"],
    }

    descriptors = result.get("descriptors", {}) or {}
    flat["formula"] = descriptors.get("formula")
    flat["molecular_weight"] = descriptors.get("molecular_weight")
    flat["logp"] = descriptors.get("logp")
    flat["hbd"] = descriptors.get("hbd")
    flat["hba"] = descriptors.get("hba")
    flat["rotatable_bonds"] = descriptors.get("rotatable_bonds")
    flat["tpsa"] = descriptors.get("tpsa")

    fg = result.get("functional_groups", {}) or {}
    if isinstance(fg, dict):
        flat["acidic_groups"] = ";".join(fg.get("acidic", [])) if fg.get("acidic") else ""
        flat["basic_groups"] = ";".join(fg.get("basic", [])) if fg.get("basic") else ""
    else:
        flat["acidic_groups"] = ""
        flat["basic_groups"] = ""

    all_predictions = fields["all_predictions"]
    if all_predictions:
        flat["prediction_count"] = len(all_predictions)
        flat["prediction_labels"] = ";".join(
            str(p.get("label", p.get("group", ""))) for p in all_predictions
        )
    else:
        flat["prediction_count"] = 0
        flat["prediction_labels"] = ""

    return flat


def write_csv_results(summary: Dict[str, Any], output_file: str):
    """写入 CSV 格式结果"""
    results = summary.get("results", [])
    if not results:
        return

    flat_results = [_flatten_result_for_csv(r) for r in results]

    field_order = [
        "name",
        "smiles",
        "status",
        "backend_used",
        "method",
        "display_neutral_to_anion_pka",
        "display_cation_to_neutral_pka",
        "dominant_neutral_to_anion_pka",
        "dominant_cation_to_neutral_pka",
        "strongest_acidic_pka",
        "strongest_basic_pka",
        "formula",
        "molecular_weight",
        "logp",
        "hbd",
        "hba",
        "rotatable_bonds",
        "tpsa",
        "acidic_groups",
        "basic_groups",
        "prediction_count",
        "prediction_labels",
        "error",
    ]

    with open(output_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=field_order, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flat_results)


def write_txt_results(summary: Dict[str, Any], output_file: str):
    """写入文本格式结果"""
    results = summary.get("results", [])

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("pKa Prediction Results\n")
        f.write("=" * 80 + "\n")
        f.write(f"status: {summary.get('status')}\n")
        f.write(f"backend_used: {summary.get('backend_used')}\n")
        f.write(f"total: {summary.get('total')}\n")
        f.write(f"success: {summary.get('success')}\n")
        f.write(f"error: {summary.get('error')}\n")
        f.write("=" * 80 + "\n\n")

        for i, result in enumerate(results, 1):
            f.write(f"[{i}] {format_pka_result(result, verbose=True)}\n")
            f.write("-" * 80 + "\n")


def format_prediction_lines(result: Dict[str, Any]) -> str:
    """
    格式化 all_predictions 为简洁文本
    """
    fields = _extract_result_fields(result)
    predictions = fields["all_predictions"]

    if not predictions:
        return ""

    lines = []
    for pred in predictions:
        pka = pred.get("pka", "N/A")
        label = pred.get("label")
        direction = pred.get("direction")
        group = pred.get("group")
        ptype = pred.get("type")

        if label:
            lines.append(f"{label}: pKa={pka} ({direction})")
        elif group:
            lines.append(f"{group}: pKa={pka} ({ptype})")
        else:
            lines.append(f"pKa={pka}")

    return " | ".join(lines)


def format_pka_result(result: Dict[str, Any], verbose: bool = False) -> str:
    """
    格式化单个 pKa 结果
    """
    name = result.get("name", "Unknown")
    smiles = result.get("smiles", "")
    status = result.get("status", "unknown")
    backend = result.get("backend_used", "unknown")

    if status != "success":
        return f"{name}: ERROR - {result.get('error', 'unknown error')}"

    fields = _extract_result_fields(result)
    neutral_to_anion = fields["display_neutral_to_anion_pka"]
    cation_to_neutral = fields["display_cation_to_neutral_pka"]

    output = f"{name}: neutral_to_anion_pKa = {neutral_to_anion}, cation_to_neutral_pKa = {cation_to_neutral} [{backend}]"

    if verbose:
        if result.get("method"):
            output += f" [方法：{result['method']}]"

        fg = result.get("functional_groups")
        if isinstance(fg, dict):
            acidic_groups = ", ".join(fg.get("acidic", [])) if fg.get("acidic") else "无"
            basic_groups = ", ".join(fg.get("basic", [])) if fg.get("basic") else "无"
            output += f" [酸性基团：{acidic_groups}] [碱性基团：{basic_groups}]"

        pred_line = format_prediction_lines(result)
        if pred_line:
            output += f" [预测明细：{pred_line}]"

        if smiles:
            output += f" [SMILES: {smiles}]"

    return output


def print_results(results: List[Dict[str, Any]], verbose: bool = False):
    """
    打印结果到控制台
    """
    print(f"\n{'=' * 60}")
    print("pKa 预测结果")
    print(f"{'=' * 60}\n")

    for i, result in enumerate(results, 1):
        print(f"[{i}] {format_pka_result(result, verbose)}")

    print(f"\n{'=' * 60}")
    print(f"总计：{len(results)} 个化合物")
    print(f"{'=' * 60}\n")


def create_output_directory(output_path: str) -> Path:
    """
    创建输出目录（如果不存在）
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path