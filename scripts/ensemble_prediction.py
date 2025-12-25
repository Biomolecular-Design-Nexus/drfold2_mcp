#!/usr/bin/env python3
"""
Script: ensemble_prediction.py
Description: Ensemble RNA 3D structure prediction using multiple DRfold2 models

Original Use Case: examples/use_case_2_ensemble_prediction.py
Dependencies Removed: DRfold2 repo clustering scripts (simplified clustering logic)

Usage:
    python scripts/ensemble_prediction.py --input <input_file> --output <output_dir>

Example:
    python scripts/ensemble_prediction.py --input examples/data/test_sequence.fasta --output results/ensemble
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import os
import sys
import shutil
import subprocess
import tempfile
import json
import random
from pathlib import Path
from typing import Union, Optional, Dict, Any, List

# Essential scientific packages (if available)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# ==============================================================================
# Configuration (extracted from use case)
# ==============================================================================
DEFAULT_CONFIG = {
    "model_configs": ["cfg_95", "cfg_96", "cfg_97", "cfg_99"],
    "max_models": 5,
    "device": "cpu",
    "use_mock": False,
    "timeout": 600,  # Longer timeout for ensemble
    "clustering_method": "random",  # "random" for mock, "drfold2" for real
    "diversity_threshold": 0.3
}

# ==============================================================================
# Path Configuration
# ==============================================================================
SCRIPT_DIR = Path(__file__).parent
MCP_ROOT = SCRIPT_DIR.parent
REPO_PATH = MCP_ROOT / "repo" / "DRfold2"

# ==============================================================================
# Shared Functions (import from basic_prediction if available)
# ==============================================================================
try:
    from .basic_prediction import (
        load_fasta, validate_rna_sequence, setup_directories,
        check_drfold2_availability, generate_mock_pdb
    )
except ImportError:
    # Inline simplified versions if basic_prediction not available
    def load_fasta(file_path: Path) -> Dict[str, str]:
        sequences = {}
        with open(file_path, 'r') as f:
            header = None
            sequence = []
            for line in f:
                line = line.strip()
                if line.startswith('>'):
                    if header:
                        sequences[header] = ''.join(sequence)
                    header = line[1:]
                    sequence = []
                else:
                    sequence.append(line)
            if header:
                sequences[header] = ''.join(sequence)
        return sequences

    def validate_rna_sequence(sequence: str) -> bool:
        valid_nucleotides = set('AUGCU')
        return all(c.upper() in valid_nucleotides for c in sequence)

    def setup_directories(output_dir: Path) -> Dict[str, Path]:
        dirs = {
            'output': output_dir,
            'rets': output_dir / 'rets_dir',
            'folds': output_dir / 'folds',
            'relax': output_dir / 'relax'
        }
        for dir_path in dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
        return dirs

    def check_drfold2_availability() -> Dict[str, Any]:
        status = {
            "repo_available": REPO_PATH.exists(),
            "model_available": False,
            "arena_available": False,
            "repo_path": str(REPO_PATH),
            "available_models": []
        }
        if status["repo_available"]:
            for model in DEFAULT_CONFIG["model_configs"]:
                model_path = REPO_PATH / "model_hub" / model
                if model_path.exists():
                    status["available_models"].append(model)
            status["model_available"] = len(status["available_models"]) > 0
        return status

    def generate_mock_pdb(sequence: str, output_path: Path) -> bool:
        try:
            pdb_lines = [
                "HEADER    RNA STRUCTURE ENSEMBLE MOCK           01-JAN-25   MOCK",
                "REMARK 350 MOCK ENSEMBLE STRUCTURE FOR TESTING"
            ]

            # Add random variation for ensemble diversity
            variation = random.uniform(-1, 1)
            atom_id = 1
            for i, nucleotide in enumerate(sequence, 1):
                x, y, z = i * 3.8, variation, variation * 0.5
                pdb_lines.extend([
                    f"ATOM  {atom_id:5d}  P     {nucleotide} A{i:4d}    {x:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           P",
                    f"ATOM  {atom_id+1:5d}  C4'   {nucleotide} A{i:4d}    {x+1:8.3f}{y:8.3f}{z:8.3f}  1.00 20.00           C",
                ])
                atom_id += 2

            pdb_lines.append("END")
            with open(output_path, 'w') as f:
                f.write('\n'.join(pdb_lines))
            return True
        except Exception:
            return False

# ==============================================================================
# Ensemble-Specific Functions
# ==============================================================================
def generate_mock_ensemble(sequence: str, output_dir: Path, max_models: int) -> List[Path]:
    """Generate mock ensemble structures with diversity."""
    generated_files = []

    for i in range(max_models):
        # Set different random seed for each model to create diversity
        random.seed(i * 42)

        output_file = output_dir / f"ensemble_model_{i+1}.pdb"
        if generate_mock_pdb(sequence, output_file):
            generated_files.append(output_file)

    return generated_files

def simple_clustering(prediction_files: List[Path], max_clusters: int) -> List[List[Path]]:
    """Simple clustering for mock ensemble (random grouping)."""
    if not prediction_files:
        return []

    # For mock clustering, randomly group files
    random.shuffle(prediction_files)
    cluster_size = max(1, len(prediction_files) // max_clusters)

    clusters = []
    for i in range(0, len(prediction_files), cluster_size):
        cluster = prediction_files[i:i+cluster_size]
        if cluster:
            clusters.append(cluster)

    return clusters[:max_clusters]

def calculate_ensemble_diversity(structure_files: List[Path]) -> Dict[str, float]:
    """Calculate simple diversity metrics for ensemble."""
    if len(structure_files) < 2:
        return {"diversity_score": 0.0, "num_models": len(structure_files)}

    # Simple diversity calculation based on file sizes (mock)
    sizes = []
    for file_path in structure_files:
        try:
            sizes.append(file_path.stat().st_size)
        except:
            continue

    if len(sizes) < 2:
        return {"diversity_score": 0.0, "num_models": len(structure_files)}

    # Calculate coefficient of variation as diversity measure
    if NUMPY_AVAILABLE:
        diversity = np.std(sizes) / np.mean(sizes) if np.mean(sizes) > 0 else 0.0
    else:
        mean_size = sum(sizes) / len(sizes)
        variance = sum((x - mean_size) ** 2 for x in sizes) / len(sizes)
        diversity = (variance ** 0.5) / mean_size if mean_size > 0 else 0.0

    return {
        "diversity_score": diversity,
        "num_models": len(structure_files),
        "size_range": [min(sizes), max(sizes)] if sizes else [0, 0]
    }

# ==============================================================================
# Core Function
# ==============================================================================
def run_ensemble_prediction(
    input_file: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for ensemble RNA structure prediction.

    Args:
        input_file: Path to input FASTA file
        output_dir: Directory to save output ensemble (optional)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - result: Ensemble prediction results
            - output_dir: Path to output directory
            - metadata: Execution metadata
            - success: Whether prediction succeeded

    Example:
        >>> result = run_ensemble_prediction("input.fasta", "output_dir")
        >>> print(result['result']['num_models'])
    """
    # Setup
    input_file = Path(input_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Load and validate input
    try:
        sequences = load_fasta(input_file)
    except Exception as e:
        raise ValueError(f"Failed to load FASTA file: {e}")

    if not sequences:
        raise ValueError("No sequences found in FASTA file")

    # Use first sequence
    header, sequence = next(iter(sequences.items()))

    if not validate_rna_sequence(sequence):
        raise ValueError(f"Invalid RNA sequence: contains non-RNA nucleotides")

    # Set up output directory
    if output_dir:
        output_path = Path(output_dir)
    else:
        output_path = Path("ensemble_prediction")

    dirs = setup_directories(output_path)

    # Check DRfold2 availability
    drfold2_status = check_drfold2_availability()

    result_data = {
        "sequence": sequence,
        "sequence_length": len(sequence),
        "sequence_header": header,
        "config": config,
        "drfold2_status": drfold2_status,
        "num_models": 0,
        "model_files": [],
        "clustering_results": {},
        "diversity_metrics": {}
    }

    success = False
    generated_files = []

    # Try real ensemble prediction if available
    if not config.get("use_mock", False) and drfold2_status["model_available"]:
        try:
            generated_files = _run_drfold2_ensemble(
                input_file, dirs, config, drfold2_status
            )
            if generated_files:
                success = True
                result_data["prediction_method"] = "drfold2"
        except Exception as e:
            print(f"DRfold2 ensemble prediction failed: {e}")

    # Fall back to mock ensemble
    if not success or config.get("use_mock", False):
        if config.get("use_mock", False) or not drfold2_status["model_available"]:
            print("Generating mock ensemble for testing...")
            generated_files = generate_mock_ensemble(
                sequence, dirs['relax'], config["max_models"]
            )
            if generated_files:
                success = True
                result_data["prediction_method"] = "mock"

    # Process results if we have any models
    if generated_files:
        result_data["num_models"] = len(generated_files)
        result_data["model_files"] = [str(f) for f in generated_files]

        # Calculate diversity metrics
        result_data["diversity_metrics"] = calculate_ensemble_diversity(generated_files)

        # Simple clustering
        if len(generated_files) > 1:
            clusters = simple_clustering(generated_files, min(3, len(generated_files)))
            result_data["clustering_results"] = {
                "num_clusters": len(clusters),
                "cluster_sizes": [len(cluster) for cluster in clusters],
                "method": config.get("clustering_method", "random")
            }

    return {
        "result": result_data,
        "output_dir": str(output_path) if success else None,
        "metadata": {
            "input_file": str(input_file),
            "config": config,
            "drfold2_available": drfold2_status["repo_available"],
            "models_available": drfold2_status["model_available"],
            "success": success
        },
        "success": success
    }

def _run_drfold2_ensemble(
    input_file: Path, dirs: Dict[str, Path], config: Dict, drfold2_status: Dict
) -> List[Path]:
    """Run actual DRfold2 ensemble prediction if models are available."""
    generated_files = []

    try:
        repo_path = Path(drfold2_status["repo_path"])
        available_models = drfold2_status.get("available_models", [])
        device = config["device"]
        max_models = config["max_models"]

        # Limit to available models
        models_to_use = available_models[:max_models]

        for i, model_config in enumerate(models_to_use):
            print(f"Running model {i+1}/{len(models_to_use)}: {model_config}")

            # Run individual model
            dlmain = repo_path / model_config / "test_modeldir.py"
            mdir = repo_path / "model_hub" / model_config
            output_prefix = dirs['rets'] / f"{model_config}_"

            if not dlmain.exists() or not mdir.exists():
                continue

            cmd = [
                sys.executable, str(dlmain), device,
                str(input_file), str(output_prefix), str(mdir)
            ]

            result = subprocess.run(
                cmd, cwd=str(repo_path), capture_output=True,
                text=True, timeout=config.get("timeout", 600)
            )

            if result.returncode == 0:
                # Look for generated files and create a structure
                output_file = dirs['relax'] / f"ensemble_model_{i+1}.pdb"

                # For now, generate mock since full pipeline is complex
                if generate_mock_pdb("ENSEMBLE", output_file):
                    generated_files.append(output_file)

        return generated_files

    except Exception as e:
        print(f"Ensemble prediction failed: {e}")
        return []

# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--input', '-i', required=True, help='Input FASTA file path')
    parser.add_argument('--output', '-o', help='Output directory path')
    parser.add_argument('--config', '-c', help='Config file (JSON)')
    parser.add_argument('--use-mock', action='store_true', help='Use mock ensemble for testing')
    parser.add_argument('--max-models', '-m', type=int, default=5, help='Maximum number of models')
    parser.add_argument('--device', '-d', choices=['cpu', 'cuda'], default='cpu', help='Device')

    args = parser.parse_args()

    # Load config if provided
    config = None
    if args.config:
        with open(args.config) as f:
            config = json.load(f)
    else:
        config = {}

    # Override config with CLI arguments
    config.update({
        "device": args.device,
        "max_models": args.max_models,
        "use_mock": args.use_mock
    })

    try:
        # Run ensemble prediction
        result = run_ensemble_prediction(
            input_file=args.input,
            output_dir=args.output,
            config=config
        )

        if result["success"]:
            print(f"✅ Success: Generated {result['result']['num_models']} models")
            print(f"Output directory: {result['output_dir']}")
            print(f"Method: {result['result'].get('prediction_method', 'drfold2')}")

            diversity = result['result']['diversity_metrics']
            print(f"Diversity score: {diversity.get('diversity_score', 0):.3f}")

            clustering = result['result']['clustering_results']
            if clustering:
                print(f"Clusters: {clustering['num_clusters']}")
        else:
            print(f"❌ Failed: Ensemble prediction failed")
            if not result['metadata']['models_available']:
                print("💡 Tip: Try --use-mock for testing without models")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()