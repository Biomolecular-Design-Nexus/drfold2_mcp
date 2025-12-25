#!/usr/bin/env python3
"""
DRfold2 Basic RNA Structure Prediction

This script performs basic RNA 3D structure prediction from a FASTA sequence
using a single DRfold2 model configuration.

Usage:
    python examples/use_case_1_basic_prediction.py [--input INPUT_FASTA] [--output OUTPUT_DIR] [--device DEVICE]

Example:
    python examples/use_case_1_basic_prediction.py --input examples/data/test_sequence.fasta --output results/basic_prediction
"""

import os
import sys
import argparse
import tempfile
import shutil
from pathlib import Path

# Add DRfold2 to path
repo_path = Path(__file__).parent.parent / "repo" / "DRfold2"
sys.path.insert(0, str(repo_path))

def setup_directories(output_dir):
    """Create necessary output directories"""
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'rets_dir'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'folds'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'relax'), exist_ok=True)

def run_basic_prediction(fasta_file, output_dir, device="cpu"):
    """
    Run basic RNA structure prediction using a single model (cfg_95)

    Args:
        fasta_file: Path to input FASTA file
        output_dir: Directory to save outputs
        device: Device for computation ("cpu" or "cuda")
    """
    try:
        import torch
        import numpy as np
        from subprocess import Popen, PIPE, STDOUT

        # Set device
        if device == "cuda" and not torch.cuda.is_available():
            print("CUDA requested but not available. Using CPU instead.")
            device = "cpu"

        print(f"Using device: {device}")

        # Setup paths
        fasta_file = os.path.realpath(fasta_file)
        output_dir = os.path.realpath(output_dir)
        exp_dir = str(repo_path)

        setup_directories(output_dir)

        ret_dir = os.path.join(output_dir, 'rets_dir')
        folddir = os.path.join(output_dir, 'folds')
        refdir = os.path.join(output_dir, 'relax')

        # Use only cfg_95 for basic prediction
        dlexp = 'cfg_95'
        dlmain = os.path.join(exp_dir, dlexp, 'test_modeldir.py')
        mdir = os.path.join(exp_dir, 'model_hub', dlexp)

        # Check if model directory exists
        if not os.path.isdir(mdir):
            print(f"Warning: Model directory not found at {mdir}")
            print("Please run the installation script: bash repo/DRfold2/install.sh")
            return False

        # Step 1: Generate e2e and geo files
        print("Step 1: Generating end-to-end and geometry prediction files...")
        cmd = f'python {dlmain} {device} {fasta_file} {ret_dir}/{dlexp}_ {mdir}'
        print(f"Running: {cmd}")

        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=exp_dir)
        output, error = p.communicate()

        if p.returncode != 0:
            print(f"Error in step 1: {output.decode() if output else 'Unknown error'}")
            return False

        # Mark generation as done
        with open(os.path.join(ret_dir, 'done'), 'w') as f:
            f.write('1')

        # Step 2: Selection and optimization
        print("Step 2: Performing model selection and geometric optimization...")

        config_sel = os.path.join(exp_dir, 'cfg_for_selection.json')
        foldconfig = os.path.join(exp_dir, 'cfg_for_folding.json')
        selpython = os.path.join(exp_dir, 'PotentialFold', 'Selection.py')
        optpython = os.path.join(exp_dir, 'PotentialFold', 'Optimization.py')

        optsaveprefix = os.path.join(folddir, 'opt_0')
        save_prefix = os.path.join(folddir, 'sel_0')

        # Find ret files
        rets = [f for f in os.listdir(ret_dir) if f.endswith('.ret')]
        rets = [os.path.join(ret_dir, f) for f in rets]
        ret_str = ' '.join(rets)

        if not rets:
            print("Error: No .ret files found. Model inference may have failed.")
            return False

        # Selection
        cmd = f'python {selpython} {fasta_file} {config_sel} {save_prefix} {ret_str}'
        print(f"Running selection: {cmd}")
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=exp_dir)
        output, error = p.communicate()

        # Optimization
        cmd = f'python {optpython} {fasta_file} {optsaveprefix} {ret_dir} {save_prefix} {foldconfig}'
        print(f"Running optimization: {cmd}")
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=exp_dir)
        output, error = p.communicate()

        # Step 3: Structure relaxation with Arena
        print("Step 3: Performing structure relaxation...")

        # Find optimized model
        opt_files = [f for f in os.listdir(folddir) if f.startswith('opt_0')]
        if not opt_files:
            print("Error: No optimized model files found.")
            return False

        cgpdb = os.path.join(folddir, opt_files[0])
        savepdb = os.path.join(refdir, 'model_1.pdb')
        arena = os.path.join(exp_dir, 'Arena', 'Arena')

        # Check if Arena executable exists
        if not os.path.isfile(arena):
            print(f"Warning: Arena executable not found at {arena}")
            print("Please compile Arena: cd repo/DRfold2/Arena && make Arena")
            # Copy the coarse-grained model as final output
            shutil.copy2(cgpdb, savepdb)
            print(f"Coarse-grained model saved to: {savepdb}")
        else:
            cmd = f'{arena} {cgpdb} {savepdb} 7'
            print(f"Running relaxation: {cmd}")
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=exp_dir)
            output, error = p.communicate()

            if os.path.isfile(savepdb):
                print(f"Relaxed structure saved to: {savepdb}")
            else:
                print("Warning: Arena relaxation failed, using coarse-grained model")
                shutil.copy2(cgpdb, savepdb)

        print(f"\nBasic RNA structure prediction completed!")
        print(f"Output directory: {output_dir}")
        print(f"Final structure: {savepdb}")
        print(f"Intermediate files: {ret_dir}")
        print(f"Optimization files: {folddir}")

        return True

    except Exception as e:
        print(f"Error during prediction: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description='DRfold2 Basic RNA Structure Prediction')
    parser.add_argument('--input', '-i', default='examples/data/test_sequence.fasta',
                       help='Input FASTA file (default: examples/data/test_sequence.fasta)')
    parser.add_argument('--output', '-o', default='results/basic_prediction',
                       help='Output directory (default: results/basic_prediction)')
    parser.add_argument('--device', '-d', default='cpu', choices=['cpu', 'cuda'],
                       help='Device for computation (default: cpu)')

    args = parser.parse_args()

    # Check input file
    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    print("DRfold2 Basic RNA Structure Prediction")
    print("=" * 40)
    print(f"Input FASTA: {args.input}")
    print(f"Output directory: {args.output}")
    print(f"Device: {args.device}")
    print()

    success = run_basic_prediction(args.input, args.output, args.device)

    if success:
        print("\n✓ Basic prediction completed successfully!")
    else:
        print("\n✗ Basic prediction failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()