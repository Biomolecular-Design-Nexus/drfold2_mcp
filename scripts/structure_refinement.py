#!/usr/bin/env python3
"""
Script: structure_refinement.py
Description: RNA structure refinement using molecular dynamics

Original Use Case: examples/use_case_3_structure_refinement.py
Dependencies Removed: Simplified OpenMM usage with better error handling

Usage:
    python scripts/structure_refinement.py --input <input_pdb> --output <output_pdb>

Example:
    python scripts/structure_refinement.py --input structure.pdb --output refined.pdb --steps 1000
"""

# ==============================================================================
# Minimal Imports (only essential packages)
# ==============================================================================
import argparse
import os
import sys
import tempfile
import json
from pathlib import Path
from typing import Union, Optional, Dict, Any

# ==============================================================================
# Configuration
# ==============================================================================
DEFAULT_CONFIG = {
    "steps": 1000,
    "temperature": 300,  # Kelvin
    "force_field": "amber14-all.xml",
    "water_model": "amber14/tip3pfb.xml",
    "padding": 1.0,  # nanometers
    "cutoff": 1.0,  # nanometers
    "use_mock": False,
    "cleanup_temp": True
}

# ==============================================================================
# OpenMM Detection and Import
# ==============================================================================
OPENMM_AVAILABLE = False
OPENMM_TYPE = None

try:
    # Try the new import path first
    import openmm.app as omm_app
    import openmm as omm
    import openmm.unit as omm_unit
    OPENMM_AVAILABLE = True
    OPENMM_TYPE = "openmm"
except ImportError:
    try:
        # Try the old import path
        import simtk.openmm.app as omm_app
        import simtk.openmm as omm
        import simtk.unit as omm_unit
        OPENMM_AVAILABLE = True
        OPENMM_TYPE = "simtk"
    except ImportError:
        OPENMM_AVAILABLE = False
        OPENMM_TYPE = None

# ==============================================================================
# Utility Functions
# ==============================================================================
def check_openmm() -> tuple[bool, Optional[str]]:
    """Check if OpenMM is available and return type."""
    return OPENMM_AVAILABLE, OPENMM_TYPE

def validate_pdb_file(file_path: Path) -> Dict[str, Any]:
    """Validate PDB file and extract basic information."""
    if not file_path.exists():
        raise FileNotFoundError(f"PDB file not found: {file_path}")

    info = {
        "atoms": 0,
        "residues": set(),
        "chains": set(),
        "has_rna": False,
        "issues": []
    }

    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith('ATOM'):
                    info["atoms"] += 1
                    parts = line.split()
                    if len(parts) >= 4:
                        residue = parts[3]
                        chain = line[21] if len(line) > 21 else 'A'
                        info["residues"].add(residue)
                        info["chains"].add(chain)

                        # Check for RNA residues
                        if residue in ['A', 'U', 'G', 'C', 'DA', 'DU', 'DG', 'DC']:
                            info["has_rna"] = True

    except Exception as e:
        raise ValueError(f"Failed to read PDB file: {e}")

    if info["atoms"] == 0:
        info["issues"].append("No ATOM records found")

    return info

def prepare_pdb_for_openmm(input_file: Path, output_file: Path) -> bool:
    """
    Prepare PDB file for OpenMM by fixing terminal residues.
    Simplified from DRfold2's woutpdb function.
    """
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()

        # Find residue numbers
        residue_nums = []
        for line in lines:
            if line.startswith('ATOM'):
                parts = line.split()
                if len(parts) >= 6:
                    residue_nums.append(int(parts[5]))

        if not residue_nums:
            return False

        residue_nums = sorted(set(residue_nums))
        first_res, last_res = residue_nums[0], residue_nums[-1]

        # Process lines
        output_lines = []
        for line in lines:
            if line.startswith('ATOM'):
                parts = line.split()
                if len(parts) >= 6:
                    atom_name = parts[2]
                    res_num = int(parts[5])

                    # Skip certain problematic atoms
                    if ("P" in atom_name and res_num == first_res) or ("H" in atom_name):
                        continue

                    # Modify terminal residue names for OpenMM
                    modified_line = line
                    if res_num == first_res and len(line) > 19:
                        modified_line = line[:17] + "5" + line[18:]
                    elif res_num == last_res and len(line) > 19:
                        modified_line = line[:17] + "3" + line[18:]

                    output_lines.append(modified_line)
            else:
                output_lines.append(line)

        with open(output_file, 'w') as f:
            f.writelines(output_lines)

        return True

    except Exception as e:
        print(f"Failed to prepare PDB: {e}")
        return False

def cleanup_pdb_after_openmm(input_file: Path, output_file: Path) -> bool:
    """
    Clean up PDB file after OpenMM refinement.
    Simplified from DRfold2's woutpdb2 function.
    """
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()

        # Remove hydrogen atoms and keep only heavy atoms
        output_lines = []
        for line in lines:
            if line.startswith('ATOM') and 'H' not in line.split()[2]:
                output_lines.append(line)

        with open(output_file, 'w') as f:
            f.writelines(output_lines)

        return True

    except Exception as e:
        print(f"Failed to cleanup PDB: {e}")
        return False

