#!/usr/bin/env python3
"""
DRfold2 Structure Refinement with OpenMM

This script performs molecular dynamics refinement of RNA structures using OpenMM
with AMBER force fields and explicit solvent.

Usage:
    python examples/use_case_3_structure_refinement.py [--input INPUT_PDB] [--output OUTPUT_PDB] [--steps STEPS]

Example:
    python examples/use_case_3_structure_refinement.py --input results/basic_prediction/relax/model_1.pdb --output results/refined_structure.pdb --steps 1000
"""

import os
import sys
import argparse
from pathlib import Path

# Add DRfold2 to path
repo_path = Path(__file__).parent.parent / "repo" / "DRfold2"
sys.path.insert(0, str(repo_path))

# Try to import OpenMM modules at top level
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

def check_openmm():
    """Check if OpenMM is available"""
    return OPENMM_AVAILABLE, OPENMM_TYPE

def woutpdb(infile, outfile):
    """
    Prepare PDB for OpenMM by setting terminal residues correctly
    (From DRfold2's refine.py)
    """
    lines = open(infile).readlines()
    nums = []
    for aline in lines:
        if aline.startswith('ATOM'):
            num = aline.split()[5]
            nums.append(num)
    nums.sort()

    olines = []
    for aline in lines:
        if aline.startswith('ATOM'):
            atom = aline.split()[2]
            num = int(aline.split()[5])

            theline = list(aline)
            if num == nums[0]:
                theline[18:20] = theline[19:20] + ['5']
            elif num == nums[-1]:
                theline[18:20] = theline[19:20] + ['3']

            # Remove phosphorus from first residue and hydrogen atoms
            if not (("P" in atom and num == 1) or ("H" in atom)):
                olines.append(''.join(theline))

    with open(outfile, 'w') as wfile:
        wfile.write(''.join(olines))

def woutpdb2(infile, outfile):
    """
    Clean up PDB file after OpenMM refinement
    (From DRfold2's refine.py)
    """
    lines = open(infile).readlines()
    olines = []
    for aline in lines:
        if aline.startswith('ATOM') and 'H' not in aline:
            olines.append(aline)

    with open(outfile, 'w') as wfile:
        wfile.write(''.join(olines))

