#!/usr/bin/env python3
"""
ADME Property Predictor

Predict ADMET properties from SMILES using Morgan fingerprints + ML models.
Supports: Caco-2, PAMPA, HIA, Pgp, Bioavailability, Lipophilicity
"""

import argparse
import json
import pickle
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List

import numpy as np

# Try to import RDKit
try:
    from rdkit import Chem
    from rdkit.Chem import AllChem
except ImportError:
    print("Error: RDKit is required. Install with: pip install rdkit", file=sys.stderr)
    sys.exit(1)

# Try to import sklearn
try:
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
except ImportError:
    print("Error: scikit-learn is required. Install with: pip install scikit-learn", file=sys.stderr)
    sys.exit(1)


class ADMEPredictor:
    """ADME property predictor using Morgan fingerprints + Random Forest."""
    
    # Model metadata for each ADME property
    MODELS = {
        'Caco2_Wang': {
            'type': 'regression',
            'description': 'Caco-2 细胞有效通透性',
            'unit': 'log Papp (10^-6 cm/s)',
            'interpretation': {
                'high': '> -5.0 (高通透性)',
                'medium': '-6.0 to -5.0 (中等通透性)',
                'low': '< -6.0 (低通透性)'
            }
        },
        'PAMPA_NCATS': {
            'type': 'classification',
            'description': 'PAMPA 通透性',
            'classes': ['Low-Moderate', 'High'],
        },
        'HIA_Hou': {
            'type': 'classification',
            'description': '人体肠道吸收',
            'classes': ['Inactive', 'Active'],
        },
        'Pgp_Broccatelli': {
            'type': 'classification',
            'description': 'P-糖蛋白抑制',
            'classes': ['Non-inhibitor', 'Inhibitor'],
        },
        'Bioavailability_Ma': {
            'type': 'classification',
            'description': '口服生物利用度',
            'classes': ['Low', 'High'],
        },
        'Lipophilicity_AstraZeneca': {
            'type': 'regression',
            'description': '亲脂性',
            'unit': 'logD',
        },
    }
    
    def __init__(self, model_dir: Optional[Path] = None):
        """
        Initialize predictor.
        
        Args:
            model_dir: Directory containing pre-trained models.
        """
        if model_dir:
            self.model_dir = Path(model_dir)
        else:
            # Try parent directory's models folder first
            self.model_dir = Path(__file__).parent.parent / 'models'
            if not self.model_dir.exists():
                self.model_dir = Path(__file__).parent / 'models'
        self.models: Dict[str, Any] = {}
        self.fingerprint_radius = 2
        self.fingerprint_nbits = 2048
        
    def smiles_to_fingerprint(self, smiles: str) -> Optional[np.ndarray]:
        """Convert SMILES to Morgan fingerprint."""
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        fp = AllChem.GetMorganFingerprintAsBitVect(
            mol, 
            radius=self.fingerprint_radius,
            nBits=self.fingerprint_nbits
        )
        return np.array(fp)
    
    def predict(self, smiles: str, properties: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Predict ADME properties for a molecule.
        
        Args:
            smiles: SMILES string of the molecule
            properties: List of properties to predict. If None, predicts all.
            
        Returns:
            Dictionary with property names and predictions.
        """
        if properties is None:
            properties = list(self.MODELS.keys())
        
        results = {
            'smiles': smiles,
            'predictions': {},
            'errors': {}
        }
        
        # Compute fingerprint once
        fp = self.smiles_to_fingerprint(smiles)
        if fp is None:
            results['errors']['fingerprint'] = f"Invalid SMILES: {smiles}"
            return results
        
        for prop in properties:
            if prop not in self.MODELS:
                results['errors'][prop] = f"Unknown property: {prop}. Use --list to see available properties."
                continue
            
            try:
                model = self._load_model(prop)
                if model is None:
                    results['errors'][prop] = "Model not found. Training required."
                    continue
                
                pred = self._predict_single(model, prop, fp)
                results['predictions'][prop] = pred
                
            except Exception as e:
                results['errors'][prop] = str(e)
        
        return results
    
    def _predict_single(self, model: Any, property_name: str, fp: np.ndarray) -> Dict[str, Any]:
        """Make prediction for a single property."""
        model_info = self.MODELS[property_name]
        
        if model_info['type'] == 'regression':
            value = model.predict([fp])[0]
            result = {
                'value': float(value),
                'type': 'regression',
                'unit': model_info.get('unit', ''),
                'description': model_info['description'],
            }
            
            # Add interpretation for Caco-2
            if property_name == 'Caco2_Wang':
                if value > -5.0:
                    result['interpretation'] = '高通透性 (吸收良好)'
                elif value >= -6.0:
                    result['interpretation'] = '中等通透性'
                else:
                    result['interpretation'] = '低通透性 (吸收差)'
            
            # Add interpretation for Lipophilicity
            if property_name == 'Lipophilicity_AstraZeneca':
                if value > 3:
                    result['interpretation'] = '高亲脂性 (可能代谢快)'
                elif value < 0:
                    result['interpretation'] = '低亲脂性 (膜通透性可能差)'
                else:
                    result['interpretation'] = '理想范围'
            
            return result
        else:  # classification
            pred_class = model.predict([fp])[0]
            pred_prob = model.predict_proba([fp])[0]
            classes = model_info.get('classes', ['Class 0', 'Class 1'])
            
            return {
                'class': classes[int(pred_class)],
                'probability': float(pred_prob[int(pred_class)]),
                'probabilities': {classes[i]: float(p) for i, p in enumerate(pred_prob)},
                'type': 'classification',
                'description': model_info['description'],
            }
    
    def _load_model(self, property_name: str) -> Optional[Any]:
        """Load pre-trained model from disk."""
        if property_name in self.models:
            return self.models[property_name]
        
        model_path = self.model_dir / f"{property_name}.pkl"
        if model_path.exists():
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            self.models[property_name] = model
            return model
        
        return None
    
    def list_properties(self) -> Dict[str, Dict[str, Any]]:
        """List all available ADME properties."""
        return self.MODELS.copy()


def format_table_output(results: Dict[str, Any]) -> str:
    """Format prediction results as a table."""
    lines = []
    lines.append(f"SMILES: {results['smiles']}")
    lines.append("")
    
    if results['predictions']:
        lines.append("ADME 性质预测结果:")
        lines.append("━" * 60)
        lines.append(f"{'性质':<25} {'预测值':<20} {'置信度/单位'}")
        lines.append("━" * 60)
        
        for prop, pred in results['predictions'].items():
            desc = pred['description']
            if pred['type'] == 'regression':
                value = f"{pred['value']:.4f} {pred.get('unit', '')}"
                confidence = '-'
            else:
                value = pred['class']
                confidence = f"{pred['probability']:.3f}"
            
            lines.append(f"{desc:<25} {value:<20} {confidence}")
            
            if 'interpretation' in pred:
                lines.append(f"{'':<25} → {pred['interpretation']}")
        
        lines.append("━" * 60)
    
    if results['errors']:
        lines.append("")
        lines.append("Errors:")
        for prop, err in results['errors'].items():
            lines.append(f"  {prop}: {err}")
    
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='ADME Property Predictor',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --smiles "CCO"
  %(prog)s --smiles "c1ccccc1" --property Caco2_Wang Lipophilicity_AstraZeneca
  %(prog)s --file molecules.smi --output results.csv
  %(prog)s --list
        """
    )
    parser.add_argument('--smiles', '-s', type=str, help='SMILES string to predict')
    parser.add_argument('--file', '-f', type=str, help='File with SMILES (one per line)')
    parser.add_argument('--property', '-p', type=str, nargs='+', help='Properties to predict')
    parser.add_argument('--list', '-l', action='store_true', help='List available properties')
    parser.add_argument('--output', '-o', type=str, help='Output file path')
    parser.add_argument('--json', '-j', action='store_true', help='Output as JSON')
    parser.add_argument('--model-dir', '-m', type=str, help='Model directory')
    
    args = parser.parse_args()
    
    predictor = ADMEPredictor(model_dir=Path(args.model_dir) if args.model_dir else None)
    
    # List properties
    if args.list:
        props = predictor.list_properties()
        if args.json:
            print(json.dumps(props, indent=2))
        else:
            print("Available ADME Properties:")
            print("=" * 60)
            for name, info in props.items():
                print(f"\n{name}")
                print(f"  Type: {info['type']}")
                print(f"  Description: {info['description']}")
                if 'unit' in info:
                    print(f"  Unit: {info['unit']}")
                if 'classes' in info:
                    print(f"  Classes: {', '.join(info['classes'])}")
                if 'interpretation' in info:
                    print(f"  Interpretation:")
                    for key, val in info['interpretation'].items():
                        print(f"    {key}: {val}")
        return
    
    # Validate input
    if not args.smiles and not args.file:
        parser.error("Either --smiles or --file is required")
    
    # Get SMILES list
    smiles_list = []
    if args.smiles:
        smiles_list = [args.smiles]
    elif args.file:
        with open(args.file, 'r') as f:
            smiles_list = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    # Predict
    all_results = []
    for smiles in smiles_list:
        results = predictor.predict(smiles, args.property)
        all_results.append(results)
    
    # Output
    if args.json:
        output = json.dumps(all_results if len(all_results) > 1 else all_results[0], indent=2, ensure_ascii=False)
    else:
        if len(all_results) == 1:
            output = format_table_output(all_results[0])
        else:
            outputs = [format_table_output(r) for r in all_results]
            output = '\n\n'.join(outputs)
    
    # Write output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✓ Results written to: {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
