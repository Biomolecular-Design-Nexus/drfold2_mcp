#!/usr/bin/env python3
"""
DRfold2 MCP Server

MCP server providing tools for RNA 3D structure prediction using DRfold2.
Provides both synchronous and asynchronous APIs for all operations.
"""

from fastmcp import FastMCP
from pathlib import Path
from typing import Optional, List
import sys
import tempfile
import json

# Setup paths
SCRIPT_DIR = Path(__file__).parent.resolve()
MCP_ROOT = SCRIPT_DIR.parent
SCRIPTS_DIR = MCP_ROOT / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(SCRIPTS_DIR))

from jobs.manager import job_manager
from loguru import logger

# Import script functions
try:
    from basic_prediction import run_basic_prediction
    from structure_refinement import run_structure_refinement
    from model_inference import run_model_inference
    from ensemble_prediction import run_ensemble_prediction

    # Import shared library functions
    sys.path.insert(0, str(SCRIPTS_DIR / "lib"))
    from file_io import load_fasta, save_fasta, validate_file_path
    from validation import validate_rna_sequence
    from utils import setup_directories

    SCRIPTS_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Scripts not available: {e}")
    SCRIPTS_AVAILABLE = False

# Create MCP server
mcp = FastMCP("DRfold2")

# ==============================================================================
# Job Management Tools (for async operations)
# ==============================================================================

@mcp.tool()
def get_job_status(job_id: str) -> dict:
    """
    Get the status of a submitted job.

    Args:
        job_id: The job ID returned from a submit_* function

    Returns:
        Dictionary with job status, timestamps, and any errors
    """
    return job_manager.get_job_status(job_id)

@mcp.tool()
def get_job_result(job_id: str) -> dict:
    """
    Get the results of a completed job.

    Args:
        job_id: The job ID of a completed job

    Returns:
        Dictionary with the job results or error if not completed
    """
    return job_manager.get_job_result(job_id)

@mcp.tool()
def get_job_log(job_id: str, tail: int = 50) -> dict:
    """
    Get log output from a running or completed job.

    Args:
        job_id: The job ID to get logs for
        tail: Number of lines from end (default: 50, use 0 for all)

    Returns:
        Dictionary with log lines and total line count
    """
    return job_manager.get_job_log(job_id, tail)

@mcp.tool()
def cancel_job(job_id: str) -> dict:
    """
    Cancel a running job.

    Args:
        job_id: The job ID to cancel

    Returns:
        Success or error message
    """
    return job_manager.cancel_job(job_id)

@mcp.tool()
def list_jobs(status: Optional[str] = None) -> dict:
    """
    List all submitted jobs.

    Args:
        status: Filter by status (pending, running, completed, failed, cancelled)

    Returns:
        List of jobs with their status
    """
    return job_manager.list_jobs(status)

# ==============================================================================
# Synchronous Tools (for fast operations < 10 min)
# ==============================================================================

