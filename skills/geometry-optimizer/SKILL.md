---
name: geometry-optimizer
description: 使用半经验方法 (xTB) 对分子三维结构进行几何优化，支持 SMILES 自动转 3D、XYZ 文件输入，输出优化后坐标、能量、收敛状态。
trigger: ["geometry optimization", "结构优化", "几何优化", "3D 优化", "optimize geometry", "xtb", "构象优化", "半经验优化", "分子结构预优化", "分子几何优化", "能量优化", "GFN-xTB"]
---

# Geometry Optimizer

`geometry-optimizer` 是一个用于 **分子三维几何结构优化** 的化学类 skill。  
它基于 **GFN-xTB 半经验量子化学方法**，对用户提供的分子初始结构进行快速、可落地的本地优化，输出优化后的坐标、能量、收敛状态等结果。

---

## 核心功能

- ✅ **SMILES → 3D → 优化**：自动从 SMILES 生成初始 3D 构象并进行 xTB 优化
- ✅ **XYZ 文件输入**：直接对已有 3D 坐标文件进行优化
- ✅ **GFN2-xTB 方法**：默认使用高精度的 GFN2-xTB 半经验方法
- ✅ **完整结果输出**：优化后坐标、最终能量、梯度、收敛状态、日志文件
- ✅ **批量处理**：支持 JSON 批量输入，多分子连续优化

---

## 适用场景

当用户有以下需求时，应调用本 skill：

| 用户需求 | 示例 |
|----------|------|
| 优化分子 3D 结构 | "帮我优化这个分子的 3D 结构" |
| SMILES 转 3D 并优化 | "把这个 SMILES 生成 3D 后优化" |
| xTB 几何优化 | "用 xTB 做一下 geometry optimization" |
| 获取优化后坐标 | "给我一个预优化后的 xyz 坐标" |
| 半经验快速优化 | "用半经验方法快速优化一下分子结构" |
| DFT 预优化 | "在做 DFT 前先用 xTB 预优化" |
| XYZ/SDF 结构优化 | "对这个 XYZ 结构做几何优化" |

---

## 不适用场景

以下情况**不应**调用本 skill：

| 场景 | 原因 | 建议 |
|------|------|------|
| 高精度 DFT / ab initio 优化 | xTB 是半经验方法，精度有限 | 使用 Gaussian、ORCA、Psi4 等 |
| 过渡态搜索、IRC、频率分析 | 当前不支持 | 使用专用量化软件 |
| 晶体/周期性体系优化 | xTB 不支持 PBC | 使用 VASP、Quantum ESPRESSO |
| 蛋白质/超大体系 | 计算成本高，可能需要特殊处理 | 使用分子力学或专用工具 |
| 发表级精确结果 | 半经验方法适合预优化/筛选 | 使用高精度方法复核 |

---

## 输入格式

### 1. SMILES（推荐）

```bash
python scripts/main_script.py --smiles "CCO" --name "乙醇"
```

- 自动使用 RDKit 生成初始 3D 构象
- 自动推断电荷和未成对电子数
- 适用于只有二维分子表达式的场景

### 2. XYZ 文件

```bash
python scripts/main_script.py --input-xyz molecule.xyz --output-dir ./results
```

- 直接使用已有 3D 坐标
- 适合从实验结构或其他软件导出的坐标

### 3. 批量 JSON 输入

```bash
python scripts/main_script.py --input input.json --output output.json --output-dir ./results
```

`input.json` 格式：

```json
[
  {"name": "乙醇", "smiles": "CCO"},
  {"name": "水", "smiles": "O"},
  {"name": "自定义", "input_xyz": "path/to/molecule.xyz"}
]
```

---

## 输出格式

### JSON 结果

```json
{
  "status": "completed",
  "backend_used": "xtb",
  "total": 1,
  "success": 1,
  "partial_success": 0,
  "error": 0,
  "results": [
    {
      "name": "乙醇",
      "input_type": "smiles",
      "smiles": "CCO",
      "canonical_smiles": "CCO",
      "status": "success",
      "backend_used": "xtb",
      "method": "gfn2",
      "charge": 0,
      "uhf": 0,
      "solvent": null,
      "converged": true,
      "energy_hartree": -11.394338789631,
      "energy_kcal_mol": -7150.050139542559,
      "final_gradient": 0.000195893782,
      "num_atoms": 9,
      "optimized_xyz_path": "./test_output/optimized.xyz",
      "log_path": "./test_output/xtbopt.log",
      "runtime_seconds": 0.26,
      "warnings": [],
      "message": "Geometry optimization completed. Converged."
    }
  ]
}
```

