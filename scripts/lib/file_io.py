"""
I/O functions for MCP scripts.

These are extracted and simplified from repo code to minimize dependencies.
"""
import json
from pathlib import Path
from typing import Union, Dict, Any, List, Optional


def load_fasta(file_path: Union[str, Path]) -> Dict[str, str]:
    """
    Load FASTA file and return sequences.

    Args:
        file_path: Path to FASTA file

    Returns:
        Dict mapping sequence headers to sequences

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is invalid
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"FASTA file not found: {file_path}")

    sequences = {}

    try:
        with open(file_path, 'r') as f:
            header = None
            sequence = []

            for line_num, line in enumerate(f, 1):
                line = line.strip()

                if not line:
                    continue

                if line.startswith('>'):
                    # Save previous sequence if exists
                    if header is not None:
                        if sequence:
                            sequences[header] = ''.join(sequence)
                        else:
                            raise ValueError(f"Empty sequence for header '{header}' at line {line_num}")

                    # Start new sequence
                    header = line[1:].strip()
                    if not header:
                        raise ValueError(f"Empty header at line {line_num}")

                    sequence = []
                else:
                    # Add to current sequence
                    if header is None:
                        raise ValueError(f"Sequence data before header at line {line_num}")

                    # Remove any whitespace and validate characters
                    clean_line = ''.join(line.split()).upper()
                    sequence.append(clean_line)

            # Save last sequence
            if header is not None:
                if sequence:
                    sequences[header] = ''.join(sequence)
                else:
                    raise ValueError(f"Empty sequence for header '{header}'")

    except Exception as e:
        if isinstance(e, (FileNotFoundError, ValueError)):
            raise
        else:
            raise ValueError(f"Failed to parse FASTA file: {e}")

    if not sequences:
        raise ValueError("No valid sequences found in FASTA file")

    return sequences


def save_fasta(sequences: Dict[str, str], file_path: Union[str, Path],
               line_width: int = 80) -> None:
    """
    Save sequences to FASTA file.

    Args:
        sequences: Dict mapping headers to sequences
        file_path: Output file path
        line_width: Maximum line width for sequence lines
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w') as f:
        for header, sequence in sequences.items():
            f.write(f">{header}\n")

            # Split sequence into lines of specified width
            for i in range(0, len(sequence), line_width):
                f.write(sequence[i:i + line_width] + "\n")


def load_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load JSON file.

    Args:
        file_path: Path to JSON file

    Returns:
        Loaded JSON data
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON format: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load JSON file: {e}")


def save_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """
    Save data to JSON file.

    Args:
        data: Data to save
        file_path: Output file path
        indent: JSON indentation
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
    except Exception as e:
        raise ValueError(f"Failed to save JSON file: {e}")


def validate_file_path(file_path: Union[str, Path],
                      must_exist: bool = True,
                      extensions: Optional[List[str]] = None) -> Path:
    """
    Validate and normalize file path.

    Args:
        file_path: File path to validate
        must_exist: Whether file must already exist
        extensions: List of allowed extensions (e.g., ['.fasta', '.fa'])

    Returns:
        Normalized Path object

    Raises:
        FileNotFoundError: If file doesn't exist and must_exist=True
        ValueError: If extension not allowed
    """
    file_path = Path(file_path)

    if must_exist and not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if extensions:
        if file_path.suffix.lower() not in [ext.lower() for ext in extensions]:
            raise ValueError(f"File extension must be one of {extensions}, got {file_path.suffix}")

    return file_path


def read_text_file(file_path: Union[str, Path]) -> List[str]:
    """
    Read text file and return lines.

    Args:
        file_path: Path to text file

    Returns:
        List of lines (with newlines stripped)
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"Text file not found: {file_path}")

    try:
        with open(file_path, 'r') as f:
            return [line.rstrip('\n\r') for line in f]
    except Exception as e:
        raise ValueError(f"Failed to read text file: {e}")


def write_text_file(lines: List[str], file_path: Union[str, Path]) -> None:
    """
    Write lines to text file.

    Args:
        lines: List of lines to write
        file_path: Output file path
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(file_path, 'w') as f:
            for line in lines:
                f.write(line + '\n')
    except Exception as e:
        raise ValueError(f"Failed to write text file: {e}")


def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get file size in bytes.

    Args:
        file_path: Path to file

    Returns:
        File size in bytes
    """
    file_path = Path(file_path)

    if not file_path.exists():
        return 0

    return file_path.stat().st_size


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted size string
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"