#!/usr/bin/env python3
"""
pKa 预测工具

支持多种后端进行 pKa 预测:
- UniPKA: 基于 Bohrium notebook 单文件权重路线
- Custom: 自定义规则和模型
- Auto: 优先 UniPKA，失败后回退 Custom
"""

import argparse
import json
import os
import sys
from typing import List, Dict, Optional, Any

# 添加脚本目录到路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

from utils.io_utils import read_smiles_file, write_results
from utils.mol_utils import check_rdkit


def check_backend_available(backend: str) -> bool:
    """
    按需检查后端是否可导入，避免 custom 模式被 unipka 依赖拖死
    """
    try:
        if backend == "unipka":
            from backends.unipka_backend import predict_pka_unipka, UniPKABackend  # noqa: F401
        elif backend == "custom":
            from backends.custom_backend import predict_pka_custom, CustomBackend  # noqa: F401
        elif backend == "auto":
            pass
        return True
    except ImportError as e:
        print(f"错误：无法导入 {backend} 后端模块：{e}", file=sys.stderr)
        return False


def decide_backend(args) -> str:
    """自动选择后端"""
    if args.backend != "auto":
        return args.backend

    # auto 模式：优先 UniPKA（只要有模型文件就走 unipka）
    if args.model:
        return "unipka"

    return "custom"