def refine_structure(input_pdb, output_pdb, steps=1000, openmm_type="simtk"):
    """
    Refine RNA structure using OpenMM molecular dynamics

    Args:
        input_pdb: Input PDB structure
        output_pdb: Output refined PDB structure
        steps: Number of minimization steps
        openmm_type: Type of OpenMM import ("simtk" or "openmm")
    """
    print(f"Refining structure: {input_pdb} -> {output_pdb}")
    print(f"Minimization steps: {steps}")

    # Use already imported OpenMM modules
    if not OPENMM_AVAILABLE:
        raise RuntimeError("OpenMM is not available")

    # Prepare temporary files
    temp_pdb1 = output_pdb + '_amber_tmp.pdb'
    temp_pdb2 = output_pdb + '_amber_tmp2.pdb'

    try:
        # Step 1: Prepare PDB for OpenMM
        print("Step 1: Preparing PDB file for OpenMM...")
        woutpdb(input_pdb, temp_pdb1)

        # Step 2: Load structure and create system
        print("Step 2: Loading structure and setting up force field...")
        pdb = omm_app.PDBFile(temp_pdb1)
        modeller = omm_app.Modeller(pdb.topology, pdb.positions)

        # Use AMBER force field
        forcefield = omm_app.ForceField('amber14-all.xml', 'amber14/tip3pfb.xml')

        # Add hydrogens and solvent
        print("Step 3: Adding hydrogens and explicit solvent...")
        modeller.addHydrogens(forcefield)
        modeller.addSolvent(forcefield, padding=1 * omm_unit.nanometer)

        # Create system
        print("Step 4: Creating molecular system...")
        system = forcefield.createSystem(
            modeller.topology,
            nonbondedMethod=omm_app.NoCutoff,
            nonbondedCutoff=1 * omm_unit.nanometer,
            constraints=omm_app.HBonds
        )

        # Optional: Add positional restraints on phosphorus atoms
        # (Currently disabled as in original DRfold2)
        if False:
            restraint = omm.CustomExternalForce('k*((x-x0)^2+(y-y0)^2+(z-z0)^2)')
            system.addForce(restraint)
            restraint.addGlobalParameter('k', 100.0*omm_unit.kilojoules_per_mole/omm_unit.nanometer)
            restraint.addPerParticleParameter('x0')
            restraint.addPerParticleParameter('y0')
            restraint.addPerParticleParameter('z0')
            for atom in pdb.topology.atoms():
                if atom.name == 'P':
                    restraint.addParticle(atom.index, pdb.positions[atom.index])

        # Setup integrator and simulation
        print("Step 5: Setting up molecular dynamics simulation...")
        integrator = omm.LangevinIntegrator(300 * omm_unit.kelvin, 1 / omm_unit.picosecond, 0.002 * omm_unit.picoseconds)
        simulation = omm_app.Simulation(modeller.topology, system, integrator)
        simulation.context.setPositions(modeller.positions)

        # Add reporter for progress monitoring
        simulation.reporters.append(omm_app.StateDataReporter(
            sys.stdout, 1000,
            step=True,
            potentialEnergy=True,
            temperature=True
        ))

        # Step 6: Energy minimization
        print(f"Step 6: Running energy minimization for {steps} steps...")
        simulation.minimizeEnergy(maxIterations=steps)

        # Step 7: Save minimized structure
        print("Step 7: Saving minimized structure...")
        position = simulation.context.getState(getPositions=True).getPositions()
        omm_app.PDBFile.writeFile(simulation.topology, position, open(temp_pdb2, 'w'))

        # Step 8: Clean up PDB file
        print("Step 8: Cleaning up final structure...")
        woutpdb2(temp_pdb2, output_pdb)

        print(f"✓ Structure refinement completed: {output_pdb}")
        return True

    except Exception as e:
        print(f"Error during refinement: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Clean up temporary files
        for temp_file in [temp_pdb1, temp_pdb2]:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except:
                pass

def main():
    parser = argparse.ArgumentParser(description='DRfold2 Structure Refinement with OpenMM')
    parser.add_argument('--input', '-i', required=True,
                       help='Input PDB file to refine')
    parser.add_argument('--output', '-o', required=True,
                       help='Output refined PDB file')
    parser.add_argument('--steps', '-s', type=int, default=1000,
                       help='Number of minimization steps (default: 1000)')
    parser.add_argument('--auto-steps', action='store_true',
                       help='Automatically determine steps based on structure size')

    args = parser.parse_args()

    # Check input file
    if not os.path.isfile(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Check OpenMM availability
    openmm_available, openmm_type = check_openmm()
    if not openmm_available:
        print("Error: OpenMM is not installed.")
        print("Please install OpenMM:")
        print("  conda install -c conda-forge openmm")
        print("or")
        print("  pip install openmm")
        sys.exit(1)

    print(f"Using OpenMM import type: {openmm_type}")

    # Auto-determine steps based on structure size
    if args.auto_steps:
        try:
            with open(args.input, 'r') as f:
                atom_count = sum(1 for line in f if line.startswith('ATOM'))
            args.steps = max(10, min(1000, int(atom_count / 20.0)))
            print(f"Auto-determined steps: {args.steps} (based on {atom_count} atoms)")
        except:
            print("Warning: Could not auto-determine steps, using default")

    print("DRfold2 Structure Refinement with OpenMM")
    print("=" * 42)
    print(f"Input PDB: {args.input}")
    print(f"Output PDB: {args.output}")
    print(f"Minimization steps: {args.steps}")
    print()

    # Create output directory if needed
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    success = refine_structure(args.input, args.output, args.steps, openmm_type)

    if success:
        print("\n✓ Structure refinement completed successfully!")

        # Print some basic statistics
        try:
            with open(args.input, 'r') as f:
                input_atoms = sum(1 for line in f if line.startswith('ATOM'))
            with open(args.output, 'r') as f:
                output_atoms = sum(1 for line in f if line.startswith('ATOM'))

            print(f"Input atoms: {input_atoms}")
            print(f"Output atoms: {output_atoms}")

        except:
            pass

    else:
        print("\n✗ Structure refinement failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()