### 输出字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | string | `success` / `partial_success` / `error` |
| `converged` | boolean | 是否达到收敛标准 (梯度 < 0.001 Eh/a₀) |
| `energy_hartree` | float | 最终能量 (Hartree) |
| `energy_kcal_mol` | float | 最终能量 (kcal/mol) |
| `final_gradient` | float | 最终梯度范数 (Eh/a₀) |
| `num_atoms` | int | 原子数 |
| `optimized_xyz_path` | string | 优化后 XYZ 坐标文件路径 |
| `log_path` | string | xTB 日志文件路径 |
| `runtime_seconds` | float | 运行时间 (秒) |
| `warnings` | array | 警告信息列表 |

### XYZ 坐标文件

```xyz
9
Optimized with xTB gfn2, energy=-11.394338789631 Ha
C -0.915405  0.082880  0.018580
C  0.513691 -0.435657 -0.103334
O  1.452768  0.397316  0.535701
H -1.015673  1.046445 -0.479628
...
```

---

## 命令行参数

```bash
python scripts/main_script.py \
  --smiles "CCO" \
  --name "乙醇" \
  --method gfn2 \
  --charge 0 \
  --uhf 0 \
  --solvent water \
  --max-cycles 200 \
  --output-dir ./results \
  --output ./results/result.json
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--smiles` | SMILES 字符串 (与 `--input-xyz` 互斥) | - |
| `--input-xyz` | 输入 XYZ 文件路径 (与 `--smiles` 互斥) | - |
| `--input` | 批量输入 JSON 文件路径 | - |
| `--name` | 分子名称 | - |
| `--output` | 输出 JSON 文件路径 | - |
| `--output-dir` | 输出目录 (XYZ 和日志文件) | - |
| `--backend` | 后端 (`xtb`) | `xtb` |
| `--method` | xTB 方法 (`gfn2`/`gfn1`/`gfnff`) | `gfn2` |
| `--charge` | 分子电荷 | 自动推断 |
| `--uhf` | 未成对电子数 | 自动推断 |
| `--solvent` | 溶剂模型 (如 `water`, `ethanol`) | 无 |
| `--max-cycles` | 最大优化步数 | `200` |

---

## 方法选择

| 方法 | 适用场景 | 精度 | 速度 |
|------|----------|------|------|
| **GFN2-xTB** (默认) | 通用有机分子、主族元素 | 高 | 中等 |
| **GFN1-xTB** | 某些无机体系、过渡金属 | 中等 | 中等 |
| **GFN-FF** | 大分子、生物分子、超分子 | 较低 | 快 |

---

## 收敛标准

xTB 几何优化收敛标准：

- **梯度范数** < 0.001 Eh/a₀ (约 0.5 kcal/mol/Å)
- 达到收敛：`status: "success"`, `converged: true`
- 未收敛但有结果：`status: "partial_success"`, `converged: false`

---

## 安装指南

### 系统要求

- Python 3.8+
- xTB 6.3+（半经验量子化学程序）

### 1. 安装 Python 依赖

```bash
cd /home/administratorlulaiao/.openclaw/workspace/skills/geometry-optimizer
pip install -r requirements.txt
```

或直接安装：

```bash
pip install rdkit
```

### 2. 安装 xTB

xTB 是该 skill 的核心依赖，必须安装。以下是几种安装方式：

#### 方式 A: Conda（推荐）

```bash
conda install -c conda-forge xtb
```

验证安装：

```bash
xtb --version
```

#### 方式 B: Ubuntu/Debian

检查系统仓库：

```bash
apt-cache search xtb
```

如果仓库中没有，需要从源码编译或使用 Conda。

#### 方式 C: 源码编译

