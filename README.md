# ChemClaw

化学计算工具集 - 基于 OpenClaw 的化学类 Skill 集合

## 简介

ChemClaw 是一个开源的化学计算工具集，提供一系列基于 Python 的化学分子性质预测和结构优化工具。所有工具都设计为可独立使用，也可集成到 OpenClaw 框架中。

## 已实现的功能

| Skill | 功能 | 状态 |
|-------|------|------|
| [geometry_optimizer](skills/geometry_optimizer/) | 分子几何结构优化 (xTB) | ✅ 完成 |
| [viscosity_predictor](skills/viscosity_predictor/) | 液体黏度预测 | ✅ 完成 |
| [density_predictor](skills/density_predictor/) | 质量密度预测 | ✅ 完成 |
| [molecular_properties_predictor](skills/molecular_properties_predictor/) | 多物化性质预测 | ✅ 完成 |
| [pka_predictor](skills/pka_predictor/) | pKa 预测 | ✅ 完成 |
| [surface_tension_predictor](skills/surface_tension_predictor/) | 表面张力预测 | ✅ 完成 |
| [iupac_to_smiles](skills/iupac_to_smiles/) | IUPAC 名称转 SMILES | ✅ 完成 |
| [mol_visualizer](skills/mol_visualizer/) | 分子结构可视化 | ✅ 完成 |

## 快速开始

### 安装依赖

```bash
# 系统依赖 (以 Ubuntu 为例)
sudo apt install xtb

# Python 依赖
pip install rdkit
```

### 使用示例

```bash
<<<<<<< HEAD
# 进入 skill 目录
cd skills/geometry_optimizer

# 运行几何优化
python scripts/main_script.py --smiles "CCO" --name "乙醇" --output-dir ./results
=======
npx skills add AI4Chem/ChemClaw --skill mol_3d_viewer
>>>>>>> upstream/main
```

### 批量处理

```bash
# 准备输入文件
cat > input.json << 'EOF'
[
  {"name": "乙醇", "smiles": "CCO"},
  {"name": "水", "smiles": "O"}
]
EOF

# 批量运行
python scripts/main_script.py --input input.json --output output.json --output-dir ./results
```

<<<<<<< HEAD
## 目录结构

```
ChemClaw/
├── README.md                 # 本文件
├── LICENSE                   # 许可证
└── skills/                   # Skill 集合
    ├── geometry_optimizer/   # 几何优化
    ├── viscosity_predictor/  # 黏度预测
    ├── density_predictor/    # 密度预测
    └── ...
```

每个 skill 都是独立的工具包，包含：
- `SKILL.md` - 功能说明和使用文档
- `README.md` - 快速入门指南
- `INSTALL.md` - 安装说明
- `scripts/` - 可执行脚本
- `requirements.txt` - Python 依赖

## 系统要求

- Python 3.8+
- xTB 6.x (几何优化相关功能)
- RDKit (分子处理)

## 开发指南

### 添加新的 Skill
=======
## Contributing
>>>>>>> upstream/main

1. 在 `skills/` 目录下创建新的 skill 文件夹
2. 参考现有 skill 的文件结构
3. 实现 `scripts/main_script.py` 作为主入口
4. 编写 `SKILL.md` 说明文档

### 测试

每个 skill 都包含测试脚本：

```bash
cd skills/geometry_optimizer
python scripts/test_xtb_backend.py
```

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 参考资料

- [OpenClaw](https://github.com/openclaw/openclaw)
- [xTB](https://github.com/grimme-lab/xtb)
- [RDKit](https://www.rdkit.org/)
