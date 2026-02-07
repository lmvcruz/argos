# Anvil & Full Data Flow Logging Implementation

## Overview

Implemented comprehensive logging for the complete data flow from frontend through backend to anvil and back:

```
Frontend (logs request) → Backend (logs receive + anvil call + response) → Anvil executes (logs via anvil logger) → Backend returns → Frontend (logs response)
```

## Features Implemented

### 1. Frontend-to-Backend Logging (Frontend)

**File: `lens/frontend/src/utils/api.ts`**

All API requests now logged at DEBUG level with full payloads:

```typescript
// Example logs generated:
[API_REQUEST] POST /api/inspection/validate
  body: { path: "...", language: "python", validator: "black", target: "...", fix: false }

[API_SUCCESS] POST /api/inspection/validate Response:
  data: { results: [...], report: {...} }

[API_POST] Request payload:
  { path: "...", language: "python", validator: "black", target: "...", fix: false }
```

**Changes:**
- `apiRequest()` logs method, endpoint, request body, response data, and status
- `apiPost()` logs full request payload before sending
- `apiPut()` logs full request payload before sending
- `apiGet()` logs query parameters before sending
- `apiDelete()` logs deletion confirmation with endpoint

### 2. Backend Request/Response Logging

**File: `lens/lens/backend/server.py`**

Validation endpoint now logs complete request/response cycle:

**Request Logging:**
```
[VALIDATE] Received request: path=..., language=python, validator=black, target=..., fix=False
```

**Anvil Call Logging:**
```
[VALIDATE] Files to validate: ['file1.py', 'file2.py', ...]
[VALIDATE] Calling anvil validator: BlackValidator
[VALIDATE] Validator options: {'fix': False}
```

**Result Logging:**
```
[VALIDATE] Validation completed - errors=2, warnings=0
[VALIDATE] Anvil result: <ValidationResult object>
[VALIDATE] Converting 2 errors and 0 warnings to Lens format
```

**Response Logging:**
```
[VALIDATE] Response to frontend: { results: [...], report: {...} }
[VALIDATE] Completed: total_issues=2, errors=2, warnings=0, files_checked=30
```

### 3. Anvil Logger Integration

**File: `lens/lens/backend/server.py` - initialization**

```python
# Configure anvil logging to use our logger
anvil_logger = get_logger('anvil')
anvil_logger.setLevel(logging.DEBUG)
```

This captures all anvil module logs at DEBUG level and writes them to `backend.log`.

### 4. Complete Data Flow Visibility

**What gets logged:**

1. **Frontend logs what it sends:**
   - HTTP method, endpoint, full request body (POST/PUT payloads)
   - Query parameters (GET requests)

2. **Backend logs what it receives:**
   - Input parameters validation
   - Which anvil validator is being called
   - Validator class and options being passed

3. **Backend logs anvil execution:**
   - Files being validated
   - Anvil validator name and type
   - Full anvil result object with errors/warnings

4. **Backend logs what it returns:**
   - Complete response object being sent to frontend
   - Summary statistics (total issues, errors, warnings)

5. **Frontend logs what it receives:**
   - Full response data from API
   - Response status code

## Logging Examples

### Validation Request Flow

**Frontend:**
```
[DEBUG] [API_REQUEST] POST /api/inspection/validate
  body: { path: "D:\argos", language: "python", validator: "black", target: "D:\argos\scout", fix: false }
```

**Backend receives:**
```
[DEBUG] [VALIDATE] Received request: path=D:\argos, language=python, validator=black, target=D:\argos\scout, fix=False
```

**Anvil called:**
```
[DEBUG] [VALIDATE] Files to validate: ['scout_cli.py', 'scout_main.py', ...]
[DEBUG] [VALIDATE] Calling anvil validator: BlackValidator
[DEBUG] [VALIDATE] Validator options: {'fix': False}
```

**Anvil result received:**
```
[DEBUG] [VALIDATE] Validation completed - errors=2, warnings=0
[DEBUG] [VALIDATE] Anvil result: <ValidationResult errors=[...] warnings=[...] />
```

**Backend returns:**
```
[DEBUG] [VALIDATE] Response to frontend: { results: [...], report: {total_issues: 2, ...} }
[INFO] [VALIDATE] Completed: total_issues=2, errors=2, warnings=0, files_checked=30
```

**Frontend receives:**
```
[DEBUG] [API_SUCCESS] POST /api/inspection/validate Response:
  data: { results: [{ file: "scout_cli.py", line: 10, message: "..." }], report: {...} }
```

## Log Levels Used

- **DEBUG**:
  - All input parameters
  - All output data
  - Intermediate steps
  - File lists and validator details

- **INFO**:
  - Operation completion
  - Summary statistics
  - Major milestones

- **ERROR**:
  - Failures and exceptions
  - Invalid inputs
  - Missing validators

## Files Modified

1. **lens/frontend/src/utils/api.ts**
   - Enhanced `apiRequest()` with full payload logging
   - Enhanced `apiPost()`, `apiPut()`, `apiGet()` with parameter logging

2. **lens/lens/backend/server.py**
   - Changed logging level from INFO to DEBUG
   - Added anvil logger configuration
   - Enhanced validation endpoint with:
     - Input parameter logging
     - Files to validate logging
     - Anvil call logging
     - Anvil result logging
     - Response logging

## Benefits

1. **Complete Visibility**: See exactly what data moves between frontend, backend, and anvil
2. **Easy Debugging**: Trace where issues occur in the flow
3. **Performance Monitoring**: Can identify slow steps
4. **Audit Trail**: Full record of what was validated and what results were returned
5. **Integration Testing**: Can verify anvil integration by examining logs

## Testing

Both servers running successfully with comprehensive logging:

```
Backend: uvicorn on http://127.0.0.1:8000 (DEBUG logging enabled)
Frontend: vite dev server on http://localhost:3000 (API logging enabled)

Sample validation execution captured:
✓ Frontend sends POST /api/inspection/validate with full payload
✓ Backend receives and logs request parameters
✓ Backend logs which anvil validator is called
✓ Backend logs files being validated (30 files)
✓ Backend receives anvil result (2 errors, 0 warnings)
✓ Backend logs response being sent to frontend
✓ Response includes all error details and diffs
```

## Next Steps

- Open browser to http://localhost:3000
- Run a validation on any Python files
- Check logs to see complete data flow with DEBUG entries
- Look at `~/.argos/lens/logs/backend.log` for anvil execution details
- Look at `~/.argos/lens/logs/frontend.log` for API request/response details