```bash
# 安装依赖
sudo apt install cmake gfortran libblas-dev liblapack-dev

# 克隆源码
git clone https://github.com/grimme-lab/xtb.git
cd xtb

# 编译
mkdir build && cd build
cmake .. -DCMAKE_INSTALL_PREFIX=$HOME/.local
make -j4
make install

# 添加到 PATH
export PATH=$HOME/.local/bin:$PATH
```

详细编译说明：https://xtb-docs.readthedocs.io/en/latest/installation.html

### 3. 验证安装

运行测试脚本：

```bash
python scripts/test_xtb_backend.py
```

预期输出：

```
✓ xTB is available: xtb version X.X.X
✓ Full optimization tests can be run!
```

### 4. 可选：安装 CREST（构象搜索）

如需进行构象搜索，可安装 CREST：

```bash
# Conda
conda install -c conda-forge crest

# 或从源码：https://github.com/grimme-lab/crest
```

验证：

```bash
crest --version
```

---

## 系统依赖

### 必须安装

- **xTB** (6.x 版本)

```bash
# Ubuntu/Debian
sudo apt install xtb

# Conda
conda install -c conda-forge xtb

# 验证安装
xtb --version
```

### Python 依赖

```bash
pip install rdkit
```

---

## 文件结构

```
geometry-optimizer/
├── SKILL.md                    # 本文件
├── README.md                   # 使用文档
├── INSTALL.md                  # 安装指南
├── requirements.txt            # Python 依赖
├── input.json                  # 批量输入示例
├── scripts/
│   ├── main_script.py          # 主入口脚本
│   ├── test_xtb_backend.py     # 测试脚本
│   ├── backends/
│   │   └── xtb_backend.py      # xTB 后端实现
│   └── utils/
│       ├── io_utils.py         # XYZ 读写工具
│       ├── smiles_utils.py     # SMILES→3D 生成
│       └── xtb_utils.py        # xTB 调用/解析工具
└── references/
    └── xtb_documentation.md    # xTB 命令参考
```

---

## 使用示例

### 示例 1: 单分子优化 (SMILES)

```bash
python scripts/main_script.py --smiles "CN1C=NC2=C1C(=O)N(C(=O)N2C)C" --name "咖啡因" --output-dir ./results
```

### 示例 2: 单分子优化 (XYZ 文件)

```bash
python scripts/main_script.py --input-xyz molecule.xyz --output-dir ./results
```

### 示例 3: 批量优化

```bash
python scripts/main_script.py --input input.json --output output.json --output-dir ./results
```

### 示例 4: 指定溶剂模型

```bash
python scripts/main_script.py --smiles "CCO" --solvent water --output-dir ./results
```

### 示例 5: 使用 GFN-FF 快速优化大分子

```bash
python scripts/main_script.py --smiles "大分子 SMILES" --method gfnff --max-cycles 500 --output-dir ./results
```

---

## 常见问题

### xTB 未找到

```
xTB not available: xtb command not found
```

**解决**: 安装 xTB，参考上方"系统依赖"。

### 3D 构象生成失败

```
Failed to generate 3D structure
```

**解决**: 
- 检查 SMILES 是否正确
- 尝试提供 XYZ 文件而非 SMILES

### 优化不收敛

```
status: "partial_success", converged: false
```

**解决**:
- 增加 `--max-cycles` (如 500)
- 尝试 `--method gfnff` 预优化，再用 `gfn2` 精修
- 检查初始结构是否合理

---

## 参考资料

- **xTB 官方文档**: https://xtb-docs.readthedocs.io
- **GFN2-xTB 论文**: https://doi.org/10.1021/acs.jctc.8b01176
- **GFN1-xTB 论文**: https://doi.org/10.1021/acs.jctc.7b00118
- **GFN-FF 论文**: https://doi.org/10.1002/anie.202004239
- **RDKit 文档**: https://www.rdkit.org/docs/

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 1.0 | 2026-03-19 | 初始版本，支持 xTB 单结构优化、SMILES→3D、XYZ 输入、批量处理 |

---

## 待扩展功能

- [ ] CREST 构象搜索后端
- [ ] 约束几何优化
- [ ] 频率分析
- [ ] 溶剂化自由能计算
- [ ] 更多输入格式支持 (MOL, SDF, PDB)
