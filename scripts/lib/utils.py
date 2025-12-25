"""
General utility functions for MCP scripts.

These functions provide common utilities for file management, formatting, etc.
"""
import os
import shutil
import time
from pathlib import Path
from typing import Union, Dict, Any, List, Optional


def setup_directories(base_dir: Union[str, Path],
                     subdirs: Optional[List[str]] = None) -> Dict[str, Path]:
    """
    Create directory structure for outputs.

    Args:
        base_dir: Base directory path
        subdirs: List of subdirectory names to create

    Returns:
        Dictionary mapping directory names to Path objects
    """
    base_dir = Path(base_dir)
    base_dir.mkdir(parents=True, exist_ok=True)

    dirs = {"base": base_dir}

    if subdirs:
        for subdir in subdirs:
            dir_path = base_dir / subdir
            dir_path.mkdir(parents=True, exist_ok=True)
            dirs[subdir] = dir_path

    return dirs


def cleanup_files(file_paths: List[Union[str, Path]],
                 ignore_errors: bool = True) -> int:
    """
    Clean up temporary files.

    Args:
        file_paths: List of file paths to remove
        ignore_errors: Whether to ignore deletion errors

    Returns:
        Number of files successfully removed
    """
    removed_count = 0

    for file_path in file_paths:
        try:
            file_path = Path(file_path)
            if file_path.exists():
                if file_path.is_file():
                    file_path.unlink()
                    removed_count += 1
                elif file_path.is_dir():
                    shutil.rmtree(file_path)
                    removed_count += 1
        except Exception as e:
            if not ignore_errors:
                raise e

    return removed_count


def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted duration string
    """
    if seconds < 1:
        return f"{seconds * 1000:.0f} ms"
    elif seconds < 60:
        return f"{seconds:.1f} s"
    elif seconds < 3600:
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        return f"{minutes:.0f}m {remaining_seconds:.0f}s"
    else:
        hours = seconds // 3600
        remaining_minutes = (seconds % 3600) // 60
        return f"{hours:.0f}h {remaining_minutes:.0f}m"


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Get detailed file information.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information
    """
    file_path = Path(file_path)

    info = {
        "path": str(file_path),
        "exists": file_path.exists(),
        "size_bytes": 0,
        "size_formatted": "0 B",
        "is_file": False,
        "is_dir": False,
        "extension": "",
        "name": file_path.name,
        "parent": str(file_path.parent)
    }

    if file_path.exists():
        stat = file_path.stat()
        info.update({
            "size_bytes": stat.st_size,
            "size_formatted": _format_bytes(stat.st_size),
            "is_file": file_path.is_file(),
            "is_dir": file_path.is_dir(),
            "extension": file_path.suffix,
            "created": stat.st_ctime,
            "modified": stat.st_mtime,
            "accessed": stat.st_atime
        })

    return info


def _format_bytes(size_bytes: int) -> str:
    """Format bytes in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def create_temp_directory(prefix: str = "drfold2_mcp_") -> Path:
    """
    Create a temporary directory.

    Args:
        prefix: Prefix for directory name

    Returns:
        Path to temporary directory
    """
    import tempfile
    temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
    return temp_dir


def copy_file(src: Union[str, Path], dst: Union[str, Path],
             create_dirs: bool = True) -> bool:
    """
    Copy file with error handling.

    Args:
        src: Source file path
        dst: Destination file path
        create_dirs: Whether to create destination directories

    Returns:
        True if copy succeeded
    """
    try:
        src = Path(src)
        dst = Path(dst)

        if not src.exists():
            return False

        if create_dirs:
            dst.parent.mkdir(parents=True, exist_ok=True)

        shutil.copy2(src, dst)
        return True

    except Exception:
        return False


def find_files(directory: Union[str, Path],
               pattern: str = "*",
               recursive: bool = False) -> List[Path]:
    """
    Find files matching pattern.

    Args:
        directory: Directory to search
        pattern: Glob pattern to match
        recursive: Whether to search recursively

    Returns:
        List of matching file paths
    """
    directory = Path(directory)

    if not directory.exists() or not directory.is_dir():
        return []

    try:
        if recursive:
            return list(directory.rglob(pattern))
        else:
            return list(directory.glob(pattern))
    except Exception:
        return []


def ensure_file_extension(file_path: Union[str, Path],
                         extension: str) -> Path:
    """
    Ensure file has specified extension.

    Args:
        file_path: File path
        extension: Required extension (e.g., '.pdb')

    Returns:
        Path with correct extension
    """
    file_path = Path(file_path)

    if not extension.startswith('.'):
        extension = '.' + extension

    if file_path.suffix.lower() != extension.lower():
        file_path = file_path.with_suffix(extension)

    return file_path


class Timer:
    """Simple timer context manager."""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time

    def elapsed(self) -> float:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return 0.0
        if self.end_time is None:
            return time.time() - self.start_time
        return self.duration

    def elapsed_formatted(self) -> str:
        """Get elapsed time in formatted string."""
        return format_duration(self.elapsed())


def check_disk_space(path: Union[str, Path], required_mb: float = 100) -> bool:
    """
    Check if sufficient disk space is available.

    Args:
        path: Path to check (file or directory)
        required_mb: Required space in megabytes

    Returns:
        True if sufficient space available
    """
    try:
        path = Path(path)
        # Find existing parent directory
        check_path = path
        while not check_path.exists() and check_path.parent != check_path:
            check_path = check_path.parent

        if check_path.exists():
            stat = shutil.disk_usage(check_path)
            available_mb = stat.free / (1024 * 1024)
            return available_mb >= required_mb

        return False

    except Exception:
        return True  # Assume OK if we can't check


def safe_remove(file_path: Union[str, Path]) -> bool:
    """
    Safely remove file or directory.

    Args:
        file_path: Path to remove

    Returns:
        True if removal succeeded
    """
    try:
        file_path = Path(file_path)
        if file_path.exists():
            if file_path.is_file():
                file_path.unlink()
            elif file_path.is_dir():
                shutil.rmtree(file_path)
            return True
        return True  # Already doesn't exist

    except Exception:
        return False