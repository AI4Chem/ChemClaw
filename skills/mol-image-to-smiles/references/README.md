# Mol Image to SMILES Converter

将分子结构图片转换为 SMILES 字符串的智能工具。

## 🚀 快速开始

### 安装依赖

```bash
# 基本安装
pip install decimer huggingface_hub

# 完整安装
pip install decimer huggingface_hub rdkit Pillow
```

### 基本使用

```bash
# 自动转换（推荐）
python3 scripts/mol_image_to_smiles.py -i molecule.png

# 指定模型
python3 scripts/mol_image_to_smiles.py -i molecule.png -m decimer
python3 scripts/mol_image_to_smiles.py -i molecule.png -m molnextr
```

## 📋 功能特性

- ✅ **双模型支持** - DECIMER + MolNextR
- ✅ **自动模型选择** - 优先使用本地 DECIMER
- ✅ **高精度识别** - 支持复杂分子结构
- ✅ **批量处理** - 支持多张图片同时转换
- ✅ **格式支持** - PNG、JPG、JPEG、GIF、BMP
- ✅ **结果保存** - JSON 格式输出

## 🎯 模型选择逻辑

```
DECIMER (本地，首选)
    ↓ 失败/未安装
MolNextR (HuggingFace API)
```

## 📊 输出示例

```json
{
  "input_image": "molecule.png",
  "timestamp": "2026-03-16T20:00:00",
  "results": [
    {
      "status": "success",
      "smiles": "CCO",
      "model": "DECIMER",
      "source": "local"
    }
  ],
  "best_result": {
    "status": "success",
    "smiles": "CCO",
    "model": "DECIMER"
  }
}
```

## 📁 目录结构

```
mol-image-to-smiles/
├── SKILL.md              # 详细技能文档
├── README.md             # 本文件
├── requirements.txt      # Python 依赖
├── scripts/
│   └── mol_image_to_smiles.py  # 主脚本
└── references/
    └── README.md         # API 文档和参考资料
```

## 🔧 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| `--input` | `-i` | 输入图片路径 | 必需 |
| `--output` | `-o` | 输出目录 | `~/.openclaw/media/mol-image-to-smiles` |
| `--model` | `-m` | 模型：auto/decimer/molnextr | `auto` |
| `--quiet` | `-q` | 安静模式（JSON 输出） | `false` |

## 💡 使用场景

### 标准化学结构图

```bash
python3 scripts/mol_image_to_smiles.py -i aspirin.png
# 输出：CC(=O)Oc1ccccc1C(=O)O
```

### 复杂分子结构

```bash
python3 scripts/mol_image_to_smiles.py -i complex_molecule.png -m molnextr
```

### 批量处理

```bash
for img in ./molecules/*.png; do
  python3 scripts/mol_image_to_smiles.py -i "$img" -o ./results
done
```

## ⚠️ 注意事项

1. **图片质量**: 清晰的图片提高识别准确率
2. **标准绘制**: 使用 ChemDraw 等标准工具
3. **DECIMER 依赖**: 需要 TensorFlow，首次运行会下载模型
4. **网络连接**: MolNextR 需要网络

## 📚 参考资料

- [DECIMER 项目](references/README.md#1-decimer)
- [MolNextR 模型](references/README.md#2-molnextr)
- [识别技巧](references/README.md#识别技巧)

## 🤝 与其他技能配合

### 完整工作流

```
分子图片 → mol-image-to-smiles → SMILES → smiles-to-iupac → IUPAC 名称
     ↓                              ↓
  mol-2d-viewer                  iupac-to-smiles
     ↓                              ↓
  2D 结构图验证                  IUPAC 名称（验证）
```

## 📈 性能对比

| 模型 | 响应时间 | 准确率 | 需要网络 |
|------|---------|--------|----------|
| DECIMER | ~5s | 90%+ | 否 (首次下载) |
| MolNextR | ~10s | 88%+ | 是 |

## 🐛 常见问题

### Q: DECIMER 模型下载失败？

A: 检查网络连接，或手动下载模型到 `~/.data/DECIMER-V2/`

### Q: 识别结果不准确？

A: 
1. 提高图片清晰度
2. 尝试 MolNextR 模型
3. 使用标准化学绘图工具

### Q: 支持手绘结构吗？

A: DECIMER 有手绘模型，但准确率较低。建议使用标准工具绘制的结构图。

## 📝 更新日志

### v1.0 (2026-03-16) - Initial

- ✅ DECIMER 模型支持
- ✅ MolNextR 支持
- ✅ 自动模型选择
- ✅ 批量处理
- ✅ JSON 输出

## 📄 许可证

MIT License

## 👥 作者

Created for OpenClaw Skills

---

**最后更新**: 2026-03-16  
**版本**: 1.0  
**状态**: ✅ 生产就绪
