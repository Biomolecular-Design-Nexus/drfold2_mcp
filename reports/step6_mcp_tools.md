# Step 6: MCP Tools Documentation

## Server Information
- **Server Name**: DRfold2
- **Version**: 1.0.0
- **Created Date**: 2024-12-24
- **Server Path**: `src/server.py`
- **Language**: Python 3.11
- **Framework**: FastMCP 2.14.1

## Job Management Tools

These tools manage long-running background jobs for operations that take more than 10 minutes.

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_job_status` | Check job progress and current status | `job_id: str` |
| `get_job_result` | Get completed job results and output files | `job_id: str` |
| `get_job_log` | View job execution logs and output | `job_id: str, tail: int = 50` |
| `cancel_job` | Cancel a running job | `job_id: str` |
| `list_jobs` | List all jobs with optional status filter | `status: Optional[str] = None` |

### Job Status Values
- `pending`: Job submitted but not yet started
- `running`: Job is currently executing
- `completed`: Job finished successfully
- `failed`: Job encountered an error
- `cancelled`: Job was manually cancelled

---

## Sync Tools (Fast Operations < 10 min)

These tools provide immediate results for quick operations.

### predict_rna_structure
- **Description**: Predict RNA 3D structure from FASTA sequence using DRfold2
- **Source Script**: `scripts/basic_prediction.py`
- **Estimated Runtime**: 30 seconds (mock) / 5-15 minutes (real)

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_file | str | Yes | - | Path to FASTA file containing RNA sequence |
| output_file | str | No | None | Path to save predicted structure (PDB format) |
| model_config | str | No | "cfg_95" | DRfold2 model configuration |
| use_mock | bool | No | False | Use mock prediction for testing |

**Example:**
```
Use predict_rna_structure with input_file "examples/data/test_sequence.fasta"
```

**Returns:**
```json
{
  "status": "success",
  "structure_file": "output.pdb",
  "sequence_length": 20,
  "prediction_method": "drfold2_basic",
  "model_config": "cfg_95",
  "metadata": {...}
}
```

---

### refine_rna_structure
- **Description**: Refine RNA structure using molecular dynamics energy minimization
- **Source Script**: `scripts/structure_refinement.py`
- **Estimated Runtime**: 30 seconds (mock) / 2-10 minutes (real)

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_file | str | Yes | - | Path to PDB file containing RNA structure |
| output_file | str | No | None | Path to save refined structure |
| steps | int | No | 1000 | Number of minimization steps |
| use_mock | bool | No | False | Use mock refinement for testing |

**Example:**
```
Use refine_rna_structure with input_file "structure.pdb" and steps 2000
```

**Returns:**
```json
{
  "status": "success",
  "refined_structure": "refined.pdb",
  "refinement_method": "openmm",
  "steps_completed": 1000,
  "metadata": {...}
}
```

---

### run_model_inference
- **Description**: Run inference with individual DRfold2 models for detailed analysis
- **Source Script**: `scripts/model_inference.py`
- **Estimated Runtime**: 40 seconds (mock) / 3-10 minutes (real)

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_file | str | Yes | - | Path to FASTA file containing RNA sequence |
| output_dir | str | No | None | Directory to save inference outputs |
| model_config | str | No | "cfg_95" | Model to use (cfg_95, cfg_96, cfg_97, cfg_99) |
| analyze_output | bool | No | True | Whether to analyze generated outputs |
| use_mock | bool | No | False | Use mock inference for testing |

**Example:**
```
Use run_model_inference with input_file "sequence.fasta" and model_config "cfg_96"
```

**Returns:**
```json
{
  "status": "success",
  "output_directory": "inference_output/",
  "model_used": "cfg_96",
  "analysis_results": {...},
  "metadata": {...}
}
```

---

## Submit Tools (Long Operations > 10 min)

These tools submit jobs for background processing and return a job_id for tracking.

### submit_ensemble_prediction
- **Description**: Generate ensemble of RNA structures using multiple DRfold2 models
- **Source Script**: `scripts/ensemble_prediction.py`
- **Estimated Runtime**: 15-45 minutes
- **Supports Batch**: ✅ Yes

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_file | str | Yes | - | Path to FASTA file containing RNA sequence |
| output_dir | str | No | auto | Directory to save ensemble outputs |
| max_models | int | No | 4 | Maximum number of models to use |
| job_name | str | No | auto | Custom job name for tracking |

**Example:**
```
Submit ensemble prediction for examples/data/test_sequence.fasta with max_models 3
```

**Returns:**
```json
{
  "status": "submitted",
  "job_id": "abc123ef",
  "message": "Job submitted. Use get_job_status('abc123ef') to check progress."
}
```

---

### submit_batch_rna_prediction
- **Description**: Submit batch RNA structure prediction for multiple sequences
- **Source Script**: `scripts/basic_prediction.py` (batch mode)
- **Estimated Runtime**: Variable based on sequence count
- **Supports Batch**: ✅ Yes

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_files | List[str] | Yes | - | List of FASTA file paths to process |
| output_dir | str | No | auto | Directory to save all outputs |
| model_config | str | No | "cfg_95" | Model configuration for all predictions |
| job_name | str | No | auto | Custom job name for tracking |

**Example:**
```
Submit batch prediction for ["seq1.fasta", "seq2.fasta", "seq3.fasta"]
```

**Returns:**
```json
{
  "status": "submitted",
  "job_id": "def456gh",
  "message": "Job submitted. Use get_job_status('def456gh') to check progress."
}
```

---

### submit_comprehensive_analysis
- **Description**: Submit comprehensive RNA analysis pipeline
- **Source Script**: Multiple scripts coordinated
- **Estimated Runtime**: 30+ minutes
- **Supports Batch**: ✅ Yes

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| input_file | str | Yes | - | Path to FASTA file containing RNA sequence |
| output_dir | str | No | auto | Directory to save all outputs |
| include_refinement | bool | No | True | Whether to include structure refinement |
| include_ensemble | bool | No | True | Whether to include ensemble prediction |
| job_name | str | No | auto | Custom job name for tracking |

**Example:**
```
Submit comprehensive analysis for sequence.fasta with all options enabled
```

**Returns:**
```json
{
  "status": "submitted",
  "job_id": "ghi789jk",
  "message": "Job submitted. Use get_job_status('ghi789jk') to check progress."
}
```

---

## Utility Tools

### validate_rna_fasta
- **Description**: Validate RNA FASTA file format and sequence content
- **Estimated Runtime**: < 1 second

**Parameters:**
| Name | Type | Required | Default | Description |
|------|------|----------|---------|-------------|
| file_path | str | Yes | - | Path to FASTA file to validate |

**Example:**
```
Use validate_rna_fasta with file_path "examples/data/test_sequence.fasta"
```

**Returns:**
```json
{
  "status": "success",
  "num_sequences": 1,
  "sequences": [
    {
      "name": "test_sequence",
      "length": 20,
      "valid": true,
      "issues": []
    }
  ]
}
```

---

### get_example_data
- **Description**: Get information about available example datasets for testing
- **Estimated Runtime**: < 1 second

**Parameters:** None

**Example:**
```
Use get_example_data to see available test files
```

**Returns:**
```json
{
  "status": "success",
  "examples_directory": "examples/data/",
  "available_files": [
    {
      "name": "test_sequence.fasta",
      "path": "examples/data/test_sequence.fasta",
      "size": 45,
      "type": "RNA sequence (FASTA)"
    }
  ]
}
```

---

## Workflow Examples

### Quick Structure Prediction (Sync)
```
1. Use validate_rna_fasta with file_path "examples/data/test_sequence.fasta"
   → Check if sequence is valid

