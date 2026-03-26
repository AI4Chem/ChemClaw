#!/usr/bin/env python3
import os
from pathlib import Path
from huggingface_hub import snapshot_download

REQUIRED_FILES = [
    'model_v3_fold_1.pth',
    'model_v3_fold_2.pth',
    'model_v3_fold_3.pth',
    'model_v3_fold_4.pth',
    'model_v3_fold_5.pth',
    'ml_feature_scaler.pkl',
]


DEFAULT_REPO_ID = 'SII-AI4Chem/boron-nmr-predict-model'


def default_model_dir() -> Path:
    return Path(os.environ.get('BORON_NMR_MODEL_DIR', '~/.cache/boron-nmr-predict/models')).expanduser()


def ensure_model_files() -> Path:
    repo_id = os.environ.get('BORON_NMR_MODEL_REPO', DEFAULT_REPO_ID).strip()
    model_dir = default_model_dir()
    model_dir.mkdir(parents=True, exist_ok=True)

    missing = [name for name in REQUIRED_FILES if not (model_dir / name).exists()]
    if not missing:
        return model_dir

    if not repo_id:
        raise SystemExit('Missing BORON_NMR_MODEL_REPO. Set it to your Hugging Face repo id, e.g. org/repo-name')

    snapshot_download(
        repo_id=repo_id,
        local_dir=str(model_dir),
        local_dir_use_symlinks=False,
        allow_patterns=REQUIRED_FILES,
    )

    missing_after = [name for name in REQUIRED_FILES if not (model_dir / name).exists()]
    if missing_after:
        raise SystemExit(f'Model download incomplete. Missing: {missing_after}')

    return model_dir


if __name__ == '__main__':
    print(str(ensure_model_files()))
