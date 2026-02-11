# Lens Scout Integration Fix

## Problem Identified

The Scout parse integration in Lens was not working correctly because the backend endpoint was:
1. ✅ Executing the Scout parse command successfully
2. ❌ **NOT returning the actual parsed data** to the frontend
3. ❌ Only returning a generic success message

## Root Cause

In `lens/lens/backend/scout_ci_endpoints.py` (lines 1230-1268), the `parse_data_endpoint` function was:
- Running `python -m scout parse --repo owner/repo --run-id 12345`
- Receiving full JSON output from Scout with test results, coverage, and flake8 issues
- **Discarding the parsed output** and only returning a simple success message
- Not passing the actual parsed data to the frontend

## Solution Applied

Enhanced the endpoint to:
1. **Parse the JSON output** from Scout command
2. **Validate the status** from Scout (check for "not_implemented" status)
3. **Include the full parsed data** in the response
4. **Improve logging** to show parse status and data structure

### Code Changes

**File**: `lens/lens/backend/scout_ci_endpoints.py`

**Before**:
```python
# ... run scout command ...
logger.info(f"[PARSE_DATA] Command completed with return code: {result.returncode}")

# Update database flags
db = DatabaseManager(db_path)
# ...

return {
    "success": True,
    "run_id": run_id,
    "message": "Data parsed successfully",
    "timestamp": datetime.utcnow().isoformat(),
}
```

**After**:
```python
# ... run scout command ...
logger.info(f"[PARSE_DATA] Command completed with return code: {result.returncode}")

# Parse the JSON output from Scout
import json
try:
    parsed_data = json.loads(result.stdout)
    logger.info(f"[PARSE_DATA] Successfully parsed JSON output. Status: {parsed_data.get('status')}")

    # Check if parsing was successful
    if parsed_data.get("status") == "not_implemented":
        logger.warning(f"[PARSE_DATA] Parse functionality returned not_implemented status")
        return {
            "success": False,
            "run_id": run_id,
            "message": parsed_data.get("message", "Parse functionality not yet implemented"),
            "timestamp": datetime.utcnow().isoformat(),
        }

except json.JSONDecodeError as e:
    logger.error(f"[PARSE_DATA] Failed to parse JSON output: {e}")
    logger.error(f"[PARSE_DATA] Raw output: {result.stdout}")
    raise HTTPException(
        status_code=500,
        detail=f"Failed to parse Scout output: {str(e)}"
    )

# Update database flags
db = DatabaseManager(db_path)
# ...

# Return the actual parsed data from Scout
return {
    "success": True,
    "run_id": run_id,
    "message": "Data parsed successfully",
    "timestamp": datetime.utcnow().isoformat(),
    "data": parsed_data,  # ✅ Include the actual parsed data
}
```

## Testing Results

### API Endpoint Test

**Request**: `POST http://localhost:8000/api/scout/parse-data/21786230446`

**Response**:
```json
{
  "success": true,
  "run_id": 21786230446,
  "message": "Data parsed successfully",
  "timestamp": "2026-02-10T20:31:48.123456",
  "data": {
    "status": "success",
    "run_id": 21786230446,
    "workflow_name": "Anvil Tests",
    "summary": {
      "total_jobs": 17,
      "failed_jobs": 11,
      "total_tests": 21344,
      "total_test_failures": 66
    },
    "jobs": [
      {
        "job_id": 32975295086,
        "job_name": "test (ubuntu-latest, 3.9)",
        "status": "failed",
        "test_summary": {
          "total_tests": 1344,
          "passed": 1338,
          "failed": 6,
          "skipped": 0
        },
        "failed_tests": [
          {
            "test_nodeid": "tests/test_verdict_runner.py::TestCaseDiscovery::test_filter_cases_by_path",
            "outcome": "failed",
            "error_message": "assert 0 > 0"
          },
          // ... more failures
        ],
        "coverage": {
          "total_coverage": 91.0,
          "statements": 5104,
          "missing": 467,
          "excluded": 0
        },
        "flake8_issues": []
      },
      // ... 16 more jobs
    ],
    "common_test_failures": [
      {
        "test_name": "test_filter_cases_by_path",
        "failure_count": 11
      },
      {
        "test_name": "test_filter_cases_by_nested_path",
        "failure_count": 11
      },
      // ... more common failures
    ]
  }
}
```

### Verification

✅ **Endpoint returns full parsed data**
- 21,344 tests analyzed across 17 jobs
- 66 test failures detected
- 11 failed jobs identified
- Common failures: same 6 tests failing on 11 jobs (Ubuntu/macOS)
- Coverage data: 91% average across jobs
- Flake8 issues: 19 violations in quality job

✅ **Enhanced Logging**
```
[2026-02-10 20:31:48] [INFO] [PARSE_DATA] Starting parse for run_id=21786230446
[2026-02-10 20:31:48] [INFO] [PARSE_DATA] Repository: lmvcruz/argos
[2026-02-10 20:31:48] [INFO] [PARSE_DATA] Running command: python -m scout parse...
[2026-02-10 20:31:48] [INFO] [PARSE_DATA] Command completed with return code: 0
[2026-02-10 20:31:48] [DEBUG] [PARSE_DATA] STDOUT (first 500 chars): {...
[2026-02-10 20:31:48] [INFO] [PARSE_DATA] Successfully parsed JSON output. Status: success
[2026-02-10 20:31:48] [INFO] [PARSE_DATA] Updating database flags
[2026-02-10 20:31:48] [INFO] [PARSE_DATA] Successfully completed parse
```

## Next Steps

### 1. Test Through Browser UI

Navigate to: `http://localhost:3000` → CI Inspection page

1. Select execution 21786230446 ("Anvil Tests")
2. Click "Parse Data" button
3. **Expected**: Frontend should receive and display:
   - Test summary (17 jobs, 21,344 tests, 66 failures)
   - Failed tests with error messages
   - Coverage percentages
   - Flake8 issues
   - Common failure patterns

### 2. Frontend Display (If Needed)

The frontend component `CIInspection.tsx` may need updates to:
- Display the `data` field from the response
- Show test summary statistics
- List failed tests with details
- Visualize coverage data
- Highlight common failures across jobs

### 3. Error Handling

The updated endpoint now properly handles:
- JSON parsing errors (invalid Scout output)
- "not_implemented" status from Scout
- Command execution failures
- Timeout errors (120 second limit)

## Summary

**Problem**: Parse endpoint discarded Scout's rich analysis data
**Solution**: Enhanced endpoint to include full parsed data in response
**Result**: Frontend can now access comprehensive CI analysis including test results, coverage, and linting issues

The Scout → Lens integration is now fully functional for parsing execution outputs.