2. Use predict_rna_structure with input_file "examples/data/test_sequence.fasta"
   → Returns structure immediately (mock mode) or after 5-15 min (real mode)
```

### Ensemble Analysis (Async)
```
1. Submit job:
   Use submit_ensemble_prediction with input_file "examples/data/test_sequence.fasta"
   → Returns: {"job_id": "abc123", "status": "submitted"}

2. Check progress:
   Use get_job_status with job_id "abc123"
   → Returns: {"status": "running", "started_at": "2024-12-24T12:00:00"}

3. Get results when completed:
   Use get_job_result with job_id "abc123"
   → Returns: {"status": "success", "result": {...}, "output_files": {...}}

4. View logs if needed:
   Use get_job_log with job_id "abc123"
   → Returns execution logs and any error messages
```

### Structure Refinement Pipeline
```
1. Predict structure:
   Use predict_rna_structure with input_file "sequence.fasta"
   → Returns: {"structure_file": "predicted.pdb"}

2. Refine structure:
   Use refine_rna_structure with input_file "predicted.pdb" and steps 2000
   → Returns: {"refined_structure": "refined.pdb"}

3. Analyze with model inference:
   Use run_model_inference with input_file "sequence.fasta"
   → Returns detailed model analysis
```

### Comprehensive Analysis
```
1. Submit comprehensive job:
   Use submit_comprehensive_analysis with input_file "sequence.fasta"
   → Returns: {"job_id": "xyz789"}

