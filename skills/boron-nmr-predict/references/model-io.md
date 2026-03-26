# Model I/O

## Hugging Face repo

Default model repo:

`SII-AI4Chem/boron-nmr-predict-model`

## Expected Hugging Face repo contents

Place these files at the root of the model repo:

- `model_v3_fold_1.pth`
- `model_v3_fold_2.pth`
- `model_v3_fold_3.pth`
- `model_v3_fold_4.pth`
- `model_v3_fold_5.pth`
- `ml_feature_scaler.pkl`

## Local cache layout

Default local model directory:

`~/.cache/boron-nmr-predict/models`

## Prediction output

The CLI returns JSON with:

- `text_summary`
- `canonical_smiles`
- `solvent`
- `num_borons`
- `predictions[]`
  - `atom_index`
  - `element`
  - `ppm`
- `image_path` when generated
- `image_error` when image rendering fails but text prediction succeeds
- `device`

## User-facing reply expectation

After prediction:

- tell the user the exact image save path
- if the channel supports attachments, send the generated image file to the user
- if attachment sending is not available, still provide the local file path explicitly
