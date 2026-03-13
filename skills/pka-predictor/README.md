```markdown
# pKa Predictor

OpenClaw 的 pKa 预测 skill，支持两种后端：

- **custom**：本地规则 / 官能团 / 可选自定义模型
- **unipka**：基于 Uni-pKa Bohrium notebook 单文件权重路线的 pKa 预测

---

## 功能特性

- ✅ 支持单个 SMILES 预测
- ✅ 支持批量输入文件
- ✅ 支持 JSON / CSV / TXT 输出
- ✅ custom 后端支持官能团识别与启发式预测
- ✅ unipka 后端支持微观态枚举与自由能汇总
- ✅ 返回结构化结果，适合 OpenClaw 调用

---

## 当前后端说明

### 1. custom 后端
适合快速、本地、低依赖场景。  
特点：

- 基于官能团识别
- 可接自定义规则
- 可接自定义 joblib 模型
- 输出 strongest acidic/basic pKa

### 2. unipka 后端
当前接入的是：

**Bohrium notebook 的 single-weight pipeline**

而不是 GitHub 仓库里的：

**`infer_pka.sh` 5-fold pipeline**

它的工作流程是：

1. 读取 `smarts_pattern.tsv` 模板
2. 枚举不同电荷态的微观态
3. 用 `t_dwar_v_novartis_a_b.pt` 对微观态做自由能预测
4. 计算相邻电荷态之间的 macro pKa transitions

因此，`unipka` 的主要输出不是简单的“一个 acidic pKa 和一个 basic pKa”，而是：

- `dominant_neutral_to_anion_pka`
- `dominant_cation_to_neutral_pka`
- `all_predictions`

---

## 目录结构

```bash
pka-predictor/
├── README.md
├── SKILL.md
├── requirements.txt
├── references/
├── Uni-pKa/
│   ├── unimol/
│   ├── uni-pka-ckpt_v2/
│   │   ├── t_dwar_v_novartis_a_b.pt
│   │   ├── smarts_pattern.tsv
│   │   └── simple_smarts_pattern.tsv
│   └── ...
└── scripts/
    ├── predict_pka.py
    ├── backends/
    │   ├── __init__.py
    │   ├── custom_backend.py
    │   └── unipka_backend.py
    └── utils/
        ├── io_utils.py
        └── mol_utils.py