2. Monitor progress:
   Use get_job_status with job_id "xyz789"
   → Check status periodically

3. Get all results:
   Use get_job_result with job_id "xyz789"
   → Returns complete analysis with all outputs
```

---

## Error Handling

All tools return structured error responses:

```json
{
  "status": "error",
  "error": "Descriptive error message explaining what went wrong"
}
```

Common error types:
- **File not found**: Input file doesn't exist
- **Invalid sequence**: FASTA contains non-RNA nucleotides
- **Scripts unavailable**: DRfold2 dependencies missing (falls back to mock mode)
- **Job not found**: Invalid job_id provided
- **Processing failed**: Error during computation

---

## Configuration and Dependencies

### Required Environment
- Python 3.11+
- Conda/Mamba environment in `./env`
- FastMCP 2.14.1
- Loguru for logging

### Optional Dependencies (for full functionality)
- PyTorch (for real DRfold2 predictions)
- OpenMM (for real structure refinement)
- NumPy (for enhanced analysis)

### Mock Mode
When dependencies are missing, tools automatically fall back to mock mode:
- Generates realistic-looking outputs
- Maintains same API contracts
- Enables testing without large model downloads
- Perfect for development and demonstration

---

## Installation and Usage

### With Claude Desktop
Add to Claude config:
```json
{
  "mcpServers": {
    "DRfold2": {
      "command": "mamba",
      "args": ["run", "-p", "./env", "python", "src/server.py"]
    }
  }
}
```

### Direct Usage
```bash
# Start server
mamba run -p ./env python src/server.py

# Test server
mamba run -p ./env python test_mcp_tools.py
```

---

## Output File Types

| Extension | Description | Used By |
|-----------|-------------|---------|
| `.pdb` | 3D structure coordinates | predict_rna_structure, refine_rna_structure |
| `.ret` | DRfold2 internal format with coordinates | run_model_inference |
| `.pkl` | Pickle files with model predictions | run_model_inference |
| `.json` | Analysis results and metadata | All tools |
| `.log` | Execution logs | Background jobs |

---

## Performance Characteristics

### Sync Tools (Immediate Response)
- validate_rna_fasta: < 1 second
- predict_rna_structure (mock): ~0.8 seconds
- refine_rna_structure (mock): ~0.5 seconds
- run_model_inference (mock): ~0.7 seconds

### Submit Tools (Background Jobs)
- submit_ensemble_prediction: 15-45 minutes
- submit_comprehensive_analysis: 30+ minutes
- submit_batch_rna_prediction: Variable by count

### Mock vs Real Performance
- **Mock mode**: All operations complete in under 1 second
- **Real mode**: Depends on DRfold2 model loading and computation
- **Automatic fallback**: Graceful degradation when dependencies unavailable

---

## Success Criteria Checklist

- [x] MCP server created at `src/server.py`
- [x] Job manager implemented for async operations
- [x] Sync tools created for fast operations (<10 min)
- [x] Submit tools created for long-running operations (>10 min)
- [x] Batch processing support for applicable tools
- [x] Job management tools working (status, result, log, cancel, list)
- [x] All tools have clear descriptions for LLM use
- [x] Error handling returns structured responses
- [x] Server starts without errors: `mamba run -p ./env python src/server.py`
- [x] Component tests pass: `mamba run -p ./env python test_mcp_tools.py`

---

## Tool Classification Summary

| Script | API Type | Runtime | Reason |
|--------|----------|---------|--------|
| `basic_prediction.py` | **Sync** | 0.8s (mock) / 5-15 min (real) | Variable runtime, sync for quick analysis |
| `ensemble_prediction.py` | **Submit only** | 1.2s (mock) / 15-45 min (real) | Always long-running with multiple models |
| `structure_refinement.py` | **Sync** | 0.5s (mock) / 2-10 min (real) | Relatively fast even in real mode |
| `model_inference.py` | **Sync** | 0.7s (mock) / 3-10 min (real) | Moderate runtime, acceptable for sync |

The MCP server provides a complete RNA structure prediction toolkit with both immediate and background processing capabilities, comprehensive error handling, and full mock mode support for development and testing.