# DRfold2 MCP Server Integration Test Report

## Test Information
- **Test Date**: 2025-12-24T12:56:06.383214
- **Server Path**: `/home/xux/Desktop/NucleicMCP/NucleicMCP/tool-mcps/drfold2_mcp/src/server.py`
- **Test Environment**: mock_mode
- **Python Version**: 3.12.12

## Test Results Summary

| Metric | Value |
|--------|-------|
| Total Tests | 7 |
| Passed | 1 |
| Failed | 0 |
| Errors | 6 |
| Pass Rate | 14.3% |
| Overall Status | **FAILED** |

## Detailed Test Results

### Server Startup
- **Status**: ✅ PASSED
- **Timestamp**: 2025-12-24T12:56:08.753541
- **Details**:
  - tool_count: 13
  - tools_found: ['get_job_status', 'get_job_result', 'get_job_log', 'cancel_job', 'list_jobs', 'predict_rna_structure', 'refine_rna_structure', 'run_model_inference', 'submit_ensemble_prediction', 'submit_batch_rna_prediction', 'submit_comprehensive_analysis', 'validate_rna_fasta', 'get_example_data']

### Sync Tool Basic
- **Status**: 💥 ERROR
- **Timestamp**: 2025-12-24T12:56:08.753600
- **Details**:
  - error: 'FunctionTool' object is not callable

### Sync Tool Prediction
- **Status**: 💥 ERROR
- **Timestamp**: 2025-12-24T12:56:08.753637
- **Details**:
  - error: 'FunctionTool' object is not callable

### Submit Workflow
- **Status**: 💥 ERROR
- **Timestamp**: 2025-12-24T12:56:08.753656
- **Details**:
  - error: 'FunctionTool' object is not callable

### Job Management
- **Status**: 💥 ERROR
- **Timestamp**: 2025-12-24T12:56:08.753663
- **Details**:
  - error: 'FunctionTool' object is not callable

### Error Handling
- **Status**: 💥 ERROR
- **Timestamp**: 2025-12-24T12:56:08.753669
- **Details**:
  - error: 'FunctionTool' object is not callable

### Example Data
- **Status**: 💥 ERROR
- **Timestamp**: 2025-12-24T12:56:08.753675
- **Details**:
  - error: 'FunctionTool' object is not callable

## Recommendations

⚠️ Some tests failed. Review the issues above and fix before deployment.

### Suggested Actions:
1. Review failed test details
2. Check server logs for additional errors
3. Validate environment setup
4. Re-run tests after fixes
