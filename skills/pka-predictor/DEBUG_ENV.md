# pKa Predictor 调试环境指南

## 推荐调试环境

### 方案 1：使用虚拟环境（推荐）

```bash
# 1. 创建虚拟环境
cd /home/administratorlulaiao/.openclaw/workspace/skills/pka-predictor
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 4. 测试安装
python3 scripts/predict_pka.py --smiles "CC(=O)O" --name "乙酸"

# 5. 调试完成后退出
deactivate
```

**优点：**
- 依赖隔离，不影响系统 Python
- 可以随意安装/卸载包
- 适合开发和测试

### 方案 2：使用 Conda 环境

```bash
# 1. 创建 conda 环境
conda create -n pka-predictor python=3.12

# 2. 激活环境
conda activate pka-predictor

# 3. 安装依赖
pip install -r requirements.txt

# 4. 测试
python3 scripts/predict_pka.py --smiles "CC(=O)O" --name "乙酸"
```

**优点：**
- 更好的包管理
- 支持多 Python 版本
- 适合科学计算

### 方案 3：使用当前系统环境

如果已安装依赖，可以直接使用：

```bash
cd /home/administratorlulaiao/.openclaw/workspace/skills/pka-predictor
python3 scripts/predict_pka.py --smiles "CC(=O)O" --name "乙酸"
```

## 依赖安装

### 完整依赖列表

```bash
# 核心依赖
pip install rdkit pandas scipy numpy requests

# 机器学习依赖（UniPKA 后端需要）
pip install torch

# 可选依赖
pip install joblib scikit-learn
```

### 一键安装

```bash
pip install -r requirements.txt
```

## 常见错误及解决方案

### 错误 1: `No module named 'pandas'`

```bash
pip install pandas
```

### 错误 2: `No module named 'scipy'`

```bash
pip install scipy
```

### 错误 3: `No module named 'torch'`

```bash
pip install torch
# 或使用 CUDA 版本
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

### 错误 4: `No module named 'transformer_encoder_with_pair'`

这是 Uni-pKa 项目的自定义模块，需要从 Uni-pKa 仓库获取：

```bash
# 克隆 Uni-pKa 仓库
git clone https://github.com/usptoyy/Uni-pKa.git
cd Uni-pKa

# 复制模块到项目
cp transformer_encoder_with_pair.py /home/administratorlulaiao/.openclaw/workspace/skills/pka-predictor/scripts/
```

### 错误 5: RDKit 导入失败

```bash
# 重新安装 RDKit
pip uninstall rdkit
pip install rdkit
```

## 调试技巧

### 1. 启用详细输出

```bash
python3 scripts/predict_pka.py --smiles "CC(=O)O" --verbose
```

### 2. 使用 Python 交互式调试

```bash
python3
>>> from scripts.backends.custom_backend import CustomBackend
>>> backend = CustomBackend()
>>> result = backend.predict("CC(=O)O", "乙酸")
>>> print(result)
```

### 3. 使用 pdb 调试

在代码中添加：
```python
import pdb; pdb.set_trace()
```

然后运行：
```bash
python3 scripts/predict_pka.py --smiles "CC(=O)O" --name "乙酸"
```

### 4. 检查依赖

```bash
python3 -c "import rdkit; print(rdkit.__version__)"
python3 -c "import pandas; print(pandas.__version__)"
python3 -c "import torch; print(torch.__version__)"
```

## 测试命令

### 基础测试

```bash
# 测试 custom 后端
python3 scripts/predict_pka.py --smiles "CC(=O)O" --name "乙酸" --backend custom

# 测试 unipka 后端（需要完整依赖）
python3 scripts/predict_pka.py --smiles "CC(=O)O" --name "乙酸" --backend unipka
```

### 批量测试

```bash
# 创建测试文件
cat > test_compounds.smi << EOF
CC(=O)O 乙酸
c1ccccc1O 苯酚
CCO 乙醇
CC(N)C(=O)O 丙氨酸
EOF

# 运行批量测试
python3 scripts/predict_pka.py --input test_compounds.smi --output results.json --verbose
```

### 性能测试

```bash
# 测试大量化合物
time python3 scripts/predict_pka.py --input large_dataset.smi --output results.json
```

## 开发环境配置

### VS Code 配置

创建 `.vscode/settings.json`：

```json
{
    "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.testing.pytestEnabled": true
}
```

### 代码格式化

```bash
# 安装格式化工具
pip install black isort

# 格式化代码
black scripts/
isort scripts/
```

### 类型检查

```bash
# 安装 mypy
pip install mypy

# 运行类型检查
mypy scripts/
```

## 性能优化建议

1. **使用 GPU 加速**（如果有）：
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```

2. **批量处理**：
   - 使用 `--input` 参数批量处理化合物
   - 避免循环调用单个预测

3. **缓存结果**：
   - 对相同 SMILES 缓存预测结果
   - 使用 `--output` 保存结果避免重复计算

## 联系与支持

如有问题，请检查：
1. Python 版本（推荐 3.10+）
2. 依赖是否完整安装
3. 环境变量是否正确设置
