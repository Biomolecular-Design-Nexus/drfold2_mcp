# Configuration Files

Configuration files for DRfold2 MCP scripts, extracted from original use cases and optimized for MCP tool integration.

## Configuration Hierarchy

1. **Default Configuration**: `default_config.json` - Global defaults for all scripts
2. **Script-Specific**: Individual config files for each script
3. **CLI Overrides**: Command-line arguments override config values
4. **Programmatic**: Function parameters override everything

## Configuration Files

### default_config.json
Global default values used by all scripts unless overridden.

**Key Sections:**
- `global`: Device, mock mode, timeout, verbosity
- `paths`: Repository and data paths
- `models`: Default model configurations
- `validation`: Input validation settings
- `output`: Output file handling
- `error_handling`: Fallback and retry behavior
- `performance`: Resource limits

### basic_prediction_config.json
Configuration for basic RNA structure prediction.

**Specific Settings:**
- Model configuration selection (cfg_95, cfg_96, etc.)
- Processing timeout and device selection
- Output formats and structure cleanup
- Mock options for testing without models

### ensemble_prediction_config.json
Configuration for ensemble prediction with multiple models.

**Specific Settings:**
- Multiple model configurations
- Clustering and diversity parameters
- Ensemble quality control
- Parallel execution settings

### structure_refinement_config.json
Configuration for molecular dynamics structure refinement.

**Specific Settings:**
- MD parameters (steps, temperature, pressure)
- Force field selection (AMBER14)
- Solvation and electrostatics
- OpenMM-specific options

### model_inference_config.json
Configuration for individual model inference and analysis.

**Specific Settings:**
- Model selection and device configuration
- Output analysis and data extraction
- Mock data generation parameters
- Data structure formatting

## Using Configuration Files

### In Scripts
```python
# Load default configuration
from scripts.lib import load_json

config = load_json("configs/default_config.json")

# Override with script-specific config
script_config = load_json("configs/basic_prediction_config.json")
config.update(script_config)

# Apply CLI overrides
config.update({
    "model.device": args.device,
    "processing.use_mock": args.use_mock
})
```

### Command Line
```bash
# Use default configuration
python scripts/basic_prediction.py --input input.fasta

# Use custom configuration file
python scripts/basic_prediction.py --input input.fasta --config my_config.json

# Override specific parameters
python scripts/basic_prediction.py --input input.fasta --device cuda --use-mock
```

### Programmatic Usage
```python
from scripts.basic_prediction import run_basic_prediction

# Custom configuration
config = {
    "model": {"config": "cfg_97", "device": "cuda"},
    "processing": {"timeout": 600, "use_mock": False},
    "output": {"formats": ["pdb", "ret"]}
}

result = run_basic_prediction(
    "input.fasta",
    "output.pdb",
    config=config
)
```

## Configuration Parameters

### Global Parameters (all scripts)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `device` | string | "cpu" | Computation device ("cpu" or "cuda") |
| `use_mock` | boolean | false | Use mock mode for testing |
| `timeout` | integer | 300 | Operation timeout in seconds |
| `verbose` | boolean | false | Enable verbose output |

### Model Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `default_config` | string | "cfg_95" | Default model configuration |
| `available_configs` | array | ["cfg_95", "cfg_96", "cfg_97", "cfg_99"] | Available model options |
| `fallback_to_mock` | boolean | true | Auto-fallback to mock if models missing |
| `check_availability` | boolean | true | Validate model availability |

### Processing Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_memory_gb` | integer | 8 | Maximum memory usage |
| `max_cpu_cores` | integer | 4 | Maximum CPU cores to use |
| `parallel_processing` | boolean | false | Enable parallel execution |
| `cache_results` | boolean | false | Cache intermediate results |

### Output Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `create_directories` | boolean | true | Auto-create output directories |
| `overwrite_existing` | boolean | false | Overwrite existing files |
| `cleanup_on_failure` | boolean | false | Clean up files on error |
| `save_metadata` | boolean | true | Save execution metadata |

