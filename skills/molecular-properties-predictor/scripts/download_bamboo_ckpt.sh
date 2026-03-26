#!/usr/bin/env bash
set -euo pipefail

# 用法：
#   在 skills/molecular-properties-predictor 目录下执行：
#   bash scripts/download_bamboo_ckpt.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BAMBOO_DIR="${SKILL_DIR}/assets/bamboo_mixer"
TARGET_DIR="${BAMBOO_DIR}/hf_bamboo_mixer"

echo "[INFO] skill dir:   ${SKILL_DIR}"
echo "[INFO] bamboo dir:  ${BAMBOO_DIR}"
echo "[INFO] target dir:  ${TARGET_DIR}"

if [[ ! -d "${BAMBOO_DIR}" ]]; then
  echo "[ERROR] Cannot find bamboo_mixer directory: ${BAMBOO_DIR}"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "[ERROR] git is required but not found."
  exit 1
fi

if ! command -v git-lfs >/dev/null 2>&1; then
  echo "[ERROR] git-lfs is required but not found."
  echo "On Ubuntu/WSL, run:"
  echo "  sudo apt update && sudo apt install -y git-lfs"
  echo "  git lfs install"
  exit 1
fi

git lfs install

cd "${BAMBOO_DIR}"

if [[ -d "${TARGET_DIR}" ]]; then
  echo "[INFO] Existing hf_bamboo_mixer directory found, removing it first..."
  rm -rf "${TARGET_DIR}"
fi

echo "[INFO] Cloning Bamboo-Mixer Hugging Face repository..."
git clone https://huggingface.co/ByteDance-Seed/bamboo_mixer "${TARGET_DIR}"

echo "[INFO] Checking mono checkpoint..."
if [[ -f "${TARGET_DIR}/ckpts/mono/optimal.pt" ]]; then
  echo "[INFO] Mono checkpoint found:"
  echo "       ${TARGET_DIR}/ckpts/mono/optimal.pt"
else
  echo "[ERROR] Mono checkpoint not found after clone."
  exit 1
fi

echo "[INFO] Bamboo checkpoint download completed."