"""
DRfold2-specific utility functions.

These functions interface with the DRfold2 repository and provide
simplified access to models and functionality.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional


# Default configuration
DEFAULT_MODELS = ["cfg_95", "cfg_96", "cfg_97", "cfg_99"]
REPO_RELATIVE_PATH = Path("repo") / "DRfold2"


def get_repo_path(base_path: Optional[Path] = None) -> Path:
    """
    Get the path to the DRfold2 repository.

    Args:
        base_path: Base path to search from (defaults to script location)

    Returns:
        Path to DRfold2 repository
    """
    if base_path is None:
        # Try to find repo relative to this file
        base_path = Path(__file__).parent.parent.parent

    repo_path = base_path / REPO_RELATIVE_PATH

    # Also try without the nested structure
    if not repo_path.exists():
        alt_path = base_path / "repo" / "DRfold2"
        if alt_path.exists():
            repo_path = alt_path

    return repo_path


def check_drfold2_availability(base_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Check DRfold2 repository and model availability.

    Args:
        base_path: Base path to search from

    Returns:
        Dictionary with availability information
    """
    repo_path = get_repo_path(base_path)

    status = {
        "repo_available": False,
        "repo_path": str(repo_path),
        "model_hub_available": False,
        "model_hub_path": None,
        "arena_available": False,
        "arena_path": None,
        "available_models": [],
        "missing_models": [],
        "scripts_available": [],
        "missing_scripts": []
    }

    # Check repository exists
    if repo_path.exists() and repo_path.is_dir():
        status["repo_available"] = True

        # Check model hub
        model_hub_path = repo_path / "model_hub"
        if model_hub_path.exists():
            status["model_hub_available"] = True
            status["model_hub_path"] = str(model_hub_path)

            # Check individual models
            for model_name in DEFAULT_MODELS:
                model_path = model_hub_path / model_name
                if model_path.exists():
                    status["available_models"].append(model_name)
                else:
                    status["missing_models"].append(model_name)

        # Check arena executable
        arena_path = repo_path / "Arena" / "Arena"
        if arena_path.exists():
            status["arena_available"] = True
            status["arena_path"] = str(arena_path)

        # Check model scripts
        for model_name in DEFAULT_MODELS:
            script_path = repo_path / model_name / "test_modeldir.py"
            if script_path.exists():
                status["scripts_available"].append(model_name)
            else:
                status["missing_scripts"].append(model_name)

    return status


def get_available_models(base_path: Optional[Path] = None) -> List[str]:
    """
    Get list of available model configurations.

    Args:
        base_path: Base path to search from

    Returns:
        List of available model names
    """
    status = check_drfold2_availability(base_path)
    return status["available_models"]


