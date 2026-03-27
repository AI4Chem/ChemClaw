---
name: chem-data-extractor
description: |
  Extract structured chemical compound characterization data from chemistry supplementary material documents (PDF/Markdown). 
  从化学论文补充材料(PDF/Markdown)中提取结构化化合物表征数据。
  Use when Kimi needs to extract compound properties including NMR spectra, HRMS, HPLC data, melting points, optical rotation, and yield information from chemistry research papers or supplementary materials. 
  支持提取NMR谱图、HRMS、HPLC数据、熔点、旋光度、产率等信息。
  Supports both single compound extraction and batch extraction of all compounds.
  支持单个化合物提取和批量提取所有化合物。
---

# Chemistry Data Extractor | 化学数据提取器

Extract structured chemical characterization data from chemistry supplementary materials and return in strict JSON format.
从化学论文补充材料中提取结构化表征数据，以严格JSON格式返回。

## Supported Data Fields

- `compound_name`: Full IUPAC or common name (including stereochemistry if given)
- `structure_image_description`: Brief description of the molecular structure
- `physical_state`: e.g., "white solid", "colorless oil"
- `mass_obtained`: in mg
- `yield_percent`: as number only
- `melting_point_range`: in °C, as string like "126.6–127.3"
- `rf_value`: Rf value and solvent system
- `optical_rotation`: [α]D²⁵ value, concentration, solvent
- `hplc_conditions`: column, mobile phase, flow rate, wavelength, retention times (major/minor), ee%
- `nmr_1H`: frequency, solvent, chemical shifts with multiplicity and coupling constants
- `nmr_13C`: frequency, solvent, chemical shifts with notes (e.g., d, JCF)
- `nmr_19F`: frequency, solvent, chemical shift
- `hrms_data`: ion type, calculated m/z, found m/z, formula
- `racemic_sample_note`: if mentioned

## Workflow

### Step 1: Ask User for Extraction Mode

When user asks to extract chemistry data, first ask:

> Do you want to extract data for:
> 1. **A specific compound** (provide compound ID like "3i" or "1a")
> 2. **All compounds** in a single document
> 3. **Batch process** multiple PDF files (creates folder for each)

---

## Mode 1: Batch Process Multiple PDFs

For processing multiple PDF files at once. Creates a separate folder for each PDF with extracted compounds.

### Usage

```bash
python scripts/batch_extract.py \
    /path/to/pdf_folder \
    -o ./output_folder
```

### Options

- `-o, --output`: Output base directory (default: `./chem_extract_output`)
- `--keep-md`: Keep intermediate markdown files (default: cleanup after extraction)
- `--skip-existing`: Skip PDFs that already have output folders

### Output Structure

```
output_folder/
├── batch_summary.json          # Overall summary of all processed PDFs
├── paper1/
│   ├── compounds.json          # All extracted compounds
│   └── summary.json            # Brief summary with compound list
├── paper2/
│   ├── compounds.json
│   └── summary.json
└── ...
```

### Example: Batch Process

```bash
# Process all PDFs in a folder
python scripts/batch_extract.py ./pdfs/ -o ./extracted_data

# Process single PDF
python scripts/batch_extract.py ./article.pdf -o ./results

# Keep intermediate files, skip existing
python scripts/batch_extract.py ./pdfs/ --keep-md --skip-existing
```

---

## Mode 2: Single Document Processing

For processing a single document (Markdown or after PDF conversion).

### Step 2: Prepare Input File

If the input is a PDF file:
1. Use `mineru-pdf-converter` skill to convert PDF to Markdown first
2. Use the generated `full.md` file as input

If the input is already a Markdown file, use it directly.

### Step 3: Extract Data

Use the extraction script to parse the data:

```bash
# Extract a specific compound
python scripts/extract_chem_data.py \
    /path/to/full.md -c COMPOUND_ID --compact

# Extract all compounds
python scripts/extract_chem_data.py \
    /path/to/full.md --compact
```

Options:
- `-c, --compound`: Extract specific compound by ID (e.g., "3i", "1a")
- `--compact`: Remove null/empty fields from output
- `-o, --output`: Save output to file instead of stdout

### Step 4: Return Results

Output **ONLY** valid JSON without any extra text, unless the user specifically asks for explanations.

---

## Examples

### Example 1: Batch Process Multiple PDFs

```bash
# Process all PDFs in a directory
python scripts/batch_extract.py ./supplementary_pdfs/ -o ./extracted_compounds

# Output structure:
# ./extracted_compounds/
# ├── batch_summary.json
# ├── paper1/
# │   ├── compounds.json
# │   └── summary.json
# └── paper2/
#     ├── compounds.json
#     └── summary.json
```

### Example 2: Extract Single Compound from Markdown

```bash
python scripts/extract_chem_data.py full.md -c 3i --compact
```

Output:
```json
{
  "compound_name": "(R)-N-Benzoyl-4-iodobenzenesulfonimidoyl fluoride",
  "physical_state": "white solid",
  "mass_obtained": 33.2,
  "yield_percent": 85,
  "melting_point_range": "126.6–127.3",
  "rf_value": "0.37 (Pet/EtOAc, 5/1, v/v)",
  "optical_rotation": "[α]D25 = +10.3 (c = 0.75, CHCl3)",
  "hplc_conditions": {
    "column": "CHIRALCEL AY-RH",
    "mobile_phase": "n-hexane/2-propanol = 60/40",
    "flow_rate": "1.0 mL/min",
    "wavelength": "256 nm",
    "retention_times": {
      "major": "9.642 min",
      "minor": "12.955 min"
    },
    "ee_percent": 90
  },
  "nmr_1H": {
    "frequency": "400 MHz",
    "solvent": "CDCl3",
    "chemical_shifts": "δ 8.17–8.09 (m, 2H), 8.06–8.00 (m, 2H)..."
  },
  "nmr_13C": {
    "frequency": "100 MHz",
    "solvent": "CDCl3",
    "chemical_shifts": "δ 170.0, 139.2, 134.3 (d, JCF = 22.0 Hz)..."
  },
  "nmr_19F": {
    "frequency": "376 MHz",
    "solvent": "CDCl3",
    "chemical_shift": "δ 65.3 (s, 1F)"
  },
  "hrms_data": {
    "ion_type": "[M+Na]+",
    "calculated_mz": 411.9275,
    "found_mz": 411.9273,
    "formula": "C13H9FINNaO2S"
  }
}
```

### Example 3: Extract All Compounds from Single File

```bash
python scripts/extract_chem_data.py full.md --compact -o all_compounds.json
```

Output is a JSON array containing all extracted compounds.

---

## Common Compound ID Patterns

Compound IDs typically follow these patterns:
- Numbers: `1`, `2`, `3`
- Numbers with letters: `1a`, `3i`, `5b`
- Numbers with multiple letters: `1aa`, `3ba`
- Numbers with primes: `1'`, `2''`

## Tips

1. **Compound identification**: The script looks for section headers like `(R)-Compound Name (3i)` or `# Compound Name (1a)`
2. **Data completeness**: Not all fields may be present for every compound - missing fields will be `null` (or omitted with `--compact`)
3. **Stereochemistry**: The script preserves stereochemical descriptors like (R), (S), (±) in compound names
4. **Multiple compounds**: When extracting all compounds, the output is a JSON array sorted by appearance in document
