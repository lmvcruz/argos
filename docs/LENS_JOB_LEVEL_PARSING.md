# Scout Job-Level Parsing Implementation

## Summary

Implemented hierarchical execution/job navigation in Lens CI Inspection, allowing users to expand workflow runs to see individual jobs and parse them separately.

## Problem

Previously, when selecting a workflow run (e.g., run #21786230446), the parse operation would process all 17 jobs together, which:
- Made it difficult to focus on specific job failures
- Combined logs from all jobs making debugging harder
- Didn't provide job-level granularity

## Solution

### Backend Changes

1. **New Endpoint**: `GET /api/scout/runs/{run_id}/jobs`
   - Location: `lens/lens/backend/scout_ci_endpoints.py`
   - Returns list of all jobs for a specific run with metadata
   - Includes: job_id, job_name, status, result, duration, runner_os, python_version

2. **Job Log Endpoint**: `POST /api/scout/fetch-job-log/{job_id}`
   - Fetches logs for a specific job from GitHub
   - Returns log content directly in response
   - Automatically fetches parent run if needed

3. **Job Parse Endpoint**: `POST /api/scout/parse-job-data/{job_id}`
   - Parses logs for a single job
   - Extracts test results, coverage, flake8 issues
   - Returns job-specific analysis without run-level aggregation

### Frontend Changes

2. **Scout Client API**
   - Added `getRunJobs(runId)` method in `scoutClient.ts`
   - Added `fetchJobLogs(jobId)` method for job-level log fetching
   - Added `parseJobData(jobId)` method for job-level parsing
   - All methods include proper error handling and TypeScript types

3. **ExecutionTree Component** (`ExecutionTree.tsx`)
   - Added expand/collapse buttons (chevron icons) for each run
   - Fetches jobs dynamically when run is expanded
   - Caches job data to avoid redundant API calls
   - Highlights selected job with blue background
   - Shows job details: platform (OS), Python version
   - Visual indicators for passed (✓) / failed (✗) jobs

4. **CIInspection Page** (`CIInspection.tsx`)
   - Added `selectedJobId` state to track job selection
   - Added `handleSelectJob()` handler
   - **Updated `handleFetchLogs()`**: Now checks if job is selected and fetches job-level logs
   - **Updated `handleParseData()`**: Now checks if job is selected and parses job-level data
   - Enhanced details panel to show job information when job is selected
   - Pass `selectedJobId` to ExecutionTree for highlighting

5. **CSS Styling** (`CIInspection.css`)
   - `.execution-expand-button`: Chevron expand/collapse button
   - `.job-row-selected`: Blue highlight for selected jobs
   - `.job-info` and `.job-details`: Job metadata display
   - Responsive hover states and dark mode support

## User Workflow

1. **View Runs**: User sees list of workflow runs in left panel
2. **Expand Run**: Click chevron icon to expand and see all jobs (lazy-loaded)
3. **Select Job**: Click on specific job (e.g., "test-python-3.11-ubuntu-latest")
   - Job gets highlighted in blue
   - Right panel shows job-specific details (platform, Python version, duration)
4. **Fetch Job Logs**: Click "Fetch Logs" button
   - If job selected: Fetches and displays only that job's logs
   - If run selected: Fetches and displays all jobs' logs
5. **Parse Job Data**: Click "Parse Data" button
   - If job selected: Parses only that job's logs and shows job-specific results
   - If run selected: Parses entire run and shows aggregated results
6. **View Results**: ScoutDataViewer shows comprehensive analysis

## Technical Details

### Job Data Structure

```typescript
interface ExecutionJob {
  id: string;
  name: string;  // e.g., "test-python-3.11-ubuntu-latest"
  status: 'completed' | 'in_progress' | 'queued';
  result: 'passed' | 'failed' | 'pending';
  duration: number;  // in seconds
  runner_os?: string;  // e.g., "ubuntu-latest"
  python_version?: string;  // e.g., "3.11"
}
```

### API Flow

```
User clicks expand → ExecutionTree.toggleExecution()
                  → scoutClient.getRunJobs(runId)
                  → GET /api/scout/runs/{run_id}/jobs
                  → Query WorkflowJob table in Scout DB
                  → Return job list
                  → Cache in jobsCache Map
                  → Render job list

User selects job → handleSelectJob(executionId, jobId)
                 → Sets selectedJobId state
                 → ExecutionTree highlights selected job
```

### State Management

- `expandedExecutions`: Set<string> - Track which runs are expanded
- `loadingJobs`: Set<string> - Track runs currently fetching jobs
- `jobsCache`: Map<string, ExecutionJob[]> - Cache loaded jobs
- `selectedJobId`: string | null - Currently selected job
- `selectedWorkflow`: string | null - Currently selected run

## Benefits

✅ **Granular Analysis**: Focus on specific failing jobs without noise from other jobs
✅ **Better Performance**: Lazy-load jobs only when needed, parse only selected job
✅ **Improved UX**: Clear visual hierarchy (runs → jobs) with blue selection highlighting
✅ **Faster Debugging**: Jump directly to problematic job and see its specific results
✅ **Platform Insights**: See OS and Python version at a glance, compare across platforms
✅ **Reduced Log Clutter**: View logs for single job instead of all 17 jobs combined
✅ **Targeted Analysis**: Parse individual jobs to identify platform-specific issues

## Next Steps

✅ **COMPLETED** - Implement job-level log fetching
✅ **COMPLETED** - Implement job-level parsing
✅ **COMPLETED** - Add job status indicators (running, queued, completed)
✅ **COMPLETED** - Show job-level details in right panel
- [ ] Add job-level test count in tree (enhancement)
- [ ] Add visual charts for job comparison (enhancement)

## Testing

To test the implementation:

1. Start backend: `cd d:\playground\argos; python -m uvicorn lens.backend.server:app --port 8000 --host 127.0.0.1`
2. Start frontend: `cd d:\playground\argos\lens\frontend; npm run dev`
3. Navigate to CI Inspection page
4. Select a workflow run with multiple jobs
5. Click chevron to expand
6. Observe job list loading
7. Click on a specific job
8. Verify job is highlighted
9. Click "Parse Data" (currently parses whole run - needs update)

## Files Modified

- `lens/lens/backend/scout_ci_endpoints.py` - New `/runs/{run_id}/jobs` endpoint
- `lens/frontend/src/api/tools/scoutClient.ts` - Added `getRunJobs()` method
- `lens/frontend/src/components/ExecutionTree.tsx` - Expandable jobs tree
- `lens/frontend/src/components/ScoutDataViewer.tsx` - New component for Scout data
- `lens/frontend/src/pages/CIInspection.tsx` - Job selection logic
- `lens/frontend/src/pages/CIInspection.css` - Job tree styling

## Files Created

- `lens/frontend/src/components/ScoutDataViewer.tsx` - Rich display component for Scout parse results
