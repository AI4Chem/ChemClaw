---
name: ms-spectra-simulation
description: Predict and visualize MS/MS spectra from a single SMILES using the fioRa online app. Use when the user wants a mass spectrum, MGF/MSP output, or a plotted stick spectrum from SMILES, with optional custom Name, precursor type, collision energy, and instrument settings.
---

# MS Spectra Simulation Skill

## When to use this
Use this skill when the user provides a **SMILES** string and wants:
- Predicted **MS/MS spectrum**
- Raw **MSP** output downloaded from fioRa
- Standard **MGF** output
- A quick **stick-spectrum PNG** visualization
- Simple defaults without manually preparing a CSV

## Inputs
- **SMILES** string (required)
- `--name` (optional, default: `mol1`)
- `--precursor` (optional, default: `[M+H]+`)
- `--ce` (optional, default: `20`)
- `--instrument` (optional, default: `HCD`)
- `--output-stem` (optional, default: `predicted_ms`)
- `--plot / --no-plot` (optional, default: plot enabled)
- `--show-title / --no-show-title` (optional, default: no title on the plot)

## Outputs
- `/tmp/chemclaw/predicted_ms.msp`
- `/tmp/chemclaw/predicted_ms.mgf`
- `/tmp/chemclaw/predicted_ms.png`

If `--output-stem mol1` is used, the outputs become:
- `/tmp/chemclaw/mol1.msp`
- `/tmp/chemclaw/mol1.mgf`
- `/tmp/chemclaw/mol1.png`

## Agent response
When returning results to the user, include the generated spectrum image directly in the response when a PNG was created.

## Notes
- This skill calls the fioRa online app at `https://apps.bam.de/shn01/fioRa/`.
- The site is a Shiny web app, so this skill uses Playwright browser automation instead of a simple REST request.
- Network access is required.

## New environment (from zero)

```bash
conda create -n fiora-online python=3.10 pip -y
conda activate fiora-online

cd ms-spectra-simulation
python -m pip install -r requirements.txt
python -m playwright install chromium
python ms_spectra_simulation.py CCO
```

- Run the script in an environment with browser access.

## How to use (environment already prepared)

### Fastest default run
```bash
cd ms-spectra-simulation
python ms_spectra_simulation.py CCO
```

This uses:
- `name=mol1`
- `precursor=[M+H]+`
- `ce=20`
- `instrument=HCD`
- plot enabled
- plot title hidden
- fioRa online backend

### Custom metadata
```bash
cd ms-spectra-simulation
python ms_spectra_simulation.py "CCO" \
  --name mol1 \
  --precursor "[M+H]+" \
  --ce 20 \
  --instrument HCD
```

### Keep the spectrum but skip PNG
```bash
cd ms-spectra-simulation
python ms_spectra_simulation.py "CCO" --no-plot
```

### Show the title on the figure
```bash
cd ms-spectra-simulation
python ms_spectra_simulation.py "CCO" --show-title
```
