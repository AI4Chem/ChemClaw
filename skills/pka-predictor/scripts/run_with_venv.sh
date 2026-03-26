#!/bin/bash
# pKa Predictor 运行脚本（使用虚拟环境）
# 用于 OpenClaw Skill 调用

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="${SCRIPT_DIR}/../.venv"

# 检查虚拟环境是否存在
if [ ! -d "$VENV_PATH" ]; then
    echo "错误：虚拟环境不存在：$VENV_PATH"
    echo "请先运行：python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# 激活虚拟环境并运行
source "${VENV_PATH}/bin/activate"
cd "${SCRIPT_DIR}"
python predict_pka.py "$@"
