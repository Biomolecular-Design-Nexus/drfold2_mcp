#!/usr/bin/env python3
"""
DRfold2 Ensemble RNA Structure Prediction

This script performs RNA 3D structure prediction using multiple DRfold2 models
with clustering to generate diverse conformations.

Usage:
    python examples/use_case_2_ensemble_prediction.py [--input INPUT_FASTA] [--output OUTPUT_DIR] [--device DEVICE] [--max-models MAX]

Example:
    python examples/use_case_2_ensemble_prediction.py --input examples/data/test_sequence.fasta --output results/ensemble_prediction --max-models 5
"""

import os
import sys
import argparse
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

def run_ensemble_prediction(fasta_file, output_dir, device="cpu", max_models=5):
    """
    Run ensemble RNA structure prediction using multiple models with clustering

    Args:
        fasta_file: Path to input FASTA file
        output_dir: Directory to save outputs
        device: Device for computation ("cpu" or "cuda")
        max_models: Maximum number of models to generate
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

        # All available model configurations
        dlexps = ['cfg_95', 'cfg_96', 'cfg_97', 'cfg_99']

        # Step 1: Generate predictions from all models
        print("Step 1: Generating predictions from all model configurations...")

        if not os.path.isfile(os.path.join(ret_dir, 'done')):
            for i, dlexp in enumerate(dlexps):
                dlmain = os.path.join(exp_dir, dlexp, 'test_modeldir.py')
                mdir = os.path.join(exp_dir, 'model_hub', dlexp)

                if not os.path.isdir(mdir):
                    print(f"Warning: Model directory not found at {mdir}")
                    continue

                print(f"Running model {i+1}/{len(dlexps)}: {dlexp}")
                cmd = f'python {dlmain} {device} {fasta_file} {ret_dir}/{dlexp}_ {mdir}'
                print(f"Command: {cmd}")

                p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=exp_dir)
                output, error = p.communicate()

                if p.returncode != 0:
                    print(f"Warning: Model {dlexp} failed: {output.decode() if output else 'Unknown error'}")

            # Mark generation as done
            with open(os.path.join(ret_dir, 'done'), 'w') as f:
                f.write('1')
        else:
            print("Using existing prediction files...")

        # Check if we have any results
        ret_files = [f for f in os.listdir(ret_dir) if f.endswith('.ret')]
        if not ret_files:
            print("Error: No prediction files (.ret) found. All models may have failed.")
            return False

        print(f"Found {len(ret_files)} prediction files")

        # Step 2: Clustering analysis
        print("Step 2: Performing clustering analysis...")

        config_sel = os.path.join(exp_dir, 'cfg_for_selection.json')
        foldconfig = os.path.join(exp_dir, 'cfg_for_folding.json')
        selpython = os.path.join(exp_dir, 'PotentialFold', 'Selection.py')
        optpython = os.path.join(exp_dir, 'PotentialFold', 'Optimization.py')
        clupy = os.path.join(exp_dir, 'PotentialFold', 'Clust.py')

        clufile = os.path.join(folddir, 'clu.txt')

        # Run clustering
        cmd = f'python {clupy} {ret_dir} {clufile}'
        print(f"Running clustering: {cmd}")
        p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=exp_dir)
        output, error = p.communicate()

        if not os.path.isfile(clufile):
            print("Warning: Clustering failed. Proceeding with single model prediction.")
            # Fall back to single model
            ret_files = [os.path.join(ret_dir, f) for f in ret_files]
            clusters = [ret_files]
        else:
            # Parse clustering results
            with open(clufile, 'r') as f:
                lines = [line.strip() for line in f.readlines() if line.strip()]

            clusters = []
            for line in lines:
                cluster_files = [os.path.join(ret_dir, f.replace('.pdb', '.ret')) for f in line.split()]
                # Filter to existing files
                cluster_files = [f for f in cluster_files if os.path.isfile(f)]
                if cluster_files:
                    clusters.append(cluster_files)

            print(f"Found {len(clusters)} clusters")

        # Step 3: Generate models for each cluster (up to max_models)
        print(f"Step 3: Generating up to {max_models} diverse models...")

        arena = os.path.join(exp_dir, 'Arena', 'Arena')
        generated_models = 0

        for i, cluster in enumerate(clusters[:max_models]):
            if generated_models >= max_models:
                break

            print(f"Processing cluster {i+1}/{min(len(clusters), max_models)}...")

            # Selection for this cluster
            save_prefix = os.path.join(folddir, f'sel_{i+1}')
            optsaveprefix = os.path.join(folddir, f'opt_{i+1}')
            ret_str = ' '.join(cluster)

            # Selection
            cmd = f'python {selpython} {fasta_file} {config_sel} {save_prefix} {ret_str}'
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=exp_dir)
            output, error = p.communicate()

            # Optimization
            cmd = f'python {optpython} {fasta_file} {optsaveprefix} {ret_dir} {save_prefix} {foldconfig}'
            p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=exp_dir)
            output, error = p.communicate()

            # Find optimized model
            opt_files = [f for f in os.listdir(folddir) if f.startswith(f'opt_{i+1}')]
            if not opt_files:
                print(f"Warning: No optimized model found for cluster {i+1}")
                continue

            cgpdb = os.path.join(folddir, opt_files[0])
            savepdb = os.path.join(refdir, f'model_{i+1}.pdb')

            # Structure relaxation
            if os.path.isfile(arena):
                cmd = f'{arena} {cgpdb} {savepdb} 7'
                p = Popen(cmd, shell=True, stdin=PIPE, stdout=PIPE, stderr=STDOUT, cwd=exp_dir)
                output, error = p.communicate()

                if os.path.isfile(savepdb):
                    print(f"Model {i+1} saved to: {savepdb}")
                    generated_models += 1
                else:
                    print(f"Warning: Relaxation failed for model {i+1}, using coarse-grained")
                    import shutil
                    shutil.copy2(cgpdb, savepdb)
                    generated_models += 1
            else:
                print(f"Warning: Arena not found, using coarse-grained model {i+1}")
                import shutil
                shutil.copy2(cgpdb, savepdb)
                generated_models += 1

        print(f"\nEnsemble RNA structure prediction completed!")
        print(f"Generated {generated_models} diverse models")
        print(f"Output directory: {output_dir}")
        print(f"Models saved in: {refdir}")
        print(f"Clustering results: {clufile if os.path.isfile(clufile) else 'Not available'}")

        return generated_models > 0

    except Exception as e:
        print(f"Error during ensemble prediction: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser(description='DRfold2 Ensemble RNA Structure Prediction')
    parser.add_argument('--input', '-i', default='examples/data/test_sequence.fasta',
                       help='Input FASTA file (default: examples/data/test_sequence.fasta)')
    parser.add_argument('--output', '-o', default='results/ensemble_prediction',
                       help='Output directory (default: results/ensemble_prediction)')
    parser.add_argument('--device', '-d', default='cpu', choices=['cpu', 'cuda'],
                       help='Device for computation (default: cpu)')
    parser.add_argument('--max-models', '-m', type=int, default=5,
                       help='Maximum number of models to generate (default: 5)')

    args = parser.parse_args()

    # Check input file
    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    print("DRfold2 Ensemble RNA Structure Prediction")
    print("=" * 45)
    print(f"Input FASTA: {args.input}")
    print(f"Output directory: {args.output}")
    print(f"Device: {args.device}")
    print(f"Max models: {args.max_models}")
    print()

    success = run_ensemble_prediction(args.input, args.output, args.device, args.max_models)

    if success:
        print("\n✓ Ensemble prediction completed successfully!")
    else:
        print("\n✗ Ensemble prediction failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()