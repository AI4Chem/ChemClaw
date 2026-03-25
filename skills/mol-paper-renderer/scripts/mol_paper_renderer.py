#!/usr/bin/env python3
"""
Molecular Paper Renderer - Publication-quality molecular graphics

Wrapper script for xyzrender with convenient defaults and batch processing.
"""

import argparse
import json
import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional


def get_default_output_dir() -> Path:
    """Get default output directory."""
    return Path.home() / ".openclaw" / "media" / "mol-paper-renderer"


def ensure_output_dir(output_dir: Path) -> None:
    """Ensure output directory exists."""
    output_dir.mkdir(parents=True, exist_ok=True)


def run_xyzrender(args: List[str], quiet: bool = False) -> int:
    """Run xyzrender with given arguments."""
    cmd = ["xyzrender"] + args
    
    if not quiet:
        print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout and not quiet:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        return result.returncode
    except FileNotFoundError:
        print("Error: xyzrender not found. Please install it:", file=sys.stderr)
        print("  pip install xyzrender", file=sys.stderr)
        print("  pip install 'xyzrender[all]'  # for all features", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error running xyzrender: {e}", file=sys.stderr)
        return 1


def process_smiles(smiles: str, output: Path, options: List[str], quiet: bool = False) -> int:
    """Process SMILES string - embed to 3D and render."""
    args = ["--smi", smiles, "-o", str(output)] + options
    
    if not quiet:
        print(f"Processing SMILES: {smiles}")
        print(f"Output: {output}")
    
    return run_xyzrender(args, quiet)


def process_file(input_file: Path, output: Path, options: List[str], quiet: bool = False) -> int:
    """Process input file."""
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}", file=sys.stderr)
        return 1
    
    args = [str(input_file), "-o", str(output)] + options
    
    if not quiet:
        print(f"Processing: {input_file}")
        print(f"Output: {output}")
    
    return run_xyzrender(args, quiet)


def batch_process(input_files: List[Path], output_dir: Path, options: List[str], 
                  quiet: bool = False) -> tuple:
    """Batch process multiple files."""
    ensure_output_dir(output_dir)
    
    success = 0
    failed = 0
    
    for i, input_file in enumerate(input_files, 1):
        if not input_file.exists():
            print(f"Skip (not found): {input_file}", file=sys.stderr)
            failed += 1
            continue
        
        # Generate output filename
        stem = input_file.stem
        ext = "svg"  # default format
        for opt in options:
            if opt.endswith(".png"):
                ext = "png"
            elif opt.endswith(".pdf"):
                ext = "pdf"
        
        output = output_dir / f"{stem}.{ext}"
        
        if process_file(input_file, output, options, quiet):
            failed += 1
        else:
            success += 1
            if not quiet:
                print(f"✓ [{i}/{len(input_files)}] Generated: {output}")
    
    return success, failed


