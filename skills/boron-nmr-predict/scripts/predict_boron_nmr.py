#!/usr/bin/env python3
import argparse
import json
import os
import sys
import tempfile
import uuid
from pathlib import Path

from rdkit import Chem

THIS_DIR = Path(__file__).resolve().parent
SKILL_ROOT = THIS_DIR.parent
SRC_DIR = SKILL_ROOT / 'src'
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

from core.predictor import BoronNMRPredictor
from ensure_model import ensure_model_files
from render_utils import generate_molecule_image

SUPPORTED_SOLVENTS = [
    'CDCl3', 'C6D6', 'd6-DMSO', 'CD3COCD3', 'CD3CN',
    'CD3OD', 'CD2Cl2', 'd8-THF', 'd8-Toluene', 'D2O'
]


def parse_args():
    p = argparse.ArgumentParser(description='Predict 11B NMR chemical shifts on CPU')
    p.add_argument('--smiles', required=True, help='Input molecule SMILES')
    p.add_argument('--solvent', default='CDCl3', help='Solvent name')
    p.add_argument('--output-image', default='', help='Optional output PNG path; defaults to a file in /tmp')
    p.add_argument('--json-indent', type=int, default=2)
    return p.parse_args()


def main():
    args = parse_args()

    if args.solvent not in SUPPORTED_SOLVENTS:
        raise SystemExit(f'Unsupported solvent: {args.solvent}. Supported: {SUPPORTED_SOLVENTS}')

    mol_check = Chem.MolFromSmiles(args.smiles)
    if mol_check is None:
        raise SystemExit(f'Invalid SMILES: {args.smiles}')
    if not any(atom.GetSymbol() == 'B' for atom in mol_check.GetAtoms()):
        raise SystemExit('No boron atom found in the molecule.')

    model_dir = ensure_model_files()

    predictor = BoronNMRPredictor(
        model_dir=str(model_dir),
        device='cpu',
        hidden_dim=256,
        dropout=0.012558398103042557,
        solvent_dim=32,
        ml_feature_dim=20,
        ml_hidden_dim=64,
    )

    result = predictor.predict(args.smiles, args.solvent)

    summary_lines = [
        f"Canonical SMILES: {result['canonical_smiles']}",
        f"Solvent: {args.solvent}",
        f"Boron atoms: {result['num_borons']}",
    ]
    for p in result['predictions']:
        summary_lines.append(f"B({p['atom_index']}): {p['ppm']:.2f} ppm")

    output = {
        'text_summary': '\n'.join(summary_lines),
        'canonical_smiles': result['canonical_smiles'],
        'solvent': args.solvent,
        'num_borons': result['num_borons'],
        'predictions': result['predictions'],
        'image_path': None,
        'image_error': None,
        'device': 'cpu',
    }

    output_image = args.output_image
    if not output_image:
        output_image = os.path.join(tempfile.gettempdir(), f'boron_nmr_{uuid.uuid4().hex[:8]}.png')

    try:
        img = generate_molecule_image(result['mol_object'], result['predictions'])
        out_path = Path(output_image).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(out_path)
        output['image_path'] = str(out_path)
    except Exception as e:
        output['image_error'] = str(e)

    print(json.dumps(output, ensure_ascii=False, indent=args.json_indent))


if __name__ == '__main__':
    main()
