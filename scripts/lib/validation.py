"""
Validation functions for molecular data.

These functions validate input data and file formats for DRfold2 MCP scripts.
"""
from pathlib import Path
from typing import Union, Dict, Any, Set, List


def validate_rna_sequence(sequence: str, allow_ambiguous: bool = False) -> bool:
    """
    Validate RNA sequence contains only valid nucleotides.

    Args:
        sequence: RNA sequence to validate
        allow_ambiguous: Whether to allow ambiguous nucleotide codes

    Returns:
        True if sequence is valid
    """
    if not sequence:
        return False

    # Standard RNA nucleotides
    valid_nucleotides = {'A', 'U', 'G', 'C'}

    if allow_ambiguous:
        # Add ambiguous nucleotide codes
        valid_nucleotides.update({
            'R', 'Y', 'S', 'W', 'K', 'M',  # Two-fold ambiguity
            'B', 'D', 'H', 'V',            # Three-fold ambiguity
            'N'                             # Four-fold ambiguity
        })

    # Check each character
    sequence = sequence.upper().strip()
    for char in sequence:
        if char not in valid_nucleotides:
            return False

    return True


def validate_pdb_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate PDB file and extract basic information.

    Args:
        file_path: Path to PDB file

    Returns:
        Dictionary with validation results and file information
    """
    file_path = Path(file_path)

    result = {
        "valid": False,
        "exists": file_path.exists(),
        "atom_count": 0,
        "residue_count": 0,
        "chain_count": 0,
        "has_rna": False,
        "has_protein": False,
        "residue_types": set(),
        "chain_ids": set(),
        "issues": []
    }

    if not result["exists"]:
        result["issues"].append("File does not exist")
        return result

    try:
        with open(file_path, 'r') as f:
            residue_numbers = set()
            current_chain = None

            for line_num, line in enumerate(f, 1):
                if line.startswith('ATOM') or line.startswith('HETATM'):
                    result["atom_count"] += 1

                    # Parse PDB line
                    if len(line) >= 54:
                        try:
                            residue_name = line[17:20].strip()
                            chain_id = line[21].strip()
                            residue_num = line[22:26].strip()

                            result["residue_types"].add(residue_name)
                            result["chain_ids"].add(chain_id)
                            residue_numbers.add((chain_id, residue_num))

                            # Check for RNA residues
                            if residue_name in {'A', 'U', 'G', 'C', 'DA', 'DU', 'DG', 'DC'}:
                                result["has_rna"] = True

                            # Check for protein residues
                            protein_residues = {
                                'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLU', 'GLN', 'GLY',
                                'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE', 'PRO', 'SER',
                                'THR', 'TRP', 'TYR', 'VAL'
                            }
                            if residue_name in protein_residues:
                                result["has_protein"] = True

                        except (ValueError, IndexError):
                            result["issues"].append(f"Invalid PDB format at line {line_num}")

            result["residue_count"] = len(residue_numbers)
            result["chain_count"] = len(result["chain_ids"])

    except Exception as e:
        result["issues"].append(f"Error reading file: {e}")
        return result

    # Validate results
    if result["atom_count"] == 0:
        result["issues"].append("No ATOM records found")
    elif result["atom_count"] < 10:
        result["issues"].append("Very few atoms found (< 10)")

    if result["residue_count"] == 0:
        result["issues"].append("No residues found")

    if not result["has_rna"] and not result["has_protein"]:
        result["issues"].append("No recognized RNA or protein residues found")

    # File is valid if no critical issues
    result["valid"] = len(result["issues"]) == 0

    # Convert sets to lists for JSON serialization
    result["residue_types"] = sorted(list(result["residue_types"]))
    result["chain_ids"] = sorted(list(result["chain_ids"]))

    return result


def check_file_format(file_path: Union[str, Path], expected_format: str) -> Dict[str, Any]:
    """
    Check if file matches expected format.

    Args:
        file_path: Path to file
        expected_format: Expected format ('fasta', 'pdb', 'json', etc.)

    Returns:
        Dictionary with validation results
    """
    file_path = Path(file_path)

    result = {
        "valid": False,
        "format": expected_format,
        "detected_format": None,
        "issues": []
    }

    if not file_path.exists():
        result["issues"].append("File does not exist")
        return result

    # Check by extension first
    extension_map = {
        '.fasta': 'fasta',
        '.fa': 'fasta',
        '.fas': 'fasta',
        '.pdb': 'pdb',
        '.ent': 'pdb',
        '.json': 'json',
        '.pkl': 'pickle',
        '.ret': 'drfold2_ret'
    }

    file_ext = file_path.suffix.lower()
    format_from_ext = extension_map.get(file_ext, 'unknown')

    # Check content
    try:
        with open(file_path, 'r') as f:
            first_lines = [f.readline().strip() for _ in range(3)]

        # Detect format from content
        if any(line.startswith('>') for line in first_lines):
            result["detected_format"] = 'fasta'
        elif any(line.startswith(('ATOM', 'HETATM', 'HEADER')) for line in first_lines):
            result["detected_format"] = 'pdb'
        elif first_lines[0].startswith('{'):
            result["detected_format"] = 'json'
        else:
            result["detected_format"] = format_from_ext

    except UnicodeDecodeError:
        # Likely binary file
        if file_ext in ['.pkl', '.ret']:
            result["detected_format"] = extension_map[file_ext]
        else:
            result["detected_format"] = 'binary'

    except Exception as e:
        result["issues"].append(f"Error reading file: {e}")
        return result

    # Validate format match
    if result["detected_format"] == expected_format:
        result["valid"] = True
    elif format_from_ext == expected_format:
        result["valid"] = True
        result["issues"].append("Format detected by extension, not content")
    else:
        result["issues"].append(
            f"Expected {expected_format}, detected {result['detected_format']}"
        )

    return result


def validate_sequence_length(sequence: str, min_length: int = 1, max_length: int = 10000) -> bool:
    """
    Validate sequence length is within acceptable range.

    Args:
        sequence: Sequence to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length

    Returns:
        True if length is valid
    """
    length = len(sequence.strip())
    return min_length <= length <= max_length


def check_nucleotide_composition(sequence: str) -> Dict[str, Any]:
    """
    Analyze nucleotide composition of RNA sequence.

    Args:
        sequence: RNA sequence

    Returns:
        Dictionary with composition statistics
    """
    sequence = sequence.upper().strip()
    total = len(sequence)

    if total == 0:
        return {
            "total_length": 0,
            "composition": {},
            "gc_content": 0.0,
            "valid": False
        }

    # Count nucleotides
    counts = {'A': 0, 'U': 0, 'G': 0, 'C': 0, 'other': 0}

    for nucleotide in sequence:
        if nucleotide in counts:
            counts[nucleotide] += 1
        else:
            counts['other'] += 1

    # Calculate percentages
    composition = {nt: (count / total) * 100 for nt, count in counts.items()}

    # Calculate GC content
    gc_content = (counts['G'] + counts['C']) / total * 100

    return {
        "total_length": total,
        "counts": counts,
        "composition": composition,
        "gc_content": gc_content,
        "valid": counts['other'] == 0
    }