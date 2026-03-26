#!/usr/bin/env bash
set -euo pipefail

# 用法：
#   在 skills/molecular-properties-predictor 目录下执行：
#   bash scripts/setup_bamboo_env.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
BAMBOO_DIR="${SKILL_DIR}/assets/bamboo_mixer"

echo "[INFO] skill dir:   ${SKILL_DIR}"
echo "[INFO] bamboo dir:  ${BAMBOO_DIR}"

if [[ ! -d "${BAMBOO_DIR}" ]]; then
  echo "[ERROR] Cannot find bamboo_mixer directory: ${BAMBOO_DIR}"
  exit 1
fi

# 选择 Python 3.11
if command -v python3.11 >/dev/null 2>&1; then
  PY311_BIN="$(command -v python3.11)"
elif [[ -x "${HOME}/.pyenv/versions/3.11.11/bin/python" ]]; then
  PY311_BIN="${HOME}/.pyenv/versions/3.11.11/bin/python"
else
  echo "[ERROR] Python 3.11 not found."
  echo "Please install python3.11 or pyenv 3.11.11 first."
  exit 1
fi

echo "[INFO] Using Python 3.11: ${PY311_BIN}"

cd "${BAMBOO_DIR}"

# 重建独立 venv
rm -rf .venv
"${PY311_BIN}" -m venv .venv
source .venv/bin/activate

python --version
which python

pip install --upgrade pip
pip install -r requirements.txt

# 针对较新 GPU（如 RTX 5070 / Blackwell）覆盖安装兼容版本
# 这一段不会自动判断显卡代际，直接统一覆盖为更稳的 cu128 方案
pip uninstall -y torch triton || true
pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cu128 \
  torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0

pip uninstall -y torch-geometric || true
pip install --no-cache-dir torch_geometric==2.7.0

echo "[INFO] Torch environment check:"
python -c "import torch; print('torch:', torch.__version__)"
python -c "import torch; print('cuda version:', torch.version.cuda)"
python -c "import torch; print('cuda available:', torch.cuda.is_available())"
python -c "import torch; print('device count:', torch.cuda.device_count())"

echo "[INFO] Bamboo environment setup completed."