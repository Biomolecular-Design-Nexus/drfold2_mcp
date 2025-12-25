# MCP Scripts

Clean, self-contained scripts extracted from DRfold2 use cases for MCP tool wrapping.

## Design Principles

1. **Minimal Dependencies**: Only essential packages imported
2. **Self-Contained**: Functions inlined where possible
3. **Configurable**: Parameters in config files, not hardcoded
4. **MCP-Ready**: Each script has a main function ready for MCP wrapping
5. **Mock-Capable**: All scripts can run in mock mode for testing without models

## Scripts

| Script | Description | Repo Dependent | Config | Mock Support |
|--------|-------------|----------------|--------|--------------|
| `basic_prediction.py` | Basic RNA structure prediction | Yes (models) | `configs/basic_prediction_config.json` | ✅ Yes |
| `ensemble_prediction.py` | Multi-model ensemble prediction | Yes (models) | `configs/ensemble_prediction_config.json` | ✅ Yes |
| `structure_refinement.py` | MD structure refinement | No (uses OpenMM) | `configs/structure_refinement_config.json` | ✅ Yes |
| `model_inference.py` | Individual model inference | Yes (models) | `configs/model_inference_config.json` | ✅ Yes |

## Usage

### Prerequisites

```bash
# Activate environment
mamba activate ./env  # or: conda activate ./env

# Optional: Install OpenMM for structure refinement
conda install -c conda-forge openmm
```

### Basic Usage

```bash
# Basic prediction with mock mode (no models required)
python scripts/basic_prediction.py \
    --input examples/data/test_sequence.fasta \
    --output results/basic.pdb \
    --use-mock

# Ensemble prediction
python scripts/ensemble_prediction.py \
    --input examples/data/test_sequence.fasta \
    --output results/ensemble \
    --use-mock \
    --max-models 3

# Structure refinement (mock mode if OpenMM not available)
python scripts/structure_refinement.py \
    --input results/basic.pdb \
    --output results/refined.pdb \
    --use-mock \
    --steps 100

# Model inference
python scripts/model_inference.py \
    --input examples/data/test_sequence.fasta \
    --output results/inference \
    --use-mock \
    --analyze
```

### With Configuration Files

```bash
# Use custom configuration
python scripts/basic_prediction.py \
    --input examples/data/test_sequence.fasta \
    --output results/basic.pdb \
    --config configs/basic_prediction_config.json

# Override specific parameters
python scripts/ensemble_prediction.py \
    --input examples/data/test_sequence.fasta \
    --output results/ensemble \
    --max-models 5 \
    --device cuda
```

### Real DRfold2 Models (if available)

```bash
# Install DRfold2 models first
bash repo/DRfold2/install.sh

# Run without mock mode
python scripts/basic_prediction.py \
    --input examples/data/test_sequence.fasta \
    --output results/real_prediction.pdb \
    --model cfg_95
```

## Shared Library

Common functions are in `scripts/lib/`:
- `io.py`: File loading/saving (FASTA, JSON, PDB validation)
- `validation.py`: RNA sequence and PDB validation
- `utils.py`: General utilities (directories, timing, file info)
- `drfold2.py`: DRfold2-specific utilities (model detection, availability)

### Using the Library

```python
from scripts.lib import load_fasta, validate_rna_sequence, check_drfold2_availability

# Load sequences
sequences = load_fasta("input.fasta")

# Validate RNA
for header, sequence in sequences.items():
    if validate_rna_sequence(sequence):
        print(f"{header}: Valid RNA sequence")

# Check DRfold2 availability
status = check_drfold2_availability()
print(f"Available models: {status['available_models']}")
```

## For MCP Wrapping (Step 6)

Each script exports a main function that can be wrapped:

```python
# For MCP tool integration
from scripts.basic_prediction import run_basic_prediction
from scripts.ensemble_prediction import run_ensemble_prediction
from scripts.structure_refinement import run_structure_refinement
from scripts.model_inference import run_model_inference

# Example MCP tool wrapper
@mcp.tool()
def predict_rna_structure(
    input_file: str,
    output_file: str = None,
    use_mock: bool = False
):
    \"\"\"Predict RNA 3D structure from FASTA sequence.\"\"\"
    return run_basic_prediction(
        input_file, output_file,
        config={"use_mock": use_mock}
    )
```

## Configuration

### Default Configuration

All scripts use values from `configs/default_config.json` unless overridden.

Key settings:
- `device`: "cpu" or "cuda"
- `use_mock`: false (set to true for testing without models)
- `timeout`: 300 seconds
- `fallback_to_mock`: true (automatically use mock if models unavailable)

### Script-Specific Configs

Each script has its own configuration file in `configs/`:
- `basic_prediction_config.json`
- `ensemble_prediction_config.json`
- `structure_refinement_config.json`
- `model_inference_config.json`

## Mock Mode

All scripts support mock mode for testing and development:

**Mock Features:**
- Generate synthetic PDB structures with realistic atom layouts
- Create mock inference data with proper tensor shapes
- Simulate ensemble diversity with coordinate variations
- Perturb coordinates for refinement simulation
- Generate realistic file sizes and formats

**When Mock Mode is Used:**
- Explicitly requested with `--use-mock`
- DRfold2 models are missing and `fallback_to_mock` is true
- OpenMM is not available (for structure refinement)

## Error Handling

Scripts handle common error conditions gracefully:

1. **Missing Models**: Clear error message with suggestion to use mock mode
2. **Invalid Input**: Validation with helpful error descriptions
3. **Missing Dependencies**: Informative messages about installation
4. **Timeout**: Configurable timeouts with graceful failure

## Dependencies

### Essential (Always Required)
- Python 3.8+
- Standard library: `os`, `sys`, `argparse`, `pathlib`, `json`

### Optional (with fallbacks)
- `torch`: Required for real DRfold2 inference
- `numpy`: Used for mock data generation and analysis
- `openmm`: Required for real structure refinement

### Repository Dependencies
- DRfold2 repository: Required for real model inference
- Model weights: ~1.3GB download required for non-mock operation

## Testing

All scripts have been tested with:
- ✅ Mock mode execution
- ✅ Configuration file loading
- ✅ CLI argument parsing
- ✅ Error handling for missing dependencies
- ✅ Output file generation
- ✅ Shared library integration

```bash
# Test all scripts in mock mode
python scripts/basic_prediction.py --input examples/data/test_sequence.fasta --output results/test1.pdb --use-mock
python scripts/ensemble_prediction.py --input examples/data/test_sequence.fasta --output results/test2 --use-mock
python scripts/structure_refinement.py --input results/test1.pdb --output results/test3.pdb --use-mock
python scripts/model_inference.py --input examples/data/test_sequence.fasta --output results/test4 --use-mock
```

## Troubleshooting

### Common Issues

1. **Import Error**: Make sure you're in the correct directory and the `scripts/lib` module is available
2. **Missing Input File**: Check that `examples/data/test_sequence.fasta` exists
3. **Permission Errors**: Ensure write permissions to the output directory
4. **Memory Issues**: Use mock mode for testing on limited systems

### Debug Mode

Add `--verbose` flag (if implemented) or check output for detailed execution information.

### Getting Help

Each script provides detailed help:
```bash
python scripts/basic_prediction.py --help
```

## Performance

### Mock Mode Performance
- Basic prediction: ~1 second
- Ensemble (3 models): ~2 seconds
- Structure refinement: ~1 second
- Model inference: ~1 second

### Memory Usage
- Mock mode: <100 MB
- Real mode: Depends on model size (1-4 GB)