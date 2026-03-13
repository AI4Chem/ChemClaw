#!/usr/bin/env python3
"""
自定义后端
允许用户自定义 pKa 预测规则或使用其他模型

特性：
- 统一输出 schema
- 支持 joblib 模型
- 规则优先，其次模型，再其次官能团启发式
"""

import json
import os
import sys
from typing import Dict, List, Optional, Any

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.mol_utils import (
    smiles_to_mol,
    identify_acidic_groups,
    identify_basic_groups,
    calculate_descriptors,
)


class CustomBackend:
    def __init__(self, config_path: Optional[str] = None, model_path: Optional[str] = None):
        self.config = self._default_config()
        self.custom_rules = []
        self.model = None

        if config_path:
            self.load_config(config_path)

        if model_path:
            self.config["model"] = model_path
            self._load_custom_model()

    def _default_config(self) -> Dict[str, Any]:
        return {
            "name": "Custom pKa Predictor",
            "version": "1.0",
            "rules": [],
            "model": None,
            "corrections": {
                "logp_threshold": 3.0,
                "logp_correction": 0.5,
                "tpsa_threshold": 80.0,
                "tpsa_correction": 0.3,
            },
        }

    def load_config(self, config_path: str):
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件不存在：{config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)

        self.config.update(user_config)
        self.custom_rules = self.config.get("rules", [])

        if self.config.get("model"):
            self._load_custom_model()

    def _load_custom_model(self):
        model_path = self.config.get("model")
        if model_path and os.path.exists(model_path):
            try:
                import joblib
                self.model = joblib.load(model_path)
            except Exception as e:
                print(f"警告：无法加载自定义模型：{e}", file=sys.stderr)
                self.model = None

    def _apply_custom_rules(self, smiles: str) -> List[Dict[str, Any]]:
        """
        简化版规则：沿用字符串匹配。
        你后面如果想升级成 SMARTS 子结构匹配，我可以再给你一版。
        """
        predictions = []
        smiles_lower = smiles.lower()

        for rule in self.custom_rules:
            pattern = str(rule.get("pattern", "")).lower().strip()
            if pattern and pattern in smiles_lower:
                pka_value = rule.get("pka")
                if pka_value is not None:
                    predictions.append({
                        "source": "custom_rule",
                        "pka": float(pka_value),
                        "type": rule.get("type", "unknown"),
                        "priority": int(rule.get("priority", 1)),
                        "rule_name": rule.get("name", "Unnamed Rule"),
                        "confidence": 0.9 if int(rule.get("priority", 1)) > 5 else 0.8,
                    })
        return predictions

    def _predict_with_model(self, descriptors: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        假设 joblib 模型输入是固定顺序特征向量。
        如果你的自有模型接口不同，这里改一下就行。
        """
        if self.model is None:
            return None

        feature_names = [
            "molecular_weight", "logp", "tpsa", "hbd", "hba", "rotatable_bonds"
        ]
        x = [[float(descriptors.get(k, 0.0)) for k in feature_names]]

        try:
            pred = self.model.predict(x)
            pka = float(pred[0])
            return {
                "source": "custom_model",
                "pka": round(pka, 4),
                "type": "unknown",
                "group": None,
                "confidence": 0.8,
            }
        except Exception as e:
            print(f"警告：自定义模型预测失败：{e}", file=sys.stderr)
            return None

    def _heuristic_predictions(
        self,
        acidic_groups: List[Dict[str, Any]],
        basic_groups: List[Dict[str, Any]],
        descriptors: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        predictions = []

        for group in acidic_groups:
            pka_range = group["pka_range"]
            pka = (pka_range[0] + pka_range[1]) / 2
            if descriptors.get("logp", 0) > self.config["corrections"]["logp_threshold"]:
                pka += self.config["corrections"]["logp_correction"]

            predictions.append({
                "source": "heuristic",
                "pka": round(pka, 4),
                "type": "acidic",
                "group": group["name"],
                "confidence": 0.7,
            })

        for group in basic_groups:
            pka_range = group["pka_range"]
            pka = (pka_range[0] + pka_range[1]) / 2
            if descriptors.get("tpsa", 0) > self.config["corrections"]["tpsa_threshold"]:
                pka -= self.config["corrections"]["tpsa_correction"]

            predictions.append({
                "source": "heuristic",
                "pka": round(pka, 4),
                "type": "basic",
                "group": group["name"],
                "confidence": 0.7,
            })

        return predictions

    def _build_final_result(
        self,
        name: str,
        smiles: str,
        acidic_groups: List[Dict[str, Any]],
        basic_groups: List[Dict[str, Any]],
        descriptors: Dict[str, Any],
        predictions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        acidic_preds = [p for p in predictions if p.get("type") == "acidic" and p.get("pka") is not None]
        basic_preds = [p for p in predictions if p.get("type") == "basic" and p.get("pka") is not None]

        strongest_acidic = min(acidic_preds, key=lambda x: x["pka"])["pka"] if acidic_preds else None
        strongest_basic = max(basic_preds, key=lambda x: x["pka"])["pka"] if basic_preds else None

        return {
            "name": name,
            "smiles": smiles,
            "status": "success",
            "backend_used": "custom",
            "method": "Custom rules / model / heuristic",
            "results": {
                "strongest_acidic_pka": strongest_acidic,
                "strongest_basic_pka": strongest_basic,
                "all_predictions": predictions,
            },
            "functional_groups": {
                "acidic": [g["name"] for g in acidic_groups],
                "basic": [g["name"] for g in basic_groups],
            },
            "descriptors": descriptors,
            "metadata": {
                "rules_loaded": len(self.custom_rules),
                "model_loaded": self.model is not None,
            },
        }

    def predict(self, smiles: str, name: str = "Unknown") -> Dict[str, Any]:
        mol = smiles_to_mol(smiles)
        if not mol:
            return {
                "name": name,
                "smiles": smiles,
                "status": "error",
                "backend_used": "custom",
                "error": "无效的 SMILES 格式",
            }

        acidic_groups = identify_acidic_groups(smiles)
        basic_groups = identify_basic_groups(smiles)
        descriptors = calculate_descriptors(smiles)

        rule_predictions = self._apply_custom_rules(smiles)
        model_prediction = self._predict_with_model(descriptors)
        heuristic_predictions = self._heuristic_predictions(acidic_groups, basic_groups, descriptors)

        predictions = []
        predictions.extend(rule_predictions)
        if model_prediction is not None:
            predictions.append(model_prediction)
        predictions.extend(heuristic_predictions)

        return self._build_final_result(
            name=name,
            smiles=smiles,
            acidic_groups=acidic_groups,
            basic_groups=basic_groups,
            descriptors=descriptors,
            predictions=predictions,
        )

    def batch_predict(self, compounds: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for compound in compounds:
            smiles = compound.get("smiles", "")
            name = compound.get("name", "Unknown")
            results.append(self.predict(smiles, name))
        return results


def predict_pka_custom(
    smiles: str,
    name: str = "Unknown",
    config_path: Optional[str] = None,
    model_path: Optional[str] = None,
) -> Dict[str, Any]:
    backend = CustomBackend(config_path=config_path, model_path=model_path)
    return backend.predict(smiles, name)


if __name__ == "__main__":
    test_smiles = "CC(=O)O"
    result = predict_pka_custom(test_smiles, "乙酸")
    print(json.dumps(result, indent=2, ensure_ascii=False))