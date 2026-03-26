#!/bin/bash
# pKa Predictor 模型下载脚本
# 用于自动下载 Uni-pKa 模型权重和模板文件

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODEL_DIR="${SCRIPT_DIR}/../assets/Uni-pKa/uni-pka-ckpt_v2"

echo "🔧 pKa Predictor - 模型下载脚本"
echo "================================"
echo ""

# 检查 huggingface_hub 是否安装
if ! command -v hf &> /dev/null; then
    echo "⚠️  检测到 huggingface_hub 未安装，正在安装..."
    # 尝试使用 --break-system-packages 标志（适用于 externally-managed Python 环境）
    pip install huggingface_hub --break-system-packages 2>/dev/null || \
    pip install huggingface_hub --user 2>/dev/null || \
    {
        echo "❌ pip 安装失败，请手动运行以下命令："
        echo "   python3 -m venv .venv && source .venv/bin/activate && pip install huggingface_hub"
        exit 1
    }
    echo "✓ huggingface_hub 安装完成"
fi

# 创建模型目录
echo "📁 创建模型目录：${MODEL_DIR}"
mkdir -p "${MODEL_DIR}"

# 下载文件列表
FILES=(
    "t_dwar_v_novartis_a_b.pt"
    "smarts_pattern.tsv"
    "simple_smarts_pattern.tsv"
)

echo ""
echo "📥 开始下载模型文件..."
echo ""

for FILE in "${FILES[@]}"; do
    if [ -f "${MODEL_DIR}/${FILE}" ]; then
        echo "✓ 已存在：${FILE}"
    else
        echo "⬇️  下载：${FILE}"
        hf download Lai-ao/uni-pka-ckpt_v2 "${FILE}" \
            --repo-type model \
            --local-dir "${MODEL_DIR}"
        echo "✓ 下载完成：${FILE}"
    fi
done

echo ""
echo "================================"
echo "✅ 模型下载完成！"
echo ""
echo "模型文件位置：${MODEL_DIR}"
ls -lh "${MODEL_DIR}"
echo ""
echo "现在可以运行："
echo "  ./run_with_venv.sh --smiles \"CC(=O)O\" --name \"乙酸\" --backend unipka --cpu"
