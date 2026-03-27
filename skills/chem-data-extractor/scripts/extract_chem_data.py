#!/usr/bin/env python3
"""
Chemistry Data Extractor Script
Extract compound characterization data from chemistry supplementary material markdown files.
"""

import re
import json
import sys
import argparse
from pathlib import Path
from typing import Optional


def extract_compounds(text: str) -> list:
    """
    Extract all compound entries from the markdown text.
    Returns a list of compound dictionaries.
    """
    compounds = []
    
    # Split by compound headers - looking for patterns like:
    # (R)-N-Benzoyl-4-iodobenzenesulfonimidoyl fluoride (3i)
    # or # N-Benzoyl-4-methylbenzenesulfonimidoyl chloride (1a)
    compound_pattern = r'(?:^|\n)#+\s*\(?[RS]-?\)?-?[^\n(]+\(\s*[0-9][a-z]*\s*\)'
    
    matches = list(re.finditer(compound_pattern, text, re.MULTILINE | re.IGNORECASE))
    
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        compound_text = text[start:end]
        
        compound = parse_compound(compound_text)
        if compound:
            compounds.append(compound)
    
    return compounds


def parse_compound(text: str) -> Optional[dict]:
    """
    Parse a single compound entry and extract all characterization data.
    """
    compound = {
        "compound_id": None,
        "compound_name": None,
        "structure_image_description": None,
        "physical_state": None,
        "mass_obtained": None,
        "yield_percent": None,
        "melting_point_range": None,
        "rf_value": None,
        "optical_rotation": None,
        "hplc_conditions": None,
        "nmr_1H": None,
        "nmr_13C": None,
        "nmr_19F": None,
        "hrms_data": None,
        "racemic_sample_note": None
    }
    
    # Extract compound name and ID from header
    header_match = re.search(r'#+\s*(.+?)\s*\(\s*([0-9][a-z]*)\s*\)', text)
    if header_match:
        compound["compound_name"] = header_match.group(1).strip()
        compound["compound_id"] = header_match.group(2).lower()
    else:
        return None
    
    # Physical state
    state_match = re.search(r'(White solid|Colorless oil|Pale yellow solid|Yellow solid|White powder)', text, re.IGNORECASE)
    if state_match:
        compound["physical_state"] = state_match.group(1).lower()
    
    # Mass obtained (mg)
    mass_match = re.search(r'(\d+\.?\d*)\s*mg', text)
    if mass_match:
        compound["mass_obtained"] = float(mass_match.group(1))
    
    # Yield percent
    yield_match = re.search(r'(\d+)%\s*yield', text, re.IGNORECASE)
    if yield_match:
        compound["yield_percent"] = int(yield_match.group(1))
    
    # Melting point
    mp_patterns = [
        r'm\.?p\.?\s*=\s*([0-9.]+\s*–\s*[0-9.]+)\s*°?C',
        r'm\.?p\.?\s*\.?=\s*([0-9.]+\s*-\s*[0-9.]+)\s*°?C',
        r'm\.?p\.?\s*=\s*([0-9.]+\s*–\s*[0-9.]+)',
        r'm\.?p\.?\s*\.?=\s*([0-9.]+\s*-\s*[0-9.]+)',
    ]
    for pattern in mp_patterns:
        mp_match = re.search(pattern, text)
        if mp_match:
            mp = mp_match.group(1).replace('-', '–').replace(' ', '')
            compound["melting_point_range"] = mp
            break
    
    # Rf value
    rf_match = re.search(r'R_f\s*=\s*([0-9.]+)\s*\(([^)]+)\)', text)
    if rf_match:
        compound["rf_value"] = f"{rf_match.group(1)} ({rf_match.group(2)})"
    
    # Optical rotation
    opt_patterns = [
        r'\[\s*α\s*\]_\s*D\s*\^?\s*(\d+)\s*=\s*([+-]?\d+\.?\d*)\s*\(\s*c\s*=\s*([0-9.]+)\s*,\s*([^)]+)\)',
        r'\[\s*α\s*\]_\s*D\s*(\d+)\s*=\s*([+-]?\d+\.?\d*)\s*\(\s*c\s*=\s*([0-9.]+)\s*,\s*([^)]+)\)',
        r'\[\s*α\s*\]_\{\s*D\s*\}\s*\^?\s*(\d+)\s*=\s*([+-]?\d+\.?\d*)',
    ]
    for pattern in opt_patterns:
        opt_match = re.search(pattern, text)
        if opt_match:
            temp = opt_match.group(1)
            value = opt_match.group(2)
            conc = opt_match.group(3) if len(opt_match.groups()) > 2 else None
            solvent = opt_match.group(4) if len(opt_match.groups()) > 3 else None
            if conc and solvent:
                compound["optical_rotation"] = f"[α]D{temp} = {value} (c = {conc}, {solvent})"
            else:
                compound["optical_rotation"] = f"[α]D{temp} = {value}"
            break
    
    # HPLC conditions
    hplc = {}
    column_match = re.search(r'HPLC\s+([A-Za-z0-9-]+)', text)
    if column_match:
        hplc["column"] = column_match.group(1)
    
    mobile_match = re.search(r'n-hexane/2-propanol\s*=\s*([0-9/]+)', text)
    if mobile_match:
        hplc["mobile_phase"] = f"n-hexane/2-propanol = {mobile_match.group(1)}"
    
    flow_match = re.search(r'flow\s*rate\s*=\s*([0-9.]+)\s*mL/min', text)
    if flow_match:
        hplc["flow_rate"] = f"{flow_match.group(1)} mL/min"
    
    wave_match = re.search(r'λ\s*=\s*([0-9]+)\s*nm', text)
    if wave_match:
        hplc["wavelength"] = f"{wave_match.group(1)} nm"
    
    # Retention times and ee
    rt_match = re.search(r'retention\s*time:\s*([0-9.]+)\s*min\s*\(([^)]+)\),?\s*([0-9.]+)\s*min\s*\(([^)]+)\)', text)
    if rt_match:
        hplc["retention_times"] = {
            rt_match.group(2).strip(): f"{rt_match.group(1)} min",
            rt_match.group(4).strip(): f"{rt_match.group(3)} min"
        }
    
    ee_match = re.search(r'(\d+)%\s*e\.?e\.?', text)
    if ee_match:
        hplc["ee_percent"] = int(ee_match.group(1))
    
    if hplc:
        compound["hplc_conditions"] = hplc
    
    # NMR 1H
    nmr1h_match = re.search(r'1H\s*NMR\s*\(\s*(\d+)\s*MHz\s*,\s*([^)]+)\)\s*δ\s*([^\n]+)', text)
    if nmr1h_match:
        compound["nmr_1H"] = {
            "frequency": f"{nmr1h_match.group(1)} MHz",
            "solvent": nmr1h_match.group(2).strip(),
            "chemical_shifts": nmr1h_match.group(3).strip()
        }
    
    # NMR 13C
    nmr13c_match = re.search(r'13C\{1H\}\s*NMR\s*\(\s*(\d+)\s*MHz\s*,\s*([^)]+)\)\s*δ\s*([^\n]+)', text)
    if nmr13c_match:
        compound["nmr_13C"] = {
            "frequency": f"{nmr13c_match.group(1)} MHz",
            "solvent": nmr13c_match.group(2).strip(),
            "chemical_shifts": nmr13c_match.group(3).strip()
        }
    
    # NMR 19F
    nmr19f_match = re.search(r'19F\{1H\}\s*NMR\s*\(\s*(\d+)\s*MHz\s*,\s*([^)]+)\)\s*δ\s*([^\n]+)', text)
    if nmr19f_match:
        compound["nmr_19F"] = {
            "frequency": f"{nmr19f_match.group(1)} MHz",
            "solvent": nmr19f_match.group(2).strip(),
            "chemical_shift": nmr19f_match.group(3).strip()
        }
    
    # HRMS
    hrms = {}
    hrms_formula_match = re.search(r'calcd\s+for\s+([A-Za-z0-9]+)', text)
    if hrms_formula_match:
        hrms["formula"] = hrms_formula_match.group(1)
    
    hrms_ion_match = re.search(r'(\[M\s*\+\s*[A-Za-z]+\]\+)', text)
    if hrms_ion_match:
        hrms["ion_type"] = hrms_ion_match.group(1).replace(' ', '')
    
    hrms_calc_match = re.search(r'calcd\s+for\s+[A-Za-z0-9]+\s+([0-9.]+)', text)
    if hrms_calc_match:
        calc_mz = hrms_calc_match.group(1).rstrip('.')
        hrms["calculated_mz"] = float(calc_mz)
    
    hrms_found_match = re.search(r'found\s+([0-9.]+)', text)
    if hrms_found_match:
        found_mz = hrms_found_match.group(1).rstrip('.')
        hrms["found_mz"] = float(found_mz)
    
    if hrms:
        compound["hrms_data"] = hrms
    
    # Racemic sample note
    racemic_match = re.search(r'Racemic sample of [0-9a-z]+', text, re.IGNORECASE)
    if racemic_match:
        compound["racemic_sample_note"] = racemic_match.group(0)
    
    return compound


