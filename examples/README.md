# DRfold2 Examples

This directory contains example scripts and data for using DRfold2 RNA structure prediction.

## Available Use Cases

### UC-1: Basic RNA Structure Prediction
**Script:** `use_case_1_basic_prediction.py`
**Description:** Performs basic RNA 3D structure prediction using a single model configuration (cfg_95).
**Usage:**
```bash
python examples/use_case_1_basic_prediction.py --input examples/data/test_sequence.fasta --output results/basic_prediction
```

**Features:**
- Single model inference for fast prediction
- End-to-end structure generation
- Geometric optimization with constraints
- Arena structure relaxation (if available)

### UC-2: Ensemble RNA Structure Prediction
**Script:** `use_case_2_ensemble_prediction.py`
**Description:** Uses multiple model configurations with clustering to generate diverse RNA conformations.
**Usage:**
```bash
python examples/use_case_2_ensemble_prediction.py --input examples/data/test_sequence.fasta --output results/ensemble_prediction --max-models 5
```

**Features:**
- Multi-model ensemble prediction (cfg_95, cfg_96, cfg_97, cfg_99)
- Clustering analysis for diverse conformations
- Multiple structure generation
- Quality assessment and ranking

### UC-3: Structure Refinement
**Script:** `use_case_3_structure_refinement.py`
**Description:** Refines existing RNA structures using OpenMM molecular dynamics with AMBER force fields.
**Usage:**
```bash
python examples/use_case_3_structure_refinement.py --input structure.pdb --output refined_structure.pdb --steps 1000
```

**Features:**
- OpenMM-based molecular dynamics refinement
- AMBER14 force field with explicit solvent
- Energy minimization
- Automatic step determination based on structure size

**Requirements:** OpenMM must be installed
```bash
conda install -c conda-forge openmm
```

### UC-4: Individual Model Inference
**Script:** `use_case_4_model_inference.py`
**Description:** Runs inference using specific model configurations for detailed analysis.
**Usage:**
```bash
python examples/use_case_4_model_inference.py --input examples/data/test_sequence.fasta --output results/model_inference --model cfg_95 --analyze
```

**Features:**
- Single model configuration testing
- Raw prediction data access
- Model behavior analysis
- Output file examination

## Example Data

### Input Sequences
- **`test_sequence.fasta`**: Test RNA sequence (30 nucleotides)
  ```
  >test
  UUGGGUUCCCUCACCCCAAUCAUAAAAAGG
  ```

### Configuration Files
- **`cfg_for_folding.json`**: Geometric optimization parameters with weights for:
  - FAPE (Frame Aligned Point Error) loss: weight 2
  - Bond constraints: weight 5000
  - Van der Waals interactions: weight 1
  - Pair contact weights and distance thresholds

- **`cfg_for_selection.json`**: Model selection criteria and parameters

## Common Workflows

### 1. Quick Structure Prediction
```bash
# Basic prediction for fast results
python examples/use_case_1_basic_prediction.py --input examples/data/test_sequence.fasta --output results/quick_test

# Check results
ls results/quick_test/relax/model_1.pdb
```

### 2. High-Quality Ensemble Prediction
```bash
# Generate multiple diverse structures
python examples/use_case_2_ensemble_prediction.py --input examples/data/test_sequence.fasta --output results/ensemble --max-models 3

# Refine the best model
python examples/use_case_3_structure_refinement.py --input results/ensemble/relax/model_1.pdb --output results/ensemble/model_1_refined.pdb
```

### 3. Model Analysis and Testing
```bash
# Test individual models
for model in cfg_95 cfg_96 cfg_97 cfg_99; do
    python examples/use_case_4_model_inference.py --input examples/data/test_sequence.fasta --output results/analysis_$model --model $model --analyze
done
```

## Output Structure

All scripts generate outputs in the following structure:
```
output_directory/
├── rets_dir/           # Raw model predictions (.ret files)
├── folds/              # Optimization intermediate files
└── relax/              # Final relaxed structures (.pdb files)
```

## Performance Notes

- **Basic prediction**: ~1-5 minutes per sequence
- **Ensemble prediction**: ~5-20 minutes depending on number of models
- **Structure refinement**: ~2-10 minutes depending on structure size and steps
- **Model inference**: ~1-3 minutes per model

## GPU Acceleration

All scripts support GPU acceleration if CUDA is available:
```bash
python examples/use_case_1_basic_prediction.py --device cuda --input examples/data/test_sequence.fasta
```

## Troubleshooting

### Model Files Missing
If you see "Model directory not found" errors:
```bash
cd repo/DRfold2
bash install.sh
```

### OpenMM Issues
For structure refinement, ensure OpenMM is properly installed:
```bash
conda install -c conda-forge openmm
```

### Arena Compilation
For structure relaxation:
```bash
cd repo/DRfold2/Arena
make Arena
```