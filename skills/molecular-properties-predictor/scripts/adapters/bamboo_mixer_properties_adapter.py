#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict

TARGET_PROPERTIES = [
    "Tm",
    "bp",
    "nD",
    "nD_liquid",
    "pka_a",
    "pka_b",
    "dc",
    "ST",
    "density",
    "vis",
    "vapP",
]


def _abspath_keep_symlink(path_str: str) -> Path:
    return Path(os.path.abspath(os.path.expanduser(path_str)))


def _resolve_bamboo_repo() -> Path:
    repo_env = os.environ.get("BAMBOO_MIXER_REPO", "assets/bamboo_mixer")
    repo_path = _abspath_keep_symlink(repo_env)
    if not repo_path.exists():
        raise FileNotFoundError(f"Bamboo-Mixer repo not found: {repo_path}")
    return repo_path


def _resolve_bamboo_python(repo_path: Path) -> str:
    py_env = os.environ.get("BAMBOO_MIXER_PYTHON")
    if py_env:
        py_path = _abspath_keep_symlink(py_env)
        if not py_path.exists():
            raise FileNotFoundError(f"BAMBOO_MIXER_PYTHON not found: {py_path}")
        return str(py_path)

    default_py = repo_path / ".venv" / "bin" / "python"
    if default_py.exists():
        return str(default_py)

    raise FileNotFoundError("Cannot find Bamboo-Mixer Python interpreter.")


def _resolve_mono_ckpt(repo_path: Path) -> Path:
    candidates = [
        repo_path / "hf_bamboo_mixer" / "ckpts" / "mono" / "optimal.pt",
        repo_path / "ckpts" / "mono" / "optimal.pt",
    ]

    ckpt_env = os.environ.get("BAMBOO_MIXER_MONO_CKPT")
    if ckpt_env:
        ckpt_path = _abspath_keep_symlink(ckpt_env)
        if ckpt_path.exists():
            return ckpt_path
        raise FileNotFoundError(f"BAMBOO_MIXER_MONO_CKPT not found: {ckpt_path}")

    for path in candidates:
        if path.exists():
            return path

    raise FileNotFoundError("Mono checkpoint not found.")


def _run_command(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    existing_pythonpath = env.get("PYTHONPATH", "")
    repo_pythonpath = str(cwd)

    if existing_pythonpath:
        env["PYTHONPATH"] = repo_pythonpath + os.pathsep + existing_pythonpath
    else:
        env["PYTHONPATH"] = repo_pythonpath

    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def _build_prepare_config(data_dir: Path) -> str:
    json_path = data_dir / "data.json"
    save_dir = data_dir

    return f"""json_path: "{json_path}"
save_dir: "{save_dir}"

data_cls: MonoData
key_map:
  temperature: temperature
"""


def _build_test_config(data_dir: Path, output_dir: Path, ckpt_path: Path) -> str:
    save_dir = data_dir
    output_path = output_dir / "output_mono.json"

    return f"""# auto-generated for molecular-properties-predictor bamboo adapter
ckpt_path: "{ckpt_path}"
save_dir: "{save_dir}"
output_path: "{output_path}"
data_cls: "MonoData"
key_map:
  temperature: "temperature"

model:
  graph_block:
    feature_layer:
      atom_embedding_dim: 16
      node_mlp_dims: [32, 32, 2]
      edge_mlp_dims: [32, 32, 2]
      act: gelu
    gnn_layer:
      gnn_type: EGT
      gnn_dims: [32, 32, 3]
      jk: cat
      act: gelu
      heads: 4
      at_channels: 8
      ffn_dims: [32, 2]
  readout_block:
    input_dim: 64
    hidden_dims: [256, 128, 16]
    output_dim: 1
"""


def predict_properties(smiles: str, temperature_celsius: float) -> Dict[str, Any]:
    try:
        repo_path = _resolve_bamboo_repo()
        bamboo_python = _resolve_bamboo_python(repo_path)
        ckpt_path = _resolve_mono_ckpt(repo_path)
    except Exception as exc:
        return {
            "success": False,
            "error_message": f"Adapter path resolution failed: {exc}",
        }

    with tempfile.TemporaryDirectory(prefix="bamboo_mono_props_") as tmpdir:
        tmpdir_path = Path(tmpdir)
        data_dir = tmpdir_path / "input_data"
        output_dir = tmpdir_path / "output"
        prepare_conf = tmpdir_path / "mono_prepare_config.yaml"
        test_conf = tmpdir_path / "mono_test_config.yaml"

        data_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        input_records = [
            {
                "name": "query_molecule",
                "smiles": smiles,
                "temperature": float(temperature_celsius),
            }
        ]
        _write_json(data_dir / "data.json", input_records)
        _write_text(prepare_conf, _build_prepare_config(data_dir))
        _write_text(test_conf, _build_test_config(data_dir, output_dir, ckpt_path))

        prepare_cmd = [
            bamboo_python,
            "scripts/prepare_data/prepare_data.py",
            "--conf",
            str(prepare_conf),
            "--data_type",
            "mono",
        ]
        prep = _run_command(prepare_cmd, cwd=repo_path)
        if prep.returncode != 0:
            return {
                "success": False,
                "error_message": "Bamboo prepare_data failed.",
                "details": {
                    "stdout": prep.stdout,
                    "stderr": prep.stderr,
                    "command": " ".join(prepare_cmd),
                    "python_used": bamboo_python,
                    "repo_path": str(repo_path),
                },
            }

        mono_cmd = [
            bamboo_python,
            "scripts/test_results/mono.py",
            "--conf",
            str(test_conf),
        ]
        infer = _run_command(mono_cmd, cwd=repo_path)
        if infer.returncode != 0:
            return {
                "success": False,
                "error_message": "Bamboo mono inference failed.",
                "details": {
                    "stdout": infer.stdout,
                    "stderr": infer.stderr,
                    "command": " ".join(mono_cmd),
                    "python_used": bamboo_python,
                    "repo_path": str(repo_path),
                },
            }

        output_json = output_dir / "output_mono.json"
        if not output_json.exists():
            return {
                "success": False,
                "error_message": f"Expected output not found: {output_json}",
                "details": {
                    "prepare_stdout": prep.stdout,
                    "prepare_stderr": prep.stderr,
                    "infer_stdout": infer.stdout,
                    "infer_stderr": infer.stderr,
                    "python_used": bamboo_python,
                    "repo_path": str(repo_path),
                },
            }

        with open(output_json, "r", encoding="utf-8") as f:
            payload = json.load(f)

        if not isinstance(payload, list) or len(payload) == 0:
            return {
                "success": False,
                "error_message": "Unexpected Bamboo output format: output_mono.json is empty or not a list.",
                "raw_output": payload,
                "python_used": bamboo_python,
            }

        first = payload[0]
        properties = {}
        for key in TARGET_PROPERTIES:
            if key not in first:
                return {
                    "success": False,
                    "error_message": f"Bamboo output does not contain '{key}'.",
                    "raw_output": first,
                    "python_used": bamboo_python,
                }
            properties[key] = float(first[key])

        return {
            "success": True,
            "properties": properties,
            "model_source": "bamboo_mixer_mono_optimal_pt",
            "canonical_smiles": first.get("smiles", smiles),
            "raw_output_record": first,
            "python_used": bamboo_python,
        }