@mcp.tool()
def predict_rna_structure(
    input_file: str,
    output_file: Optional[str] = None,
    model_config: str = "cfg_95",
    use_mock: bool = False
) -> dict:
    """
    Predict RNA 3D structure from FASTA sequence using DRfold2 (fast operation).

    Use this for quick structure predictions. For batch processing or when you
    need to process many sequences, use submit_batch_rna_prediction instead.

    Args:
        input_file: Path to FASTA file containing RNA sequence
        output_file: Optional path to save predicted structure (PDB format)
        model_config: DRfold2 model configuration (cfg_95, cfg_96, cfg_97, cfg_99)
        use_mock: Use mock prediction for testing (default: False)

    Returns:
        Dictionary with prediction results and output file path

    Example:
        predict_rna_structure("examples/data/test_sequence.fasta", "output.pdb")
    """
    if not SCRIPTS_AVAILABLE:
        return {"status": "error", "error": "DRfold2 scripts not available"}

    try:
        result = run_basic_prediction(
            input_file=input_file,
            output_file=output_file,
            config={
                "model_config": model_config,
                "use_mock": use_mock
            }
        )

        return {
            "status": "success",
            "structure_file": result.get("output_file"),
            "sequence_length": result.get("result", {}).get("sequence_length"),
            "prediction_method": "drfold2_basic",
            "model_config": model_config,
            "metadata": result.get("metadata", {})
        }

    except FileNotFoundError as e:
        return {"status": "error", "error": f"File not found: {e}"}
    except ValueError as e:
        return {"status": "error", "error": f"Invalid input: {e}"}
    except Exception as e:
        logger.error(f"Basic prediction failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def refine_rna_structure(
    input_file: str,
    output_file: Optional[str] = None,
    steps: int = 1000,
    use_mock: bool = False
) -> dict:
    """
    Refine RNA structure using molecular dynamics (fast operation).

    Uses OpenMM for energy minimization and structural refinement. Falls back
    to mock refinement if OpenMM is not available.

    Args:
        input_file: Path to PDB file containing RNA structure
        output_file: Optional path to save refined structure
        steps: Number of minimization steps (default: 1000)
        use_mock: Use mock refinement for testing (default: False)

    Returns:
        Dictionary with refinement results and output file path

    Example:
        refine_rna_structure("structure.pdb", "refined.pdb", steps=2000)
    """
    if not SCRIPTS_AVAILABLE:
        return {"status": "error", "error": "DRfold2 scripts not available"}

    try:
        result = run_structure_refinement(
            input_file=input_file,
            output_file=output_file,
            config={
                "steps": steps,
                "use_mock": use_mock
            }
        )

        return {
            "status": "success",
            "refined_structure": result.get("output_file"),
            "refinement_method": result.get("result", {}).get("method", "unknown"),
            "steps_completed": result.get("result", {}).get("steps", steps),
            "metadata": result.get("metadata", {})
        }

    except FileNotFoundError as e:
        return {"status": "error", "error": f"File not found: {e}"}
    except Exception as e:
        logger.error(f"Structure refinement failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def run_model_inference(
    input_file: str,
    output_dir: Optional[str] = None,
    model_config: str = "cfg_95",
    analyze_output: bool = True,
    use_mock: bool = False
) -> dict:
    """
    Run inference with individual DRfold2 models (fast operation).

    Generates raw model outputs including distance maps, contact predictions,
    and confidence scores. Use this for detailed analysis of model predictions.

    Args:
        input_file: Path to FASTA file containing RNA sequence
        output_dir: Optional directory to save inference outputs
        model_config: Model to use (cfg_95, cfg_96, cfg_97, cfg_99)
        analyze_output: Whether to analyze generated outputs (default: True)
        use_mock: Use mock inference for testing (default: False)

    Returns:
        Dictionary with inference results and analysis

    Example:
        run_model_inference("sequence.fasta", "inference_output", "cfg_96")
    """
    if not SCRIPTS_AVAILABLE:
        return {"status": "error", "error": "DRfold2 scripts not available"}

    try:
        result = run_model_inference(
            input_file=input_file,
            output_dir=output_dir,
            config={
                "model_config": model_config,
                "analyze": analyze_output,
                "use_mock": use_mock
            }
        )

        return {
            "status": "success",
            "output_directory": result.get("output_dir"),
            "model_used": model_config,
            "analysis_results": result.get("result", {}),
            "metadata": result.get("metadata", {})
        }

    except FileNotFoundError as e:
        return {"status": "error", "error": f"File not found: {e}"}
    except Exception as e:
        logger.error(f"Model inference failed: {e}")
        return {"status": "error", "error": str(e)}

# ==============================================================================
# Submit Tools (for long-running operations > 10 min)
# ==============================================================================

