# Molecular 3D Viewer

分子 3D 结构可视化器 - 生成可交互的 3D 分子网页和静态 3D 图片。

## 功能特点

- 🧪 **SMILES → 3D 分子** - 从 SMILES 生成优化的 3D 结构
- 📝 **IUPAC 名称支持** - 自动通过 OPSIN 转换名称
- 📁 **分子文件支持** - SDF、MOL、PDB 格式
- 🌐 **可交互 HTML** - WebGL 网页，支持鼠标旋转、缩放
- 🖼️ **静态 3D 图片** - PNG/SVG 格式
- 🎨 **多种渲染样式** - 棍状、球棍、空间填充、表面
- 🔬 **聚合物支持** - 正确处理聚合物结构
- 📦 **批量生成** - 支持多个分子同时处理

## 快速开始

### 安装依赖

```bash
pip install rdkit requests numpy
```

### 基本使用

```bash
# 生成可交互 3D 网页
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol.html --interactive

# 从名称生成 3D 结构
python3 scripts/mol_3d_viewer.py --name "caffeine" --output caffeine.html --interactive

# 生成静态 3D 图片
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol_3d.png
```

### 聚合物示例

```bash
# 聚乙烯
python3 scripts/mol_3d_viewer.py --smiles "*CC*" --output pe_3d.html --interactive

# 聚环氧乙烷
python3 scripts/mol_3d_viewer.py --smiles "*OCC*" --output peo_3d.html --interactive

# 从聚合物名称
python3 scripts/mol_3d_viewer.py --name "poly[oxy(1-methylethylene)]" --output ppo_3d.html --interactive
```

## 输出示例

### 可交互 HTML

生成的 HTML 网页支持：
- 🖱️ 鼠标旋转、缩放、平移
- 🎨 多种显示模式切换
- 🏷️ 原子标签显示/隐藏
- 🔄 自动旋转
- 📸 截图保存

### 静态图片

- PNG 格式 - 适合网页展示
- SVG 格式 - 适合出版物

## 与其他化学技能配合

### 与 iupac_to_smiles 配合

```bash
# 1. 转换名称为 SMILES
python3 ../iupac-to-smiles/scripts/iupac_to_smiles.py --name "poly[oxy(1-methylethylene)]" -o result.json

# 2. 生成 3D 可交互网页
SMILES=$(cat result.json | jq -r '.results[0].polymer_smiles')
python3 scripts/mol_3d_viewer.py --smiles "$SMILES" --output ppo_3d.html --interactive
```

### 与 mol_visualizer 配合

```bash
# 2D + 3D 一起生成
python3 ../mol-visualizer/scripts/mol_visualizer.py --smiles "CCO" --output ethanol_2d.png
python3 scripts/mol_3d_viewer.py --smiles "CCO" --output ethanol_3d.html --interactive
```

## 技术细节

### 3D 优化流程

1. 从 SMILES 生成 2D 结构
2. 添加氢原子
3. 使用 ETKDG 算法生成 3D 坐标
4. MMFF94 力场优化（最多 200 步）
5. 渲染输出

### 渲染引擎

- **HTML**: 3Dmol.js (WebGL)
- **图片**: RDKit Cairo 渲染

## 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--smiles, -s` | SMILES 字符串 | - |
| `--name, -n` | IUPAC 名称 | - |
| `--input, -i` | 输入分子文件 | - |
| `--output, -o` | 输出文件路径 | 自动生成 |
| `--interactive, -I` | 生成可交互 HTML | false |
| `--style, -S` | 渲染样式 | stick |
| `--width, -W` | 宽度（像素） | 800 |
| `--height, -H` | 高度（像素） | 600 |

## 渲染样式

- `stick` - 棍状模型
- `sphere` - 空间填充模型
- `ball_stick` - 球棍模型
- `surface` - 分子表面
- `line` - 线状模型

## 支持的分子文件格式

- SDF (`.sdf`, `.sd`)
- MOL (`.mol`)
- PDB (`.pdb`)
- XYZ (`.xyz`)

## 输出目录

默认输出目录：`~/.openclaw/media/mol-3d-viewer/`

## 性能参考

| 分子大小 | 3D 生成时间 |
|----------|------------|
| 小分子 (<20 原子) | <0.5s |
| 中等分子 (20-50 原子) | 0.5-2s |
| 大分子 (50-100 原子) | 2-5s |
| 聚合物/蛋白 (>100 原子) | 5-20s |

## 故障排除

### 3D 生成失败

- 检查 SMILES 格式是否正确
- 尝试简化分子结构
- 使用 `--force-field uff` 切换力场

### 名称无法识别

- OPSIN 可能不支持某些复杂名称
- 直接使用 SMILES 输入

### HTML 无法打开

- 确保浏览器支持 WebGL
- 检查网络连接（需要加载 3Dmol.js CDN）

## License

MIT License
