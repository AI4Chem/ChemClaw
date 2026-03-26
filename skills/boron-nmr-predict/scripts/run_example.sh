#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$SKILL_ROOT"

if ! command -v python >/dev/null 2>&1; then
  echo "[ERROR] python not found in PATH. Activate the conda environment for this skill first." >&2
  exit 1
fi

python "$SKILL_ROOT/scripts/predict_boron_nmr.py" \
  --smiles "OB(O)c1ccccc1" \
  --solvent CDCl3

echo "[OK] Example run finished."
echo "[OK] The JSON result includes the saved image path under image_path."