def generate_mock_refined_structure(input_file: Path, output_file: Path) -> bool:
    """Generate a mock refined structure by slightly modifying coordinates."""
    try:
        import random
        random.seed(42)  # For reproducible results

        with open(input_file, 'r') as f:
            lines = f.readlines()

        output_lines = []
        for line in lines:
            if line.startswith('ATOM'):
                # Add small random perturbations to simulate refinement
                try:
                    x = float(line[30:38]) + random.uniform(-0.1, 0.1)
                    y = float(line[38:46]) + random.uniform(-0.1, 0.1)
                    z = float(line[46:54]) + random.uniform(-0.1, 0.1)

                    # Reconstruct line with new coordinates
                    new_line = (
                        line[:30] +
                        f"{x:8.3f}" +
                        f"{y:8.3f}" +
                        f"{z:8.3f}" +
                        line[54:]
                    )
                    output_lines.append(new_line)
                except (ValueError, IndexError):
                    output_lines.append(line)
            else:
                output_lines.append(line)

        with open(output_file, 'w') as f:
            f.writelines(output_lines)

        return True

    except Exception as e:
        print(f"Failed to generate mock refinement: {e}")
        return False

# ==============================================================================
# Core Refinement Function
# ==============================================================================
def refine_structure_with_openmm(
    input_file: Path,
    output_file: Path,
    config: Dict[str, Any]
) -> bool:
    """Refine RNA structure using OpenMM molecular dynamics."""
    if not OPENMM_AVAILABLE:
        raise RuntimeError("OpenMM is not available")

    print(f"Refining structure with OpenMM ({OPENMM_TYPE})")
    print(f"Steps: {config['steps']}")

    # Create temporary files
    temp_dir = Path(tempfile.mkdtemp())
    temp_pdb1 = temp_dir / "prepared.pdb"
    temp_pdb2 = temp_dir / "refined_raw.pdb"

    try:
        # Step 1: Prepare PDB for OpenMM
        print("Step 1: Preparing PDB file for OpenMM...")
        if not prepare_pdb_for_openmm(input_file, temp_pdb1):
            raise RuntimeError("Failed to prepare PDB file")

        # Step 2: Load structure
        print("Step 2: Loading structure...")
        pdb = omm_app.PDBFile(str(temp_pdb1))
        modeller = omm_app.Modeller(pdb.topology, pdb.positions)

        # Step 3: Set up force field
        print("Step 3: Setting up force field...")
        try:
            forcefield = omm_app.ForceField(
                config["force_field"],
                config["water_model"]
            )
        except Exception as e:
            print(f"Warning: Force field setup failed ({e}), trying basic setup...")
            # Fallback to simpler force field
            forcefield = omm_app.ForceField('amber14-all.xml')

        # Step 4: Add hydrogens
        print("Step 4: Adding hydrogens...")
        try:
            modeller.addHydrogens(forcefield)
        except Exception as e:
            print(f"Warning: Could not add hydrogens ({e}), continuing...")

        # Step 5: Add solvent (optional)
        if config.get("add_solvent", False):
            print("Step 5: Adding explicit solvent...")
            try:
                modeller.addSolvent(
                    forcefield,
                    padding=config["padding"] * omm_unit.nanometer
                )
            except Exception as e:
                print(f"Warning: Could not add solvent ({e}), using implicit solvent...")

        # Step 6: Create system
        print("Step 6: Creating molecular system...")
        system = forcefield.createSystem(
            modeller.topology,
            nonbondedMethod=omm_app.NoCutoff,
            nonbondedCutoff=config["cutoff"] * omm_unit.nanometer,
            constraints=omm_app.HBonds
        )

        # Step 7: Set up integrator
        print("Step 7: Setting up molecular dynamics...")
        integrator = omm.LangevinIntegrator(
            config["temperature"] * omm_unit.kelvin,
            1 / omm_unit.picosecond,
            0.002 * omm_unit.picoseconds
        )

        # Step 8: Create simulation
        simulation = omm_app.Simulation(modeller.topology, system, integrator)
        simulation.context.setPositions(modeller.positions)

        # Step 9: Energy minimization
        print(f"Step 9: Running energy minimization ({config['steps']} steps)...")
        simulation.minimizeEnergy(maxIterations=config["steps"])

        # Step 10: Save structure
        print("Step 10: Saving refined structure...")
        positions = simulation.context.getState(getPositions=True).getPositions()
        omm_app.PDBFile.writeFile(
            simulation.topology, positions, open(str(temp_pdb2), 'w')
        )

        # Step 11: Clean up structure
        print("Step 11: Cleaning up final structure...")
        if not cleanup_pdb_after_openmm(temp_pdb2, output_file):
            # If cleanup fails, just copy the raw output
            import shutil
            shutil.copy2(temp_pdb2, output_file)

        return True

    except Exception as e:
        print(f"OpenMM refinement failed: {e}")
        return False

    finally:
        # Cleanup temporary files
        if config.get("cleanup_temp", True):
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass

