---
name: gjf-to-xyz
description: |
  Convert Gaussian gjf input files to XYZ format.
  将Gaussian gjf输入文件转换为XYZ格式。
  
  Use when agent needs to convert molecular structure files from Gaussian input format (.gjf) to XYZ format for visualization or use with other computational chemistry software.
  当智能体需要将Gaussian输入格式(.gjf)的分子结构文件转换为XYZ格式用于可视化或其他计算化学软件时使用。
---

# GJF to XYZ Converter

Convert Gaussian gjf files to XYZ format. Supports single file conversion and batch processing.

## Quick Start

### Command Line

```bash
# Single file conversion
python scripts/gjf2xyz.py input.gjf

# Specify output file
python scripts/gjf2xyz.py input.gjf -o output.xyz

# Batch conversion
python scripts/gjf2xyz.py ./gjf_directory/ -o ./xyz_directory/
```

### Python API

```python
from scripts.gjf2xyz import convert_gjf_to_xyz, batch_convert

# Convert single file
output_path = convert_gjf_to_xyz("molecule.gjf", "molecule.xyz")

# Batch conversion
converted_files = batch_convert("./gjf_files/", "./xyz_files/")
```

## File Formats

### Input: GJF (Gaussian Input)
```
%chk=molecule.chk
# hf/3-21g

Title Card Required

0 1
 C     2.21210000    0.98250000   -0.58720000
 H     2.46010000    0.50290000    0.38600000
...
```

### Output: XYZ
```
56
Title Card Required
 C      2.21210000    0.98250000   -0.58720000
 H      2.46010000    0.50290000    0.38600000
...
```

## Features

- Extracts atomic coordinates from Gaussian gjf files
- Preserves element symbols and coordinates
- Extracts title from gjf file
- Handles connectivity section (ignored in output)
- Batch processing support
- Automatic output naming

## Notes

- XYZ format contains only element symbol and coordinates
- Charge and multiplicity information is not preserved in XYZ
- Connectivity information is ignored during conversion
