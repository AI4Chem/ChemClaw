---
name: boron-nmr-predict
description: Predict 11B (boron-11) NMR chemical shift for boron-containing molecules using a local CPU inference pipeline. Use when the user asks to predict boron NMR or 11B chemical shift and provides a molecule such as a SMILES string. The skill can download model weights from Hugging Face on first use, run local CPU inference, and generate a labeled molecule image so each predicted shift can be matched to a specific boron atom.
---

# Boron NMR Predict

Use the bundled scripts for deterministic local inference.

## Workflow

1. Create and activate a fresh conda environment for this skill.
2. Install Python dependencies from `requirements-core.txt` and `requirements-pyg.txt`.
3. Ensure model files exist locally by running `scripts/ensure_model.py`.
4. Run `scripts/predict_boron_nmr.py` with a SMILES string and solvent.
5. Return the predicted chemical shift for each boron atom in text form.
6. Generate the labeled PNG image into the user's tmp directory so each ppm value can be matched to `B(index)` in the structure image.

## Input contract

Prefer SMILES input.

Required:
- Molecule SMILES containing at least one boron atom

Optional:
- Solvent name. Supported solvents are:
  - `CDCl3`
  - `C6D6`
  - `d6-DMSO`
  - `CD3COCD3`
  - `CD3CN`
  - `CD3OD`
  - `CD2Cl2`
  - `d8-THF`
  - `d8-Toluene`
  - `D2O`

## Commands

Create a fresh conda environment and install deps:

```bash
bash scripts/setup_env.sh
```

The setup script is portable: it does not assume any machine-specific conda path. It first tries the current shell's `conda`, then common user-local installs such as `~/miniconda3`, `~/anaconda3`, and `~/conda`.

Manual alternative:

```bash
conda create -n boron-nmr-predict python=3.11 -y
conda activate boron-nmr-predict
python -m pip install -r requirements-core.txt
python -m pip install -r requirements-pyg.txt
```

Download model weights:

```bash
python scripts/ensure_model.py
```

Run prediction:

```bash
python scripts/predict_boron_nmr.py \
  --smiles "OB(O)c1ccccc1" \
  --solvent CDCl3 \
  --output-image /tmp/boron_nmr_result.png
```

Run an example:

```bash
bash scripts/run_example.sh
```

## Environment variables

- `BORON_NMR_MODEL_REPO`: Hugging Face repo id holding the model files
- `BORON_NMR_MODEL_DIR`: local cache directory for downloaded model files

Defaults:
- model repo: `SII-AI4Chem/boron-nmr-predict-model`
- model dir: `~/.cache/boron-nmr-predict/models`
- image output: user tmp directory such as `/tmp/boron_nmr_<id>.png`
- device: CPU only

## Output contract

Return:
- a text summary for the user
- canonical SMILES
- solvent
- number of boron atoms
- per-boron predictions with:
  - `atom_index`
  - `element`
  - `ppm`
- image path in the user's tmp directory when generated
- image error message when text prediction succeeds but image rendering fails

When replying to the user:
- explicitly tell the user where the image file was saved
- include the concrete `image_path` in the reply
- if the runtime/channel supports file sending, send the generated image file to the user as an attachment
- if file sending is unavailable, still tell the user the exact saved path so they can retrieve it

## Notes

- Keep inference on CPU.
- Use the bundled source files in `src/` instead of the original web app.
- The labeled image uses `B(index)` so users can map ppm values to specific boron atoms.
- By default, model files are downloaded from `SII-AI4Chem/boron-nmr-predict-model`. Override only when a different repo is explicitly required.
- Image rendering failure should not block the text prediction result; return the text result and include an image error when needed.
- After successful image generation, do not only mention that an image exists; tell the user the saved location and send the image when channel capabilities allow it.
