#!/usr/bin/env python3
"""
DRfold2 Individual Model Inference

This script runs inference using individual DRfold2 model configurations
for testing and analysis of specific model behaviors.

Usage:
    python examples/use_case_4_model_inference.py [--input INPUT_FASTA] [--output OUTPUT_DIR] [--model MODEL] [--device DEVICE]

Example:
    python examples/use_case_4_model_inference.py --input examples/data/test_sequence.fasta --output results/model_inference --model cfg_95
"""

import os
import sys
import argparse
from pathlib import Path

# Add DRfold2 to path
repo_path = Path(__file__).parent.parent / "repo" / "DRfold2"
sys.path.insert(0, str(repo_path))

def run_model_inference(fasta_file, output_dir, model_config="cfg_95", device="cpu"):
    """
    Run inference using a specific DRfold2 model configuration

    Args:
        fasta_file: Path to input FASTA file
        output_dir: Directory to save outputs
        model_config: Model configuration to use (cfg_95, cfg_96, cfg_97, cfg_99)
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
        print(f"Using model configuration: {model_config}")

        # Setup paths
        fasta_file = os.path.realpath(fasta_file)
        output_dir = os.path.realpath(output_dir)
        exp_dir = str(repo_path)

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Check model configuration
        available_models = ['cfg_95', 'cfg_96', 'cfg_97', 'cfg_99']
        if model_config not in available_models:
            print(f"Error: Invalid model configuration '{model_config}'")
            print(f"Available models: {', '.join(available_models)}")
            return False

        # Model paths
        dlmain = os.path.join(exp_dir, model_config, 'test_modeldir.py')
        mdir = os.path.join(exp_dir, 'model_hub', model_config)

        # Check if paths exist
        if not os.path.isfile(dlmain):
            print(f"Error: Model script not found: {dlmain}")
            return False

        if not os.path.isdir(mdir):
            print(f"Error: Model directory not found: {mdir}")
            print("Please run the installation script: bash repo/DRfold2/install.sh")
            return False

        # Output prefix
        output_prefix = os.path.join(output_dir, f'{model_config}_')

        print(f"Running model inference...")
        print(f"Model script: {dlmain}")
        print(f"Model directory: {mdir}")
        print(f"Output prefix: {output_prefix}")

        # Run inference
        cmd = f'python {dlmain} {device} {fasta_file} {output_prefix} {mdir}'
        print(f"Command: {cmd}")

        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=exp_dir)
        output, error = p.communicate()

        if p.returncode != 0:
            print(f"Error running model inference:")
            if output:
                print(output.decode())
            return False

        print("Model inference completed successfully!")

        # Check output files
        output_files = []
        for ext in ['.ret', '.pdb', '.pkl']:
            pattern = f'{model_config}_*{ext}'
            matches = [f for f in os.listdir(output_dir) if f.startswith(f'{model_config}_') and f.endswith(ext)]
            output_files.extend([os.path.join(output_dir, f) for f in matches])

        if output_files:
            print(f"Generated {len(output_files)} output files:")
            for file_path in sorted(output_files):
                file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                print(f"  {os.path.basename(file_path)} ({file_size} bytes)")
        else:
            print("Warning: No output files found with expected patterns")

        return True

    except Exception as e:
        print(f"Error during model inference: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def analyze_model_outputs(output_dir, model_config):
    """Analyze the outputs from model inference"""
    print(f"\nAnalyzing outputs for {model_config}:")

    # Look for different file types
    output_files = os.listdir(output_dir)

    ret_files = [f for f in output_files if f.startswith(model_config) and f.endswith('.ret')]
    pdb_files = [f for f in output_files if f.startswith(model_config) and f.endswith('.pdb')]
    pkl_files = [f for f in output_files if f.startswith(model_config) and f.endswith('.pkl')]

    print(f"  .ret files (structure data): {len(ret_files)}")
    print(f"  .pdb files (3D structures): {len(pdb_files)}")
    print(f"  .pkl files (raw predictions): {len(pkl_files)}")

    # Try to load and examine a .ret file if available
    if ret_files:
        ret_file = os.path.join(output_dir, ret_files[0])
        try:
            print(f"\nExamining {ret_files[0]}:")

            # Try to load as pickle
            import pickle
            with open(ret_file, 'rb') as f:
                data = pickle.load(f)

            print(f"  Data type: {type(data)}")

            if isinstance(data, dict):
                print(f"  Keys: {list(data.keys())}")
                for key, value in data.items():
                    if hasattr(value, 'shape'):
                        print(f"    {key}: shape {value.shape}")
                    else:
                        print(f"    {key}: {type(value)}")

        except Exception as e:
            print(f"  Could not analyze .ret file: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='DRfold2 Individual Model Inference')
    parser.add_argument('--input', '-i', default='examples/data/test_sequence.fasta',
                       help='Input FASTA file (default: examples/data/test_sequence.fasta)')
    parser.add_argument('--output', '-o', default='results/model_inference',
                       help='Output directory (default: results/model_inference)')
    parser.add_argument('--model', '-m', default='cfg_95',
                       choices=['cfg_95', 'cfg_96', 'cfg_97', 'cfg_99'],
                       help='Model configuration to use (default: cfg_95)')
    parser.add_argument('--device', '-d', default='cpu', choices=['cpu', 'cuda'],
                       help='Device for computation (default: cpu)')
    parser.add_argument('--analyze', action='store_true',
                       help='Analyze the output files after inference')

    args = parser.parse_args()

    # Check input file
    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    print("DRfold2 Individual Model Inference")
    print("=" * 38)
    print(f"Input FASTA: {args.input}")
    print(f"Output directory: {args.output}")
    print(f"Model configuration: {args.model}")
    print(f"Device: {args.device}")
    print()

    # Read and display input sequence
    try:
        with open(args.input, 'r') as f:
            lines = f.readlines()

        sequence_lines = [line.strip() for line in lines if not line.startswith('>')]
        sequence = ''.join(sequence_lines)

        print(f"Input sequence length: {len(sequence)} nucleotides")
        print(f"Sequence: {sequence[:50]}{'...' if len(sequence) > 50 else ''}")
        print()

    except Exception as e:
        print(f"Warning: Could not read input sequence: {str(e)}")

    success = run_model_inference(args.input, args.output, args.model, args.device)

    if success:
        print("\n✓ Model inference completed successfully!")

        if args.analyze:
            analyze_model_outputs(args.output, args.model)
    else:
        print("\n✗ Model inference failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()