def find_compound_by_id(compounds: list, compound_id: str) -> Optional[dict]:
    """
    Find a compound by its ID (e.g., '3i', '1a').
    """
    target_id = compound_id.lower()
    for compound in compounds:
        if compound.get("compound_id") == target_id:
            return compound
    return None


def main():
    parser = argparse.ArgumentParser(description='Extract chemistry compound data from markdown files.')
    parser.add_argument('input_file', help='Input markdown file path')
    parser.add_argument('-o', '--output', help='Output JSON file path')
    parser.add_argument('-c', '--compound', help='Extract specific compound by ID (e.g., 3i, 1a)')
    parser.add_argument('--compact', action='store_true', help='Output compact JSON without null fields')
    
    args = parser.parse_args()
    
    # Read input file
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)
    
    text = input_path.read_text(encoding='utf-8')
    
    # Extract compounds
    compounds = extract_compounds(text)
    
    if not compounds:
        print("No compounds found in the file.", file=sys.stderr)
        sys.exit(1)
    
    # Filter by compound ID if specified
    if args.compound:
        compound = find_compound_by_id(compounds, args.compound)
        if not compound:
            print(f"Compound '{args.compound}' not found.", file=sys.stderr)
            available = [c["compound_id"] for c in compounds if c.get("compound_id")]
            print(f"Available compounds: {', '.join(sorted(set(available)))}", file=sys.stderr)
            sys.exit(1)
        result = compound
    else:
        result = compounds
    
    # Remove null fields if compact mode
    if args.compact:
        if isinstance(result, list):
            result = [{k: v for k, v in c.items() if v is not None} for c in result]
        else:
            result = {k: v for k, v in result.items() if v is not None}
    
    # Output
    output_json = json.dumps(result, indent=2, ensure_ascii=False)
    
    if args.output:
        output_path = Path(args.output)
        output_path.write_text(output_json, encoding='utf-8')
        if args.compound:
            print(f"Compound '{args.compound}' extracted to {args.output}")
        else:
            print(f"{len(compounds)} compounds extracted to {args.output}")
    else:
        print(output_json)


if __name__ == '__main__':
    main()
