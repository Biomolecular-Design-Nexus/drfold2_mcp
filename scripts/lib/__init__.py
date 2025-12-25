"""
Shared library for DRfold2 MCP scripts.

This library contains common functions extracted and simplified from the
original DRfold2 repository to minimize dependencies while preserving
essential functionality.
"""

from .io import (
    load_fasta,
    save_fasta,
    load_json,
    save_json,
    validate_file_path
)

from .validation import (
    validate_rna_sequence,
    validate_pdb_file,
    check_file_format
)

from .utils import (
    setup_directories,
    cleanup_files,
    format_duration,
    get_file_info
)

from .drfold2 import (
    check_drfold2_availability,
    get_available_models,
    get_model_info
)

__version__ = "1.0.0"
__all__ = [
    # I/O functions
    "load_fasta", "save_fasta", "load_json", "save_json", "validate_file_path",
    # Validation functions
    "validate_rna_sequence", "validate_pdb_file", "check_file_format",
    # Utility functions
    "setup_directories", "cleanup_files", "format_duration", "get_file_info",
    # DRfold2-specific functions
    "check_drfold2_availability", "get_available_models", "get_model_info"
]