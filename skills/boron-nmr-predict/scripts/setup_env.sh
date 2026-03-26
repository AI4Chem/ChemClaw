#!/usr/bin/env bash
set -euo pipefail

ENV_NAME="${1:-boron-nmr-predict}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

find_conda_sh() {
  if command -v conda >/dev/null 2>&1; then
    local conda_base
    conda_base="$(conda info --base 2>/dev/null || true)"
    if [ -n "$conda_base" ] && [ -f "$conda_base/etc/profile.d/conda.sh" ]; then
      printf '%s\n' "$conda_base/etc/profile.d/conda.sh"
      return 0
    fi
  fi

  if [ -n "${CONDA_EXE:-}" ]; then
    local conda_bin
    conda_bin="$(cd "$(dirname "$CONDA_EXE")" && pwd)"
    if [ -f "$conda_bin/../etc/profile.d/conda.sh" ]; then
      printf '%s\n' "$conda_bin/../etc/profile.d/conda.sh"
      return 0
    fi
  fi

  for candidate in \
    "$HOME/miniconda3/etc/profile.d/conda.sh" \
    "$HOME/anaconda3/etc/profile.d/conda.sh" \
    "$HOME/conda/etc/profile.d/conda.sh"; do
    if [ -f "$candidate" ]; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  return 1
}

CONDA_SH="$(find_conda_sh || true)"
if [ -z "$CONDA_SH" ]; then
  echo "[ERROR] conda not found. Make sure conda is installed and initialized in the shell, or activate a shell where 'conda' works before running this script." >&2
  echo "[TIP] Common locations checked: ~/miniconda3, ~/anaconda3, ~/conda" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$CONDA_SH"

if ! command -v conda >/dev/null 2>&1; then
  echo "[ERROR] conda initialization failed after sourcing: $CONDA_SH" >&2
  exit 1
fi

if conda env list | awk '{print $1}' | grep -qx "$ENV_NAME"; then
  echo "[INFO] Conda env '$ENV_NAME' already exists. Reusing it."
else
  echo "[INFO] Creating conda env '$ENV_NAME' with Python ${PYTHON_VERSION}..."
  conda create -n "$ENV_NAME" "python=${PYTHON_VERSION}" -y
fi

conda activate "$ENV_NAME"

python -m pip install --upgrade pip
python -m pip install -r "$SKILL_ROOT/requirements-core.txt"
python -m pip install -r "$SKILL_ROOT/requirements-pyg.txt"

echo "[OK] Environment ready: $ENV_NAME"
echo "[TIP] Activate with: conda activate $ENV_NAME"