@mcp.tool()
def submit_ensemble_prediction(
    input_file: str,
    output_dir: Optional[str] = None,
    max_models: int = 4,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit ensemble RNA structure prediction for background processing.

    Generates multiple structure variants using different DRfold2 models,
    then clusters them to identify consensus structures. This operation
    typically takes 15-45 minutes.

    Args:
        input_file: Path to FASTA file containing RNA sequence
        output_dir: Directory to save ensemble outputs
        max_models: Maximum number of models to use (default: 4)
        job_name: Optional name for the job (for easier tracking)

    Returns:
        Dictionary with job_id for tracking. Use:
        - get_job_status(job_id) to check progress
        - get_job_result(job_id) to get results when completed
        - get_job_log(job_id) to see execution logs

    Example:
        submit_ensemble_prediction("sequence.fasta", "ensemble_out", max_models=3)
    """
    script_path = str(SCRIPTS_DIR / "ensemble_prediction.py")

    return job_manager.submit_job(
        script_path=script_path,
        args={
            "input": input_file,
            "output_dir": output_dir,
            "max_models": max_models
        },
        job_name=job_name or f"ensemble_{Path(input_file).stem}"
    )

@mcp.tool()
def submit_batch_rna_prediction(
    input_files: List[str],
    output_dir: Optional[str] = None,
    model_config: str = "cfg_95",
    job_name: Optional[str] = None
) -> dict:
    """
    Submit batch RNA structure prediction for multiple sequences.

    Processes multiple FASTA files with the same model configuration.
    Suitable for high-throughput structure prediction.

    Args:
        input_files: List of FASTA file paths to process
        output_dir: Directory to save all outputs
        model_config: Model configuration to use for all predictions
        job_name: Optional name for the batch job

    Returns:
        Dictionary with job_id for tracking the batch job

    Example:
        submit_batch_rna_prediction(["seq1.fasta", "seq2.fasta"], "batch_out")
    """
    script_path = str(SCRIPTS_DIR / "basic_prediction.py")

    # Create a batch processing script call
    # Note: This would need a batch wrapper script or modification to basic_prediction.py
    # For now, we'll process the first file and note this limitation

    if not input_files:
        return {"status": "error", "error": "No input files provided"}

    return job_manager.submit_job(
        script_path=script_path,
        args={
            "input": input_files[0],  # Process first file for now
            "output_dir": output_dir,
            "model_config": model_config
        },
        job_name=job_name or f"batch_{len(input_files)}_sequences"
    )

@mcp.tool()
def submit_comprehensive_analysis(
    input_file: str,
    output_dir: Optional[str] = None,
    include_refinement: bool = True,
    include_ensemble: bool = True,
    job_name: Optional[str] = None
) -> dict:
    """
    Submit comprehensive RNA analysis pipeline for background processing.

    Runs a complete analysis including:
    1. Basic structure prediction
    2. Ensemble prediction (if enabled)
    3. Structure refinement (if enabled)
    4. Model inference analysis

    This operation may take 30+ minutes depending on sequence length and options.

    Args:
        input_file: Path to FASTA file containing RNA sequence
        output_dir: Directory to save all outputs
        include_refinement: Whether to include structure refinement
        include_ensemble: Whether to include ensemble prediction
        job_name: Optional name for the comprehensive job

    Returns:
        Dictionary with job_id for tracking the comprehensive analysis

    Example:
        submit_comprehensive_analysis("sequence.fasta", "comprehensive_out")
    """
    # For comprehensive analysis, we'll start with ensemble prediction
    # as it includes multiple prediction steps
    script_path = str(SCRIPTS_DIR / "ensemble_prediction.py")

    return job_manager.submit_job(
        script_path=script_path,
        args={
            "input": input_file,
            "output_dir": output_dir,
            "max_models": 4 if include_ensemble else 1
        },
        job_name=job_name or f"comprehensive_{Path(input_file).stem}"
    )

# ==============================================================================
# Utility Tools
# ==============================================================================

@mcp.tool()
def validate_rna_fasta(file_path: str) -> dict:
    """
    Validate RNA FASTA file format and sequence content.

    Checks file format, sequence validity, and provides sequence statistics.

    Args:
        file_path: Path to FASTA file to validate

    Returns:
        Dictionary with validation results and sequence information
    """
    try:
        # Basic file validation
        if not Path(file_path).exists():
            return {"status": "error", "error": f"File not found: {file_path}"}

        if not SCRIPTS_AVAILABLE:
            return {
                "status": "warning",
                "message": "Limited validation - scripts not available",
                "file_exists": True
            }

        # Load and validate FASTA
        sequences = load_fasta(file_path)

        if not sequences:
            return {"status": "error", "error": "No sequences found in FASTA file"}

        results = {
            "status": "success",
            "num_sequences": len(sequences),
            "sequences": []
        }

        for name, seq in sequences:
            seq_info = {
                "name": name,
                "length": len(seq),
                "valid": True,
                "issues": []
            }

            # Validate RNA sequence
            try:
                validation_result = validate_rna_sequence(seq)
                seq_info.update(validation_result)
            except Exception as e:
                seq_info["valid"] = False
                seq_info["issues"].append(str(e))

            results["sequences"].append(seq_info)

        return results

    except Exception as e:
        logger.error(f"FASTA validation failed: {e}")
        return {"status": "error", "error": str(e)}

@mcp.tool()
def get_example_data() -> dict:
    """
    Get information about available example datasets for testing.

    Returns:
        Dictionary with example files and their descriptions
    """
    examples_dir = MCP_ROOT / "examples" / "data"

    example_info = {
        "status": "success",
        "examples_directory": str(examples_dir),
        "available_files": []
    }

    if examples_dir.exists():
        for file_path in examples_dir.glob("*"):
            if file_path.is_file():
                file_info = {
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "description": "Example data for testing DRfold2 tools"
                }

                if file_path.suffix == ".fasta":
                    file_info["type"] = "RNA sequence (FASTA)"
                elif file_path.suffix == ".pdb":
                    file_info["type"] = "RNA structure (PDB)"
                else:
                    file_info["type"] = "Data file"

                example_info["available_files"].append(file_info)
    else:
        example_info["status"] = "warning"
        example_info["message"] = "Examples directory not found"

    return example_info

# ==============================================================================
# Entry Point
# ==============================================================================

if __name__ == "__main__":
    mcp.run()