def main():
    parser = argparse.ArgumentParser(
        description="Publication-quality molecular renderer (xyzrender wrapper)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # From SMILES
  %(prog)s -s "CCO" -o ethanol.svg
  
  # From XYZ file
  %(prog)s -i molecule.xyz -o output.png
  
  # Transition state
  %(prog)s -i ts.out --ts -o ts_figure.svg
  
  # NCI interactions
  %(prog)s -i complex.xyz --nci -o nci.svg
  
  # Rotation GIF
  %(prog)s -i molecule.xyz --gif-rot -o rotation.gif
  
  # Molecular orbital (cube file)
  %(prog)s -i caffeine_homo.cube --mo -o homo.svg
  
  # Batch processing
  %(prog)s -i *.xyz -d ./output
  
  # With custom style
  %(prog)s -i molecule.xyz --config paton -o styled.svg

Common options:
  --hy              Show hydrogen atoms
  --no-hy           Hide all hydrogen atoms
  --ts              Auto-detect transition state bonds
  --nci             Auto-detect non-covalent interactions
  --mo              Render molecular orbitals (cube file)
  --dens            Render electron density surface
  --esp FILE        ESP cube file for potential mapping
  --vdw             Show van der Waals spheres
  --hull INDICES    Convex hull (e.g., 1-6 for benzene ring)
  --gif-rot         Generate rotation GIF
  --gif-ts          Generate TS vibration GIF
  --config PRESET   Style preset: default, flat, paton

For full xyzrender options, see: https://xyzrender.readthedocs.io
        """
    )
    
    # Input options
    input_group = parser.add_argument_group("Input")
    input_group.add_argument("-i", "--input", type=Path, help="Input file (XYZ, SDF, PDB, cube, etc.)")
    input_group.add_argument("-s", "--smiles", type=str, help="SMILES string (auto 3D embedding)")
    input_group.add_argument("-d", "--output-dir", type=Path, default=None,
                            help=f"Output directory for batch mode (default: {get_default_output_dir()})")
    
    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument("-o", "--output", type=Path, help="Output file path")
    output_group.add_argument("-f", "--format", type=str, choices=["svg", "png", "pdf", "gif"],
                             default="svg", help="Output format (default: svg)")
    
    # Style options
    style_group = parser.add_argument_group("Style")
    style_group.add_argument("--config", type=str, help="Style preset or JSON config file")
    style_group.add_argument("--canvas-size", "-S", type=int, default=800, help="Canvas size in pixels")
    style_group.add_argument("--atom-scale", "-a", type=float, help="Atom radius scale")
    style_group.add_argument("--bond-width", "-b", type=float, help="Bond line width")
    style_group.add_argument("--background", "-B", type=str, help="Background color")
    style_group.add_argument("--transparent", "-t", action="store_true", help="Transparent background")
    style_group.add_argument("--no-gradient", action="store_true", help="Disable radial gradients")
    style_group.add_argument("--no-fog", action="store_true", help="Disable depth fog")
    
    # Display options
    display_group = parser.add_argument_group("Display")
    display_group.add_argument("--hy", "--hydrogens", action="store_true", help="Show hydrogen atoms")
    display_group.add_argument("--no-hy", "--no-hydrogens", action="store_true", help="Hide all H")
    display_group.add_argument("--kekule", "-k", action="store_true", help="Use Kekule bond orders")
    display_group.add_argument("--vdw", action="store_true", help="Show van der Waals spheres")
    display_group.add_argument("--vdw-opacity", type=float, help="vdW sphere opacity")
    
    # Advanced features
    advanced_group = parser.add_argument_group("Advanced Features")
    advanced_group.add_argument("--ts", action="store_true", help="Auto-detect TS bonds")
    advanced_group.add_argument("--ts-bond", type=str, action="append", help="Manual TS bond (e.g., 1-6)")
    advanced_group.add_argument("--nci", action="store_true", help="Auto-detect NCI interactions")
    advanced_group.add_argument("--nci-bond", type=str, action="append", help="Manual NCI bond")
    advanced_group.add_argument("--mo", action="store_true", help="Render MO (cube file)")
    advanced_group.add_argument("--mo-colors", type=str, nargs=2, help="MO colors (pos neg)")
    advanced_group.add_argument("--dens", action="store_true", help="Render density surface")
    advanced_group.add_argument("--esp", type=Path, help="ESP cube file")
    advanced_group.add_argument("--nci-surf", type=Path, help="NCI surface cube file")
    advanced_group.add_argument("--hull", type=str, nargs="+", help="Convex hull atom indices")
    advanced_group.add_argument("--hull-color", type=str, help="Hull color")
    advanced_group.add_argument("--hull-opacity", type=float, help="Hull opacity")
    advanced_group.add_argument("--measure", action="store_true", help="Print measurements")
    advanced_group.add_argument("--idx", action="store_true", help="Show atom indices")
    advanced_group.add_argument("--cmap", type=Path, help="Atom property colormap file")
    
    # Animation
    anim_group = parser.add_argument_group("Animation")
    anim_group.add_argument("--gif-rot", type=str, nargs="?", const="y", help="Rotation GIF (axis: x,y,z,xy,xz,yz)")
    anim_group.add_argument("--gif-ts", action="store_true", help="TS vibration GIF")
    anim_group.add_argument("--gif-trj", action="store_true", help="Trajectory GIF")
    anim_group.add_argument("--gif-output", "-go", type=Path, help="GIF output path")
    anim_group.add_argument("--gif-fps", type=int, default=10, help="GIF FPS")
    
    # Crystal
    crystal_group = parser.add_argument_group("Crystal")
    crystal_group.add_argument("--crystal", type=str, nargs="?", help="Load crystal structure (vasp/qe)")
    crystal_group.add_argument("--cell", action="store_true", help="Draw unit cell box")
    crystal_group.add_argument("--no-ghosts", action="store_true", help="Hide ghost atoms")
    crystal_group.add_argument("--no-axes", action="store_true", help="Hide crystal axes")
    crystal_group.add_argument("--axis", type=str, help="View direction [HKL]")
    
    # Other
    other_group = parser.add_argument_group("Other")
    other_group.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")
    other_group.add_argument("--stdout", action="store_true", help=argparse.SUPPRESS)  # Reserved
    other_group.add_argument("--charge", type=int, default=0, help="Molecular charge")
    other_group.add_argument("--multiplicity", "-m", type=int, help="Spin multiplicity")
    other_group.add_argument("--debug", action="store_true", help="Debug mode")
    
    args = parser.parse_args()
    
    # Build xyzrender options
    xyz_opts = []
    
    # Format
    if args.format and args.output:
        # Override format from output extension if present
        if args.output.suffix.lower() in [".svg", ".png", ".pdf", ".gif"]:
            pass  # Use extension from output path
        else:
            # Add extension if not present
            if not args.output.suffix:
                args.output = args.output.with_suffix(f".{args.format}")
    
    # Style
    if args.config:
        xyz_opts.extend(["--config", args.config])
    if args.canvas_size:
        xyz_opts.extend(["-S", str(args.canvas_size)])
    if args.atom_scale:
        xyz_opts.extend(["-a", str(args.atom_scale)])
    if args.bond_width:
        xyz_opts.extend(["-b", str(args.bond_width)])
    if args.background:
        xyz_opts.extend(["-B", args.background])
    if args.transparent:
        xyz_opts.append("-t")
    if args.no_gradient:
        xyz_opts.append("--no-grad")
    if args.no_fog:
        xyz_opts.append("--no-fog")
    
    # Display
    if args.hy:
        xyz_opts.append("--hy")
    if args.no_hy:
        xyz_opts.append("--no-hy")
    if args.kekule:
        xyz_opts.extend(["-k", "--bo"])
    if args.vdw:
        xyz_opts.append("--vdw")
    if args.vdw_opacity:
        xyz_opts.extend(["--vdw-opacity", str(args.vdw_opacity)])
    
    # Advanced
    if args.ts:
        xyz_opts.append("--ts")
    if args.ts_bond:
        for bond in args.ts_bond:
            xyz_opts.extend(["--ts-bond", bond])
    if args.nci:
        xyz_opts.append("--nci")
    if args.nci_bond:
        for bond in args.nci_bond:
            xyz_opts.extend(["--nci-bond", bond])
    if args.mo:
        xyz_opts.append("--mo")
    if args.mo_colors:
        xyz_opts.extend(["--mo-colors"] + args.mo_colors)
    if args.dens:
        xyz_opts.append("--dens")
    if args.esp:
        xyz_opts.extend(["--esp", str(args.esp)])
    if args.nci_surf:
        xyz_opts.extend(["--nci-surf", str(args.nci_surf)])
    if args.hull:
        xyz_opts.extend(["--hull"] + args.hull)
    if args.hull_color:
        xyz_opts.extend(["--hull-color", args.hull_color])
    if args.hull_opacity:
        xyz_opts.extend(["--hull-opacity", str(args.hull_opacity)])
    if args.measure:
        xyz_opts.append("--measure")
    if args.idx:
        xyz_opts.append("--idx")
    if args.cmap:
        xyz_opts.extend(["--cmap", str(args.cmap)])
    
    # Animation
    if args.gif_rot:
        xyz_opts.extend(["--gif-rot", args.gif_rot if args.gif_rot != "y" else "y"])
    if args.gif_ts:
        xyz_opts.append("--gif-ts")
    if args.gif_trj:
        xyz_opts.append("--gif-trj")
    if args.gif_output:
        xyz_opts.extend(["-go", str(args.gif_output)])
    if args.gif_fps:
        xyz_opts.extend(["--gif-fps", str(args.gif_fps)])
    
    # Crystal
    if args.crystal:
        xyz_opts.extend(["--crystal", args.crystal])
    if args.cell:
        xyz_opts.append("--cell")
    if args.no_ghosts:
        xyz_opts.append("--no-ghosts")
    if args.no_axes:
        xyz_opts.append("--no-axes")
    if args.axis:
        xyz_opts.extend(["--axis", args.axis])
    
    # Other
    if args.charge:
        xyz_opts.extend(["--charge", str(args.charge)])
    if args.multiplicity:
        xyz_opts.extend(["-m", str(args.multiplicity)])
    if args.debug:
        xyz_opts.append("-d")
    
    # Process input
    if args.smiles:
        # SMILES mode
        if not args.output:
            # Generate default output name from SMILES
            safe_smiles = args.smiles.replace("=", "_").replace("(", "_").replace(")", "_")[:30]
            args.output = get_default_output_dir() / f"mol_{safe_smiles}.{args.format}"
        
        ensure_output_dir(args.output.parent)
        return process_smiles(args.smiles, args.output, xyz_opts, args.quiet)
    
    elif args.input:
        # File mode
        if isinstance(args.input, str):
            # Could be glob pattern
            import glob
            input_files = [Path(f) for f in glob.glob(args.input)]
            if len(input_files) == 0:
                print(f"No files matching: {args.input}", file=sys.stderr)
                return 1
            elif len(input_files) == 1:
                args.input = input_files[0]
            else:
                # Batch mode
                output_dir = args.output_dir or get_default_output_dir()
                success, failed = batch_process(input_files, output_dir, xyz_opts, args.quiet)
                print(f"\n完成：{success} 成功，{failed} 失败")
                return 0 if failed == 0 else 1
        
        if not args.output:
            args.output = get_default_output_dir() / f"{args.input.stem}.{args.format}"
        
        ensure_output_dir(args.output.parent)
        return process_file(args.input, args.output, xyz_opts, args.quiet)
    
    else:
        # Read from stdin or show help
        if not sys.stdin.isatty():
            # Piped input
            temp_input = Path("/tmp/xyzrender_stdin.xyz")
            temp_input.write_text(sys.stdin.read())
            if not args.output:
                args.output = get_default_output_dir() / "stdin.svg"
            ensure_output_dir(args.output.parent)
            return process_file(temp_input, args.output, xyz_opts, args.quiet)
        else:
            parser.print_help()
            return 0


if __name__ == "__main__":
    sys.exit(main())
