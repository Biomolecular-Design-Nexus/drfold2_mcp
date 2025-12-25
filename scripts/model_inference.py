#!/usr/bin/env python3
"""
Script: model_inference.py
Description: Individual DRfold2 model inference and analysis

Original Use Case: examples/use_case_4_model_inference.py
Dependencies Removed: Simplified model loading with better fallbacks

Usage:
    python scripts/model_inference.py --input <input_file> --output <output_dir>

Example:
    python scripts/model_inference.py --input examples/data/test_sequence.fasta --output results/inference --model cfg_95
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import os
import sys
import subprocess
import tempfile
import json
import pickle
from pathlib import Path
from typing import Union, Optional, Dict, Any, List

# Essential packages (if available)
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# ==============================================================================
# Configuration
# ==============================================================================
DEFAULT_CONFIG = {
    "model_config": "cfg_95",
    "available_models": ["cfg_95", "cfg_96", "cfg_97", "cfg_99"],
    "device": "cpu",
    "use_mock": False,
    "timeout": 300,
    "analyze_output": True,
    "output_formats": ["ret", "pkl"],
    "mock_data_size": 1000  # Size of mock tensor data
}

# ==============================================================================
# Path Configuration
# ==============================================================================
SCRIPT_DIR = Path(__file__).parent
MCP_ROOT = SCRIPT_DIR.parent
REPO_PATH = MCP_ROOT / "repo" / "DRfold2"

# ==============================================================================
# Shared Functions (reuse from basic_prediction)
# ==============================================================================
try:
    from .basic_prediction import (
        load_fasta, validate_rna_sequence, check_drfold2_availability
    )
except ImportError:
    # Inline simplified versions
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

    def check_drfold2_availability() -> Dict[str, Any]:
        status = {
            "repo_available": REPO_PATH.exists(),
            "model_available": False,
            "available_models": [],
            "repo_path": str(REPO_PATH)
        }
        if status["repo_available"]:
            for model in DEFAULT_CONFIG["available_models"]:
                model_path = REPO_PATH / "model_hub" / model
                if model_path.exists():
                    status["available_models"].append(model)
            status["model_available"] = len(status["available_models"]) > 0
        return status

# ==============================================================================
# Model Inference Functions
# ==============================================================================
def generate_mock_inference_data(sequence: str, model_config: str, output_dir: Path) -> Dict[str, Any]:
    """Generate mock inference data for testing."""
    import random
    random.seed(hash(sequence + model_config) % 2**32)

    seq_length = len(sequence)

    # Generate mock data structures
    mock_data = {
        "sequence": sequence,
        "model_config": model_config,
        "sequence_length": seq_length
    }

    # Create mock prediction tensors (if numpy available)
    if NUMPY_AVAILABLE:
        mock_data.update({
            "distance_map": np.random.random((seq_length, seq_length)) * 20,
            "contact_map": np.random.random((seq_length, seq_length)),
            "coordinates": np.random.random((seq_length, 3)) * 100,
            "angles": np.random.random((seq_length, 3)) * 360,
            "confidence": np.random.random(seq_length) * 0.5 + 0.5
        })
    else:
        # Use plain lists if numpy not available
        mock_data.update({
            "distance_map": [[random.random() * 20 for _ in range(seq_length)] for _ in range(seq_length)],
            "contact_map": [[random.random() for _ in range(seq_length)] for _ in range(seq_length)],
            "coordinates": [[random.random() * 100 for _ in range(3)] for _ in range(seq_length)],
            "angles": [[random.random() * 360 for _ in range(3)] for _ in range(seq_length)],
            "confidence": [random.random() * 0.5 + 0.5 for _ in range(seq_length)]
        })

    # Save mock .ret file (pickle format)
    ret_file = output_dir / f"{model_config}_mock.ret"
    try:
        with open(ret_file, 'wb') as f:
            pickle.dump(mock_data, f)
    except Exception as e:
        print(f"Warning: Could not save mock .ret file: {e}")

    # Save mock .pkl file (raw data)
    pkl_file = output_dir / f"{model_config}_raw.pkl"
    try:
        raw_data = {
            "model_output": mock_data,
            "metadata": {
                "model": model_config,
                "sequence_length": seq_length,
                "mock": True
            }
        }
        with open(pkl_file, 'wb') as f:
            pickle.dump(raw_data, f)
    except Exception as e:
        print(f"Warning: Could not save mock .pkl file: {e}")

    return mock_data

def analyze_inference_output(output_dir: Path, model_config: str) -> Dict[str, Any]:
    """Analyze the output files from model inference."""
    analysis = {
        "files_found": [],
        "file_details": {},
        "data_summary": {},
        "issues": []
    }

    # Look for output files
    output_files = list(output_dir.glob(f"{model_config}*"))
    analysis["files_found"] = [f.name for f in output_files]

    for file_path in output_files:
        file_info = {
            "size_bytes": file_path.stat().st_size,
            "extension": file_path.suffix,
            "readable": False,
            "data_type": None
        }

        # Try to analyze file content
        try:
            if file_path.suffix in ['.ret', '.pkl']:
                with open(file_path, 'rb') as f:
                    data = pickle.load(f)
                file_info["readable"] = True
                file_info["data_type"] = type(data).__name__

                if isinstance(data, dict):
                    file_info["dict_keys"] = list(data.keys())
                    # Analyze data content
                    for key, value in data.items():
                        if hasattr(value, 'shape'):
                            file_info[f"{key}_shape"] = value.shape
                        elif isinstance(value, (list, tuple)):
                            file_info[f"{key}_length"] = len(value)
                        elif isinstance(value, (int, float, str)):
                            file_info[f"{key}_value"] = str(value)[:100]  # Limit length

        except Exception as e:
            file_info["error"] = str(e)
            analysis["issues"].append(f"Could not read {file_path.name}: {e}")

        analysis["file_details"][file_path.name] = file_info

    # Generate summary
    total_size = sum(info.get("size_bytes", 0) for info in analysis["file_details"].values())
    readable_files = sum(1 for info in analysis["file_details"].values() if info.get("readable", False))

    analysis["data_summary"] = {
        "total_files": len(output_files),
        "total_size_bytes": total_size,
        "readable_files": readable_files,
        "file_types": list(set(info.get("extension", "unknown") for info in analysis["file_details"].values()))
    }

    return analysis

def check_model_availability(model_config: str) -> Dict[str, Any]:
    """Check if specific model is available."""
    model_info = {
        "model_config": model_config,
        "available": False,
        "script_path": None,
        "model_path": None,
        "issues": []
    }

    if not REPO_PATH.exists():
        model_info["issues"].append("DRfold2 repository not found")
        return model_info

    # Check model script
    script_path = REPO_PATH / model_config / "test_modeldir.py"
    if script_path.exists():
        model_info["script_path"] = str(script_path)
    else:
        model_info["issues"].append(f"Model script not found: {script_path}")

    # Check model directory
    model_path = REPO_PATH / "model_hub" / model_config
    if model_path.exists():
        model_info["model_path"] = str(model_path)
        model_info["available"] = script_path.exists()
    else:
        model_info["issues"].append(f"Model directory not found: {model_path}")

    return model_info

# ==============================================================================
# Core Inference Function
# ==============================================================================
def run_model_inference(
    input_file: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for individual model inference.

    Args:
        input_file: Path to input FASTA file
        output_dir: Directory to save outputs (optional)
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - result: Inference results
            - output_dir: Path to output directory
            - metadata: Execution metadata
            - success: Whether inference succeeded

    Example:
        >>> result = run_model_inference("input.fasta", "output_dir", {"model_config": "cfg_95"})
        >>> print(result['result']['model_info'])
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
        output_path = Path("model_inference")

    output_path.mkdir(parents=True, exist_ok=True)

    # Check model availability
    model_config = config["model_config"]
    model_info = check_model_availability(model_config)
    drfold2_status = check_drfold2_availability()

    result_data = {
        "sequence": sequence,
        "sequence_length": len(sequence),
        "sequence_header": header,
        "model_config": model_config,
        "model_info": model_info,
        "drfold2_status": drfold2_status,
        "config": config,
        "inference_method": None,
        "output_files": []
    }

    success = False

    # Try real model inference if available
    if not config.get("use_mock", False) and model_info["available"]:
        try:
            print(f"Running DRfold2 model inference with {model_config}...")
            success = _run_drfold2_inference(
                input_file, output_path, config, model_info
            )
            if success:
                result_data["inference_method"] = "drfold2"
        except Exception as e:
            print(f"DRfold2 inference failed: {e}")
            success = False

    # Fall back to mock inference
    if not success:
        if config.get("use_mock", False) or not model_info["available"]:
            print("Generating mock inference data...")
            mock_data = generate_mock_inference_data(sequence, model_config, output_path)
            if mock_data:
                success = True
                result_data["inference_method"] = "mock"

    # Analyze outputs if requested
    if success and config.get("analyze_output", True):
        analysis = analyze_inference_output(output_path, model_config)
        result_data["output_analysis"] = analysis
        result_data["output_files"] = analysis["files_found"]

    return {
        "result": result_data,
        "output_dir": str(output_path) if success else None,
        "metadata": {
            "input_file": str(input_file),
            "config": config,
            "model_available": model_info["available"],
            "drfold2_available": drfold2_status["repo_available"],
            "success": success
        },
        "success": success
    }

def _run_drfold2_inference(
    input_file: Path, output_dir: Path, config: Dict, model_info: Dict
) -> bool:
    """Run actual DRfold2 model inference."""
    try:
        model_config = config["model_config"]
        device = config["device"]

        # Set up command
        script_path = model_info["script_path"]
        model_path = model_info["model_path"]
        output_prefix = output_dir / f"{model_config}_"

        cmd = [
            sys.executable, script_path, device,
            str(input_file), str(output_prefix), model_path
        ]

        print(f"Running: {' '.join(cmd)}")

        # Run inference
        result = subprocess.run(
            cmd, cwd=str(REPO_PATH), capture_output=True,
            text=True, timeout=config.get("timeout", 300)
        )

        if result.returncode != 0:
            print(f"Model inference failed:")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return False

        # Check for output files
        output_files = list(output_dir.glob(f"{model_config}*"))
        return len(output_files) > 0

    except subprocess.TimeoutExpired:
        print("Model inference timed out")
        return False
    except Exception as e:
        print(f"Model inference failed: {e}")
        return False

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
    parser.add_argument('--model', '-m', default='cfg_95',
                       choices=['cfg_95', 'cfg_96', 'cfg_97', 'cfg_99'],
                       help='Model configuration to use')
    parser.add_argument('--device', '-d', choices=['cpu', 'cuda'], default='cpu',
                       help='Device for computation')
    parser.add_argument('--use-mock', action='store_true', help='Use mock inference for testing')
    parser.add_argument('--analyze', action='store_true', help='Analyze output files')

    args = parser.parse_args()

    # Load config if provided
    config = {}
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Override config with CLI arguments
    config.update({
        "model_config": args.model,
        "device": args.device,
        "use_mock": args.use_mock,
        "analyze_output": args.analyze
    })

    # Check model availability
    if not args.use_mock:
        model_info = check_model_availability(args.model)
        if not model_info["available"]:
            print(f"❌ Model {args.model} is not available:")
            for issue in model_info["issues"]:
                print(f"   - {issue}")
            print("💡 Use --use-mock for testing without models")
            response = input("Continue with mock inference? (y/N): ")
            if response.lower() != 'y':
                sys.exit(1)
            config["use_mock"] = True

    try:
        # Run inference
        result = run_model_inference(
            input_file=args.input,
            output_dir=args.output,
            config=config
        )

        if result["success"]:
            print(f"✅ Success: Model inference completed")
            print(f"Output directory: {result['output_dir']}")
            print(f"Method: {result['result']['inference_method']}")
            print(f"Model: {result['result']['model_config']}")

            output_files = result['result'].get('output_files', [])
            print(f"Output files: {len(output_files)}")

            if args.analyze and 'output_analysis' in result['result']:
                analysis = result['result']['output_analysis']
                print(f"Total size: {analysis['data_summary']['total_size_bytes']} bytes")
                print(f"Readable files: {analysis['data_summary']['readable_files']}")
        else:
            print(f"❌ Failed: Model inference failed")
            if not result['metadata']['model_available']:
                print("💡 Tip: Try --use-mock for testing without models")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()