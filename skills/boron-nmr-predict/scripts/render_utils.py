#!/usr/bin/env python3
import io
from PIL import Image
from rdkit.Chem.Draw import rdMolDraw2D


def generate_molecule_image(mol, predictions, width=750, height=480):
    boron_indices = [p['atom_index'] for p in predictions]
    atom_colors = {idx: (0.68, 0.85, 1.0) for idx in boron_indices}
    atom_radii = {idx: 0.4 for idx in boron_indices}

    drawer = rdMolDraw2D.MolDraw2DCairo(width, height)
    opts = drawer.drawOptions()
    opts.additionalAtomLabelPadding = 0.15

    for p in predictions:
        idx = p['atom_index']
        opts.atomLabels[idx] = f"B({idx})"

    drawer.DrawMolecule(
        mol,
        highlightAtoms=boron_indices,
        highlightAtomColors=atom_colors,
        highlightAtomRadii=atom_radii,
    )
    drawer.FinishDrawing()
    png_data = drawer.GetDrawingText()
    return Image.open(io.BytesIO(png_data))
