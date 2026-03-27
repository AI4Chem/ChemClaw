#!/usr/bin/env python3
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

FIORA_URL = "https://apps.bam.de/shn01/fioRa/"
OUTPUT_DIR = Path("/tmp/chemclaw")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Predict and visualize an MS/MS spectrum from a single SMILES using the fioRa online app."
    )
    parser.add_argument("smiles", help="Input SMILES string, for example CCO.")
    parser.add_argument("--name", default="mol1", help="Spectrum name. Default: mol1.")
    parser.add_argument(
        "--precursor",
        default="[M+H]+",
        help="Precursor ion type. Default: [M+H]+.",
    )
    parser.add_argument(
        "--ce",
        type=float,
        default=20.0,
        help="Collision energy. Default: 20.",
    )
    parser.add_argument(
        "--instrument",
        default="HCD",
        help="Instrument type. Default: HCD.",
    )
    parser.add_argument(
        "--output-stem",
        default="predicted_ms",
        help="Base name for output files inside /tmp/chemclaw. Default: predicted_ms.",
    )
    parser.add_argument(
        "--plot",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Generate a PNG stick spectrum. Default: true.",
    )
    parser.add_argument(
        "--show-title",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="Show the molecule name at the top of the plot. Default: false.",
    )
    parser.add_argument("--debug", action=argparse.BooleanOptionalAction, default=False, help="Enable debug output.")
    return parser.parse_args()


def require_playwright():
    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Missing dependency 'playwright'. Install with:\n"
            "  python -m pip install -r requirements.txt\n"
            "  python -m playwright install chromium"
        ) from exc
    return sync_playwright, PlaywrightTimeoutError


def build_textbox_payload(args: argparse.Namespace) -> str:
    return (
        "Name,SMILES,Precursor_type,CE,Instrument_type\n"
        f"{args.name},{args.smiles},{args.precursor},{args.ce:g},{args.instrument}\n"
    )


def download_msp(args: argparse.Namespace, msp_path: Path) -> None:
    sync_playwright, PlaywrightTimeoutError = require_playwright()
    payload = build_textbox_payload(args)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        try:
            page.goto(FIORA_URL, wait_until="domcontentloaded", timeout=120000)
            page.locator("#fioRa-text_input").fill(payload)
            page.locator("#fioRa-start_button").click()

            page.wait_for_function(
                """
                () => {
                  const select = document.querySelector('#fioRa-current_name-input');
                  return select && select.options && select.options.length > 0;
                }
                """,
                timeout=120000,
            )

            page.wait_for_function(
                """
                () => {
                  const link = document.querySelector('#fioRa-btn_download_msp');
                  return link
                    && link.getAttribute('href')
                    && link.getAttribute('href') !== ''
                    && !link.classList.contains('disabled');
                }
                """,
                timeout=120000,
            )

            with page.expect_download(timeout=60000) as download_info:
                page.locator("#fioRa-btn_download_msp").click()
            download = download_info.value
            download.save_as(str(msp_path))
        except PlaywrightTimeoutError as exc:
            raise RuntimeError(
                "Timed out while waiting for fioRa online app to return a downloadable MSP file."
            ) from exc
        finally:
            context.close()
            browser.close()


def parse_spectrum_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    if "BEGIN IONS" in text:
        return parse_mgf_text(text)
    return parse_msp_text(text)


def parse_mgf_text(text: str) -> list[dict]:
    records = []
    current_headers: dict[str, str] | None = None
    current_peaks: list[tuple[float, float]] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line == "BEGIN IONS":
            current_headers = {}
            current_peaks = []
            continue
        if line == "END IONS":
            if current_headers is not None:
                records.append({"headers": current_headers, "peaks": current_peaks})
            current_headers = None
            current_peaks = []
            continue
        if current_headers is None:
            continue
        if "=" in line:
            key, value = line.split("=", 1)
            current_headers[key.strip()] = value.strip()
            continue

        parts = line.split()
        if len(parts) >= 2:
            try:
                mz = float(parts[0])
                intensity = float(parts[1])
            except ValueError:
                continue
            current_peaks.append((mz, intensity))

    return records