## Custom Configuration

### Creating Custom Configs

1. **Copy base configuration**:
   ```bash
   cp configs/default_config.json configs/my_config.json
   ```

2. **Modify values**:
   ```json
   {
     "global": {
       "device": "cuda",
       "use_mock": false,
       "timeout": 600
     },
     "models": {
       "default_config": "cfg_97"
     }
   }
   ```

3. **Use in script**:
   ```bash
   python scripts/basic_prediction.py --config configs/my_config.json
   ```

### Environment-Specific Configs

Create configs for different environments:

**development.json** (testing with mock):
```json
{
  "global": {
    "use_mock": true,
    "timeout": 60,
    "verbose": true
  },
  "error_handling": {
    "fail_on_missing_models": false
  }
}
```

**production.json** (real models):
```json
{
  "global": {
    "use_mock": false,
    "timeout": 1800,
    "verbose": false
  },
  "performance": {
    "max_memory_gb": 16,
    "parallel_processing": true
  }
}
```

**gpu.json** (CUDA acceleration):
```json
{
  "global": {
    "device": "cuda",
    "use_mock": false
  },
  "performance": {
    "max_memory_gb": 24
  }
}
```

## Validation

### Config Validation
Scripts automatically validate configuration parameters:

```python
# Example validation in script
def validate_config(config):
    errors = []

    # Check device
    if config.get('device') not in ['cpu', 'cuda']:
        errors.append("Device must be 'cpu' or 'cuda'")

    # Check timeout
    if config.get('timeout', 0) <= 0:
        errors.append("Timeout must be positive")

    # Check model config
    available = config.get('available_configs', [])
    selected = config.get('default_config')
    if selected not in available:
        errors.append(f"Model {selected} not in available list")

    if errors:
        raise ValueError("Configuration errors: " + "; ".join(errors))
```

### Parameter Types and Ranges

| Parameter Type | Validation | Example |
|----------------|------------|---------|
| Device | Must be "cpu" or "cuda" | "cuda" |
| Timeout | Positive integer, max 7200 | 600 |
| Memory | Positive integer, max 128 | 16 |
| Boolean | Must be true/false | true |
| Path | Must be valid path string | "repo/DRfold2" |
| Model Config | Must be in available list | "cfg_95" |

## Troubleshooting

### Common Configuration Issues

1. **Invalid JSON syntax**:
   ```
   Error: JSON decode error at line 15
   Solution: Check for missing commas, quotes, brackets
   ```

2. **Unknown parameters**:
   ```
   Warning: Unknown parameter 'invalid_param' ignored
   Solution: Check parameter name spelling
   ```

3. **Type mismatches**:
   ```
   Error: 'timeout' must be integer, got string
   Solution: Remove quotes around numeric values
   ```

4. **Path issues**:
   ```
   Error: Config path 'nonexistent.json' not found
   Solution: Check file path and permissions
   ```

### Debugging Configuration

Enable verbose mode to see configuration loading:
```bash
python scripts/basic_prediction.py --verbose --input input.fasta
```

Output includes:
```
Loading default config: configs/default_config.json
Loading script config: configs/basic_prediction_config.json
Applying CLI overrides: {'device': 'cuda'}
Final configuration: {...}
```

### Configuration Schema

For IDE support and validation, here's the JSON schema structure:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "global": {
      "type": "object",
      "properties": {
        "device": {"type": "string", "enum": ["cpu", "cuda"]},
        "use_mock": {"type": "boolean"},
        "timeout": {"type": "integer", "minimum": 1, "maximum": 7200}
      }
    },
    "models": {
      "type": "object",
      "properties": {
        "default_config": {"type": "string"},
        "available_configs": {
          "type": "array",
          "items": {"type": "string"}
        }
      }
    }
  }
}
```

This schema can be used with JSON editors for auto-completion and validation.