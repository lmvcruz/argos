# Test Discovery - Current State & Action Plan

**Date**: February 9, 2026
**Status**: ⚠️ PARTIALLY WORKING - Backend implementation complete, frontend not displaying data

---

## 🎯 Overview

Test Discovery is a feature in Lens that allows users to:
1. Browse project files in a tree structure (File Tree)
2. Discover and display test suites and test cases (Test Discovery)
3. Execute individual tests or test suites

**Current Issue**: Source tree is not showing any files in the frontend UI, despite the backend being properly implemented and fixed.

---

## ✅ What We Have (Implemented & Fixed)

### 1. Backend API - File Tree Endpoint
**Endpoint**: `GET /api/inspection/files?path={project_path}`
**Location**: [lens/backend/server.py](d:\playground\argos\lens\lens\backend\server.py#L329-L419)

**Status**: ✅ IMPLEMENTED & FIXED

**Implementation Details**:
- Recursively builds file tree structure with max depth of 10
- Filters out hidden files/folders (`.git`, `__pycache__`, `node_modules`, etc.)
- Returns children of root directory directly for better UX
- **Fix Applied** (Line 414-419): Returns `file_tree["children"]` instead of `[file_tree]` to avoid showing only the root folder

**Response Format**:
```json
{
  "files": [
    {
      "id": "path/to/file",
      "name": "filename.py",
      "type": "file|folder",
      "children": [...]  // Only for folders
    }
  ]
}
```

### 2. Backend API - Test Discovery Endpoint
**Endpoint**: `GET /api/tests/discover?path={project_path}`
**Location**: [lens/backend/server.py](d:\playground\argos\lens\lens\backend\server.py#L2190-L2290)

**Status**: ✅ IMPLEMENTED & FIXED

**Implementation Details**:
- Uses `pytest --collect-only` to discover tests
- **Fix Applied** (Line 2223): Increased timeout from 30s to 120s to handle monorepos
- Parses pytest output to extract test suites and test cases
- Groups tests by file (suite)

**Response Format**:
```json
{
  "suites": [
    {
      "id": "path/to/test_file.py",
      "name": "test_file",
      "file": "path/to/test_file.py",
      "tests": [
        {
          "id": "test_id",
          "name": "test_name",
          "suite": "test_file"
        }
      ]
    }
  ],
  "total_suites": 49,
  "total_tests": 1356,
  "timestamp": "2026-02-09T..."
}
```

**Verified Working**: On 2026-02-09, test script confirmed:
- File tree: 33 items returned for anvil project
- Test discovery: 49 suites with 1356 tests in 7.8 seconds

### 3. Frontend Components
**Location**: [lens/frontend/src/pages/LocalTests.tsx](d:\playground\argos\lens\frontend\src\pages\LocalTests.tsx)

**Status**: ✅ IMPLEMENTED

**Components**:
- `TestSuiteTree`: Left panel showing discovered test suites
- `TestFileTree`: Right panel showing project file tree
- `TestRunner`: Component for executing tests

**API Integration**:
- Lines 65-92: Fetches file tree from `/api/inspection/files`
- Lines 95-130: Fetches test suites from `/api/tests/discover`

---

## ❌ What's Not Working

### 1. Frontend Not Displaying Data
**Symptom**: Source tree shows no files despite backend returning data

**Possible Causes**:
1. **Backend Not Running**: The backend process may have stopped or crashed
   - Last known status: Started on port 8000 (PID 53488)
   - Needs verification: Check if backend is responding to API calls

2. **CORS Issues**: Frontend on `localhost:3000` may be blocked from accessing backend on `localhost:8000`
   - Check browser console for CORS errors

3. **Frontend State Management**: React state may not be updating properly
   - Check if API calls are succeeding but UI not re-rendering
   - Verify `fileTree` and `testSuites` state variables

4. **API Response Format Mismatch**: Frontend expecting different data structure
   - Backend returns `{"files": [...]}`
   - Frontend may expect different key or structure

5. **Frontend Not Making API Calls**: useEffect hooks may not be triggering
   - Check if `selectedProject` is properly set
   - Verify useEffect dependencies

---

## 🔧 Critical Issues to Fix

### Issue #1: Backend Process Management
**Problem**: Backend keeps shutting down when commands are run in the same terminal

**Current Workaround**: Created [start_backend.ps1](d:\playground\argos\start_backend.ps1) to run in separate window

**Permanent Solution Needed**:
- Create proper service/daemon management
- Use process manager (PM2, Windows Service, Docker, etc.)
- Add restart-on-failure logic

### Issue #2: Working Directory Dependency
**Problem**: Backend must be run from `d:\playground\argos` (not `d:\playground\argos\lens`)

**Why**: Looks for Anvil database at `./.anvil/execution.db` relative to CWD

**Impact**:
- Incorrect CWD → Database not found → Server fails silently
- Caused multiple startup failures during debugging

**Solution Options**:
1. Make path absolute in code: Use `Path(__file__).parent.parent / ".anvil" / "execution.db"`
2. Add CWD validation on startup
3. Add environment variable for ARGOS_ROOT
4. Update documentation with clear startup instructions

---

## 📋 Action Plan to Complete Task

### Phase 1: Verify Backend (IMMEDIATE)
1. ✅ Check if backend is running and responding
   ```powershell
   netstat -ano | findstr ":8000"
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health"
   ```

2. ✅ Test file tree endpoint
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/inspection/files?path=d:\playground\argos\anvil"
   ```

3. ✅ Test test discovery endpoint
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/tests/discover?path=d:\playground\argos\anvil"
   ```

### Phase 2: Verify Frontend (IMMEDIATE)
1. ✅ Check if frontend is running
   ```powershell
   netstat -ano | findstr ":3000"
   ```

2. ✅ Open browser dev tools and check:
   - Console for JavaScript errors
   - Network tab for API call failures
   - React DevTools for component state

3. ✅ Verify API calls are being made:
   - Look for requests to `/api/inspection/files` and `/api/tests/discover`
   - Check response status codes (should be 200)
   - Check response data structure

### Phase 3: Debug Frontend Integration (IF NEEDED)
1. Add console.log statements in LocalTests.tsx to track data flow:
   ```typescript
   console.log("File tree response:", fileTreeResponse);
   console.log("Test suites response:", testSuitesResponse);
   console.log("Current state:", { fileTree, testSuites });
   ```

2. Check TestFileTree component:
   - Verify it's receiving the `files` prop
   - Check rendering logic
   - Ensure tree expand/collapse works

3. Check API client configuration:
   - Verify base URL is correct
   - Check timeout settings
   - Ensure proper error handling

### Phase 4: Fix Process Management (CRITICAL)
1. Create Docker Compose setup for services:
   ```yaml
   services:
     backend:
       working_dir: /app
       command: uvicorn lens.backend.server:app --host 0.0.0.0 --port 8000
     frontend:
       command: npm run dev
   ```

2. OR: Create systemd/Windows Service definitions

3. OR: Add proper signal handling in server.py

### Phase 5: Documentation & Testing
1. Update README with:
   - Correct startup procedures
   - Required working directory
   - Environment setup
   - Troubleshooting guide

2. Create automated tests:
   - Backend API endpoint tests
   - Frontend component tests
   - Integration tests

3. Add health checks and monitoring

---

## 🔍 Verification Checklist

Before marking as "COMPLETE", verify:

- [ ] Backend starts successfully from correct directory
- [ ] Backend /api/health endpoint returns 200 OK
- [ ] Backend /api/inspection/files returns file tree with 30+ items
- [ ] Backend /api/tests/discover returns test suites (40+ suites)
- [ ] Frontend loads successfully on http://localhost:3000
- [ ] Frontend makes API calls to backend (visible in Network tab)
- [ ] Frontend displays file tree in right panel
- [ ] Frontend displays test suites in left panel
- [ ] Can expand/collapse folders in file tree
- [ ] Can expand/collapse test suites
- [ ] Can select individual tests
- [ ] Test execution works (if implemented)
- [ ] No console errors in browser
- [ ] No 500 errors in backend logs
- [ ] Services stay running (don't auto-shutdown)

---

## 📊 Test Results Log

### 2026-02-09 - Initial Testing (SUCCESSFUL)
**Test Script**: `test_tree_issue.py`
**Results**:
- File tree: ✅ 33 items returned
- Test discovery: ✅ 49 suites, 1356 tests
- Duration: 7.8 seconds
- Conclusion: Backend APIs working correctly

### 2026-02-09 - Current Status (UNKNOWN)
**Status**: Backend PID 53488 started, but not responding to API calls
**Next**: Need to verify if backend is still running and frontend is making requests

---

## 🎯 Success Criteria

Test Discovery will be considered **COMPLETE** when:

1. ✅ User can open Lens frontend in browser
2. ✅ User can see list of projects in Projects page
3. ✅ User can navigate to "Local Tests" page
4. ✅ File tree loads automatically showing project structure (30+ files)
5. ✅ Test tree loads automatically showing test suites (40+ suites)
6. ✅ User can expand/collapse folders and test suites
7. ✅ User can select individual tests
8. ✅ Both panels update when switching between projects
9. ✅ Services stay running without manual intervention
10. ✅ No errors in console or logs

---

## 📝 Notes

- **Monorepo Consideration**: Argos is a monorepo with multiple projects (anvil, scout, forge, lens, verdict), so test discovery can take 20-30 seconds
- **Timeout Fix**: Changed from 30s to 120s to accommodate large codebases
- **UX Improvement**: File tree now shows contents directly instead of requiring root folder expansion
- **Performance**: Consider pagination or lazy-loading for projects with 1000+ tests

---

## 🔗 Related Files

- Backend Server: [lens/backend/server.py](d:\playground\argos\lens\lens\backend\server.py)
- Frontend Page: [lens/frontend/src/pages/LocalTests.tsx](d:\playground\argos\lens\frontend\src\pages\LocalTests.tsx)
- Test Script: [test_tree_issue.py](d:\playground\argos\test_tree_issue.py)
- Startup Script: [start_backend.ps1](d:\playground\argos\start_backend.ps1)

---

**Last Updated**: 2026-02-09
**Next Review**: After verification of current backend/frontend status