def parse_msp_text(text: str) -> list[dict]:
    records = []
    current_headers: dict[str, str] = {}
    current_peaks: list[tuple[float, float]] = []
    reading_peaks = False

    def flush_record() -> None:
        nonlocal current_headers, current_peaks, reading_peaks
        if current_headers or current_peaks:
            records.append({"headers": current_headers, "peaks": current_peaks})
        current_headers = {}
        current_peaks = []
        reading_peaks = False

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            flush_record()
            continue

        lower = line.lower()
        if lower.startswith("num peaks"):
            reading_peaks = True
            continue

        if not reading_peaks and ":" in line:
            key, value = line.split(":", 1)
            current_headers[key.strip()] = value.strip()
            continue

        if reading_peaks:
            parts = line.split()
            if len(parts) >= 2:
                try:
                    mz = float(parts[0])
                    intensity = float(parts[1])
                except ValueError:
                    continue
                current_peaks.append((mz, intensity))

    flush_record()
    return records


def write_mgf(records: list[dict], mgf_path: Path) -> None:
    lines: list[str] = []
    for record in records:
        headers = record["headers"]
        peaks = record["peaks"]
        lines.append("BEGIN IONS")
        title = headers.get("Name") or headers.get("TITLE") or "fioRa_prediction"
        lines.append(f"TITLE={title}")

        header_map = {
            "SMILES": ["SMILES"],
            "FORMULA": ["Formula", "FORMULA"],
            "PEPMASS": ["Precursor_MZ", "PRECURSOR_MZ", "PrecursorMZ", "PRECURSORMZ"],
            "PRECURSORTYPE": ["Precursor_type", "PRECURSORTYPE"],
            "COLLISIONENERGY": ["CE", "Collision_energy", "COLLISIONENERGY"],
            "INSTRUMENTTYPE": ["Instrument_type", "INSTRUMENTTYPE"],
            "RETENTIONTIME": ["RETENTIONTIME"],
            "CCS": ["CCS"],
            "COMMENT": ["Comment", "COMMENT"],
        }
        for out_key, candidates in header_map.items():
            for candidate in candidates:
                value = headers.get(candidate)
                if value:
                    lines.append(f"{out_key}={value}")
                    break

        for mz, intensity in peaks:
            lines.append(f"{mz:g} {intensity:g}")
        lines.append("END IONS")
        lines.append("")

    mgf_path.write_text("\n".join(lines), encoding="utf-8")


def plot_spectrum(records: list[dict], png_path: Path, show_title: bool) -> None:
    if not records:
        raise RuntimeError("No spectra found in downloaded MSP output.")

    record = records[0]
    peaks = record["peaks"]
    if not peaks:
        raise RuntimeError("Downloaded MSP output contains no peaks.")

    title = record["headers"].get("Name", "fioRa prediction")
    mz_values = [peak[0] for peak in peaks]
    intensities = [peak[1] for peak in peaks]

    plt.figure(figsize=(10, 4.5))
    plt.vlines(mz_values, [0], intensities, linewidth=1.2)
    plt.xlabel("m/z")
    plt.ylabel("Intensity")
    plt.xlim(0, max(mz_values) * 1.05)
    plt.ylim(0, max(intensities) * 1.1)
    if show_title:
        plt.title(title)
    plt.tight_layout()
    plt.savefig(png_path, dpi=180)
    plt.close()


def main() -> None:
    args = parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    msp_path = OUTPUT_DIR / f"{args.output_stem}.msp"
    mgf_path = OUTPUT_DIR / f"{args.output_stem}.mgf"
    png_path = OUTPUT_DIR / f"{args.output_stem}.png"

    download_msp(args, msp_path)
    records = parse_spectrum_file(msp_path)
    write_mgf(records, mgf_path)

    if args.plot:
        plot_spectrum(records, png_path, args.show_title)
        print(f"Plot written to {png_path}")

    print(f"MSP written to {msp_path}")
    print(f"MGF written to {mgf_path}")


if __name__ == "__main__":
    main()