def predict_single(
    smiles: str,
    name: str,
    backend: str,
    config_path: Optional[str] = None,
    model_path: Optional[str] = None,
    template_file: Optional[str] = None,
    batch_size: int = 32,
    remove_hs: bool = False,
    use_gpu: bool = True,
    head_name: str = "chembl_all",
    maxiter: int = 10,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    预测单个化合物的 pKa
    """
    if backend == "unipka":
        from backends.unipka_backend import predict_pka_unipka
        return predict_pka_unipka(
            smiles=smiles,
            name=name,
            model_path=model_path,
            template_file=template_file,
            batch_size=batch_size,
            remove_hs=remove_hs,
            use_gpu=use_gpu,
            head_name=head_name,
            maxiter=maxiter,
        )

    elif backend == "custom":
        from backends.custom_backend import predict_pka_custom
        return predict_pka_custom(
            smiles=smiles,
            name=name,
            config_path=config_path,
            model_path=model_path,
        )

    else:
        raise ValueError(f"未知的后端类型：{backend}")


def predict_batch(
    compounds: List[Dict[str, Any]],
    backend: str,
    config_path: Optional[str] = None,
    model_path: Optional[str] = None,
    template_file: Optional[str] = None,
    batch_size: int = 32,
    remove_hs: bool = False,
    use_gpu: bool = True,
    head_name: str = "chembl_all",
    maxiter: int = 10,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    批量预测
    """
    if backend == "unipka":
        from backends.unipka_backend import UniPKABackend
        predictor = UniPKABackend(
            model_path=model_path,
            template_file=template_file,
            batch_size=batch_size,
            remove_hs=remove_hs,
            use_gpu=use_gpu,
            head_name=head_name,
            maxiter=maxiter,
        )
        return predictor.batch_predict(compounds)

    elif backend == "custom":
        from backends.custom_backend import CustomBackend
        predictor = CustomBackend(config_path=config_path, model_path=model_path)
        return predictor.batch_predict(compounds)

    else:
        raise ValueError(f"未知的后端类型：{backend}")


def summarize_results(results: List[Dict[str, Any]], backend_used: str) -> Dict[str, Any]:
    total = len(results)
    success = sum(1 for r in results if r.get("status") == "success")
    error = total - success
    return {
        "status": "completed" if error == 0 else "partial_success",
        "backend_used": backend_used,
        "total": total,
        "success": success,
        "error": error,
        "results": results,
    }


def main():
    parser = argparse.ArgumentParser(
        description="pKa 预测工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # custom 后端
  %(prog)s --smiles "CC(=O)O" --name "乙酸" --backend custom

  # UniPKA 单文件权重后端（使用默认模型和模板）
  %(prog)s --smiles "CC(=O)O" --name "乙酸" --backend unipka

  # UniPKA 单文件权重后端（显式指定模型和模板）
  %(prog)s --smiles "CC(=O)O" --name "乙酸" --backend unipka \\
      --model "/home/administratorlulaiao/.openclaw/workspace/skills/pka-predictor/assets/Uni-pKa/uni-pka-ckpt_v2/t_dwar_v_novartis_a_b.pt" \\
      --template "/home/administratorlulaiao/.openclaw/workspace/skills/pka-predictor/assets/Uni-pKa/uni-pka-ckpt_v2/smarts_pattern.tsv"

  # 批量预测
  %(prog)s --input compounds.smi --output results.json --backend custom
        """,
    )

    # 输入
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--smiles", "-s", help="单个化合物的 SMILES")
    input_group.add_argument("--input", "-i", help="输入文件路径 (.smi, .csv, .json, .txt)")

    parser.add_argument("--name", "-n", default="Unknown", help="化合物名称（单个化合物时使用）")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--format", "-f", choices=["json", "csv", "txt"], default="json", help="输出格式")

    # 后端
    parser.add_argument(
        "--backend", "-b",
        choices=["auto", "unipka", "custom"],
        default="custom",
        help="预测后端（默认：custom）"
    )

    # custom 参数
    parser.add_argument("--config", "-c", help="custom 后端配置文件")

    # 通用 / UniPKA 参数
    parser.add_argument(
        "--model", "-m",
        help="模型文件路径。对于 unipka，为单文件权重 .pt；对于 custom，为自定义模型文件"
    )
    parser.add_argument(
        "--template", "-t",
        help="UniPKA 模板文件路径（如 smarts_pattern.tsv 或 simple_smarts_pattern.tsv）"
    )
    parser.add_argument(
        "--head-name",
        default="chembl_all",
        help="UniPKA 单权重模型的 classification head 名称（默认：chembl_all）"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="推理 batch size（默认：32）"
    )
    parser.add_argument(
        "--maxiter",
        type=int,
        default=10,
        help="UniPKA 微观态枚举最大迭代次数（默认：10）"
    )
    parser.add_argument(
        "--remove-hs",
        action="store_true",
        help="是否在 UniPKA 前处理中去除氢原子"
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="强制使用 CPU（默认如果可用则使用 GPU）"
    )

    # 其他
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--quiet", "-q", action="store_true", help="安静模式")

    args = parser.parse_args()

    # RDKit 检查
    try:
        check_rdkit()
    except ImportError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)

    selected_backend = decide_backend(args)

    if not check_backend_available(selected_backend):
        sys.exit(1)

    try:
        use_gpu = not args.cpu

        if args.smiles:
            result = predict_single(
                smiles=args.smiles,
                name=args.name,
                backend=selected_backend,
                config_path=args.config,
                model_path=args.model,
                template_file=args.template,
                batch_size=args.batch_size,
                remove_hs=args.remove_hs,
                use_gpu=use_gpu,
                head_name=args.head_name,
                maxiter=args.maxiter,
                verbose=args.verbose,
            )
            results = [result]

        else:
            compounds = read_smiles_file(args.input)
            results = predict_batch(
                compounds=compounds,
                backend=selected_backend,
                config_path=args.config,
                model_path=args.model,
                template_file=args.template,
                batch_size=args.batch_size,
                remove_hs=args.remove_hs,
                use_gpu=use_gpu,
                head_name=args.head_name,
                maxiter=args.maxiter,
                verbose=args.verbose,
            )

        summary = summarize_results(results, selected_backend)

        if args.output:
            write_results(summary, args.output, args.format)
            if not args.quiet:
                print(f"结果已保存到：{args.output}")
        else:
            print(json.dumps(summary, indent=2, ensure_ascii=False))

        if summary["error"] > 0:
            sys.exit(2)

    except FileNotFoundError as e:
        print(f"错误：{e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"错误：{e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()