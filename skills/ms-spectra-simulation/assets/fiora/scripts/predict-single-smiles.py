#!/usr/bin/env python3
import argparse
import csv
import subprocess
import sys
import tempfile
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a one-row Fiora input CSV from a single SMILES and run MS/MS prediction."
    )
    parser.add_argument("--smiles", required=True, help="Input SMILES string.")
    parser.add_argument("--name", default="mol1", help="Molecule name written to the output metadata.")
    parser.add_argument(
        "--precursor",
        default="[M+H]+",
        help="Precursor ion type, for example [M+H]+ or [M-H]-.",
    )
    parser.add_argument(
        "--ce",
        type=float,
        default=20.0,
        help="Collision energy value written to the CSV input.",
    )
    parser.add_argument(
        "--instrument",
        default="HCD",
        help="Instrument type written to the CSV input.",
    )
    parser.add_argument(
        "--output",
        default="mol1.mgf",
        help="Output spectrum path (.mgf or .msp). Defaults to mol1.mgf.",
    )
    parser.add_argument("--model", default="default", help="Model path passed to Fiora.")
    parser.add_argument("--dev", default="cpu", help="Device passed to Fiora, for example cpu or mps.")
    parser.add_argument(
        "--min-prob",
        type=float,
        default=0.001,
        help="Minimum peak probability to record.",
    )
    parser.add_argument("--rt", action=argparse.BooleanOptionalAction, default=False, help="Predict RT.")
    parser.add_argument("--ccs", action=argparse.BooleanOptionalAction, default=False, help="Predict CCS.")
    parser.add_argument(
        "--annotation",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Annotate predicted peaks with fragment SMILES.",
    )
    parser.add_argument("--debug", action=argparse.BooleanOptionalAction, default=False, help="Enable Fiora debug output.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    script_dir = Path(__file__).resolve().parent
    fiora_predict = script_dir / "fiora-predict"

    with tempfile.TemporaryDirectory(prefix="fiora_single_") as temp_dir:
        input_csv = Path(temp_dir) / "input.csv"
        with input_csv.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Name", "SMILES", "Precursor_type", "CE", "Instrument_type"])
            writer.writerow([args.name, args.smiles, args.precursor, args.ce, args.instrument])

        command = [
            sys.executable,
            str(fiora_predict),
            "-i",
            str(input_csv),
            "-o",
            str(output_path),
            "--model",
            args.model,
            "--dev",
            args.dev,
            "--min_prob",
            str(args.min_prob),
        ]
        if args.rt:
            command.append("--rt")
        if args.ccs:
            command.append("--ccs")
        if args.annotation:
            command.append("--annotation")
        if args.debug:
            command.append("--debug")

        subprocess.run(command, check=True)

    print(f"Finished single-SMILES prediction. Output written to {output_path}")


if __name__ == "__main__":
    main()