# ==============================================================================
# Main Refinement Function
# ==============================================================================
def run_structure_refinement(
    input_file: Union[str, Path],
    output_file: Union[str, Path],
    config: Optional[Dict[str, Any]] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Main function for structure refinement.

    Args:
        input_file: Path to input PDB file
        output_file: Path to save refined structure
        config: Configuration dict (uses DEFAULT_CONFIG if not provided)
        **kwargs: Override specific config parameters

    Returns:
        Dict containing:
            - result: Refinement results
            - output_file: Path to refined structure
            - metadata: Execution metadata
            - success: Whether refinement succeeded

    Example:
        >>> result = run_structure_refinement("input.pdb", "refined.pdb")
        >>> print(result['success'])
    """
    # Setup
    input_file = Path(input_file)
    output_file = Path(output_file)
    config = {**DEFAULT_CONFIG, **(config or {}), **kwargs}

    # Validate input
    pdb_info = validate_pdb_file(input_file)

    # Create output directory
    output_file.parent.mkdir(parents=True, exist_ok=True)

    result_data = {
        "input_info": pdb_info,
        "config": config,
        "openmm_available": OPENMM_AVAILABLE,
        "openmm_type": OPENMM_TYPE,
        "refinement_method": None
    }

    success = False

    # Try OpenMM refinement if available and not using mock
    if not config.get("use_mock", False) and OPENMM_AVAILABLE:
        try:
            print("Attempting OpenMM structure refinement...")
            success = refine_structure_with_openmm(input_file, output_file, config)
            if success:
                result_data["refinement_method"] = "openmm"
                print("✓ OpenMM refinement completed successfully")
        except Exception as e:
            print(f"OpenMM refinement failed: {e}")
            success = False

    # Fall back to mock refinement
    if not success:
        if config.get("use_mock", False) or not OPENMM_AVAILABLE:
            print("Using mock refinement (coordinate perturbation)...")
            success = generate_mock_refined_structure(input_file, output_file)
            if success:
                result_data["refinement_method"] = "mock"
                print("✓ Mock refinement completed")

    # Validate output
    if success and output_file.exists():
        try:
            output_info = validate_pdb_file(output_file)
            result_data["output_info"] = output_info
        except Exception as e:
            print(f"Warning: Could not validate output file: {e}")

    return {
        "result": result_data,
        "output_file": str(output_file) if success else None,
        "metadata": {
            "input_file": str(input_file),
            "config": config,
            "openmm_available": OPENMM_AVAILABLE,
            "success": success
        },
        "success": success
    }

# ==============================================================================
# CLI Interface
# ==============================================================================
def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--input', '-i', required=True, help='Input PDB file')
    parser.add_argument('--output', '-o', required=True, help='Output refined PDB file')
    parser.add_argument('--config', '-c', help='Config file (JSON)')
    parser.add_argument('--steps', '-s', type=int, default=1000, help='Minimization steps')
    parser.add_argument('--use-mock', action='store_true', help='Use mock refinement')
    parser.add_argument('--temperature', type=float, default=300, help='Temperature (K)')

    args = parser.parse_args()

    # Check OpenMM availability
    openmm_available, openmm_type = check_openmm()
    if not openmm_available and not args.use_mock:
        print("Warning: OpenMM is not available.")
        print("Install OpenMM with: conda install -c conda-forge openmm")
        print("Or use --use-mock for testing without OpenMM")
        response = input("Continue with mock refinement? (y/N): ")
        if response.lower() != 'y':
            sys.exit(1)
        args.use_mock = True
    else:
        print(f"OpenMM status: {'Available' if openmm_available else 'Not available'}")
        if openmm_available:
            print(f"Import type: {openmm_type}")

    # Load config if provided
    config = {}
    if args.config:
        with open(args.config) as f:
            config = json.load(f)

    # Override config with CLI arguments
    config.update({
        "steps": args.steps,
        "temperature": args.temperature,
        "use_mock": args.use_mock
    })

    try:
        # Run refinement
        result = run_structure_refinement(
            input_file=args.input,
            output_file=args.output,
            config=config
        )

        if result["success"]:
            print(f"✅ Success: {result['output_file']}")
            print(f"Method: {result['result']['refinement_method']}")

            input_atoms = result['result']['input_info']['atoms']
            if 'output_info' in result['result']:
                output_atoms = result['result']['output_info']['atoms']
                print(f"Atoms: {input_atoms} → {output_atoms}")
            else:
                print(f"Input atoms: {input_atoms}")
        else:
            print(f"❌ Failed: Structure refinement failed")
            if not result['metadata']['openmm_available']:
                print("💡 Tip: Try --use-mock for testing without OpenMM")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()