def get_model_info(model_name: str, base_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get detailed information about a specific model.

    Args:
        model_name: Model configuration name
        base_path: Base path to search from

    Returns:
        Dictionary with model information
    """
    repo_path = get_repo_path(base_path)

    info = {
        "model_name": model_name,
        "available": False,
        "script_path": None,
        "script_available": False,
        "model_path": None,
        "model_directory_exists": False,
        "config_files": [],
        "issues": []
    }

    if not repo_path.exists():
        info["issues"].append("DRfold2 repository not found")
        return info

    # Check model script
    script_path = repo_path / model_name / "test_modeldir.py"
    info["script_path"] = str(script_path)
    info["script_available"] = script_path.exists()

    if not info["script_available"]:
        info["issues"].append(f"Model script not found: {script_path}")

    # Check model directory
    model_path = repo_path / "model_hub" / model_name
    info["model_path"] = str(model_path)
    info["model_directory_exists"] = model_path.exists()

    if not info["model_directory_exists"]:
        info["issues"].append(f"Model directory not found: {model_path}")

    # Look for config files
    if model_path.exists():
        for ext in ['.json', '.yaml', '.yml', '.cfg']:
            config_files = list(model_path.glob(f"*{ext}"))
            info["config_files"].extend([str(f) for f in config_files])

        # Also check in the model script directory
        script_dir = repo_path / model_name
        if script_dir.exists():
            for ext in ['.json', '.yaml', '.yml', '.cfg']:
                config_files = list(script_dir.glob(f"*{ext}"))
                info["config_files"].extend([str(f) for f in config_files])

    # Model is available if both script and directory exist
    info["available"] = info["script_available"] and info["model_directory_exists"]

    return info


def check_dependencies() -> Dict[str, Any]:
    """
    Check if required Python dependencies are available.

    Returns:
        Dictionary with dependency information
    """
    deps = {
        "torch": {"available": False, "version": None},
        "numpy": {"available": False, "version": None},
        "openmm": {"available": False, "version": None, "type": None}
    }

    # Check torch
    try:
        import torch
        deps["torch"]["available"] = True
        deps["torch"]["version"] = torch.__version__
    except ImportError:
        pass

    # Check numpy
    try:
        import numpy as np
        deps["numpy"]["available"] = True
        deps["numpy"]["version"] = np.__version__
    except ImportError:
        pass

    # Check OpenMM
    try:
        import openmm
        deps["openmm"]["available"] = True
        deps["openmm"]["type"] = "openmm"
        deps["openmm"]["version"] = openmm.__version__
    except ImportError:
        try:
            import simtk.openmm
            deps["openmm"]["available"] = True
            deps["openmm"]["type"] = "simtk"
            deps["openmm"]["version"] = simtk.openmm.__version__
        except ImportError:
            pass

    return deps


def validate_model_name(model_name: str) -> bool:
    """
    Validate model configuration name.

    Args:
        model_name: Model name to validate

    Returns:
        True if valid model name
    """
    return model_name in DEFAULT_MODELS


def get_model_script_path(model_name: str, base_path: Optional[Path] = None) -> Optional[Path]:
    """
    Get path to model script.

    Args:
        model_name: Model configuration name
        base_path: Base path to search from

    Returns:
        Path to model script or None if not found
    """
    if not validate_model_name(model_name):
        return None

    repo_path = get_repo_path(base_path)
    script_path = repo_path / model_name / "test_modeldir.py"

    return script_path if script_path.exists() else None


def get_model_directory_path(model_name: str, base_path: Optional[Path] = None) -> Optional[Path]:
    """
    Get path to model directory.

    Args:
        model_name: Model configuration name
        base_path: Base path to search from

    Returns:
        Path to model directory or None if not found
    """
    if not validate_model_name(model_name):
        return None

    repo_path = get_repo_path(base_path)
    model_path = repo_path / "model_hub" / model_name

    return model_path if model_path.exists() else None


def get_arena_path(base_path: Optional[Path] = None) -> Optional[Path]:
    """
    Get path to Arena executable.

    Args:
        base_path: Base path to search from

    Returns:
        Path to Arena executable or None if not found
    """
    repo_path = get_repo_path(base_path)
    arena_path = repo_path / "Arena" / "Arena"

    return arena_path if arena_path.exists() else None


def create_model_summary() -> Dict[str, Any]:
    """
    Create a summary of all model availability.

    Returns:
        Dictionary with model availability summary
    """
    drfold2_status = check_drfold2_availability()
    deps = check_dependencies()

    summary = {
        "repository": {
            "available": drfold2_status["repo_available"],
            "path": drfold2_status["repo_path"]
        },
        "models": {
            "available_count": len(drfold2_status["available_models"]),
            "total_count": len(DEFAULT_MODELS),
            "available": drfold2_status["available_models"],
            "missing": drfold2_status["missing_models"]
        },
        "components": {
            "model_hub": drfold2_status["model_hub_available"],
            "arena": drfold2_status["arena_available"],
            "scripts": len(drfold2_status["scripts_available"])
        },
        "dependencies": deps,
        "ready_for_inference": (
            drfold2_status["repo_available"] and
            len(drfold2_status["available_models"]) > 0 and
            deps["torch"]["available"]
        )
    }

    return summary