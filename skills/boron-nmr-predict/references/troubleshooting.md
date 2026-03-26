# Troubleshooting

## Common issues

### 1. `conda: command not found`
Conda is not installed or not initialized in the shell. The setup script only uses portable discovery rules: current shell `conda`, `CONDA_EXE`, and common user-local installs such as `~/miniconda3`, `~/anaconda3`, and `~/conda`.

If detection still fails:
- activate a shell where `conda` already works, then rerun `bash scripts/setup_env.sh`
- or source your own conda init script first, then rerun the setup script

Do not add machine-specific personal paths into the distributed skill.

### 2. PyG packages fail to install
The skill expects CPU wheels from:

`https://data.pyg.org/whl/torch-2.3.1+cpu.html`

Verify that the installed torch version matches the wheel index expectation. If needed, reinstall torch in a fresh conda environment before installing `requirements-pyg.txt`.

### 3. Model download fails
Check network access to Hugging Face and verify the repo exists:

`SII-AI4Chem/boron-nmr-predict-model`

Override with `BORON_NMR_MODEL_REPO` only when using a different repo.

### 4. `No boron atom found in the molecule`
The input SMILES parsed successfully, but contains no boron atom. Provide a boron-containing molecule.

### 5. Image path issues
The default image location is a unique file under `/tmp`, for example `/tmp/boron_nmr_ab12cd34.png`. If the user wants a different path, pass `--output-image /desired/path.png`.
