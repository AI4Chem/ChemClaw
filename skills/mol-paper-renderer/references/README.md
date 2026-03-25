# Molecular Paper Renderer

论文级分子渲染工具，基于 **xyzrender**。

## 快速开始

### 安装依赖

```bash
# 基础安装
pip install xyzrender --break-system-packages

# 完整功能（推荐）
pip install 'xyzrender[all]' --break-system-packages
```

### 使用示例

```bash
# 从 SMILES 生成
python3 scripts/mol_paper_renderer.py -s "CCO" -o ethanol.svg

# 从文件生成
python3 scripts/mol_paper_renderer.py -i molecule.xyz -o output.png

# 过渡态
python3 scripts/mol_paper_renderer.py -i ts.out --ts -o ts.svg

# 旋转 GIF
python3 scripts/mol_paper_renderer.py -i molecule.xyz --gif-rot -o rotation.gif

# 使用包装脚本（直接调用 xyzrender）
xyzrender --smi "CCO" --hy -o ethanol.svg
```

## 输出目录

默认输出：`~/.openclaw/media/mol-paper-renderer/`

## 文档

详见 `SKILL.md` 或 https://xyzrender.readthedocs.io
