# Scout CLI to Lens UI Integration Guide

**Purpose**: Translate Scout's command-line interface into an intuitive browser-based UI
**Status**: Design & Planning
**Created**: February 2026

---

## Overview: CLI → UI Translation Model

Scout's CLI has a hierarchical command structure. Here's how we translate each level to UI:

```
CLI Level 1: Command         →  UI Level 1: Section/Tab (scout, ci)
CLI Level 2: Subcommand      →  UI Level 2: Feature Page (sync, analyze, etc.)
CLI Level 3: Options/Args    →  UI Level 3: Form Controls & Parameters
CLI Output Format            →  UI Output: Visualization Component
CLI Execution (streaming)    →  UI UX: Real-time progress & WebSocket updates
```

---

## Part 1: High-Level Architecture

### Routes & Navigation Structure

```
Lens UI
├── /scout                           # Scout Section
│   ├── /scout/dashboard            # Quick access to all Scout features
│   ├── /scout/sync                 # Full pipeline (fetch→parse→save)
│   ├── /scout/workflows            # List and view workflows
│   ├── /scout/analysis             # Failure analysis
│   ├── /scout/patterns             # Failure pattern detection
│   ├── /scout/comparison           # Compare workflow runs
│   ├── /scout/health               # Flaky tests & quality metrics
│   ├── /scout/config               # Configuration & settings
│   └── /scout/ci/*                 # CI-specific commands
│       ├── /scout/ci/fetch         # Fetch from GitHub
│       ├── /scout/ci/download      # Download logs
│       ├── /scout/ci/analyze       # Analyze patterns
│       ├── /scout/ci/compare       # Local vs CI comparison
│       └── /scout/ci/show          # View run details
```

### Component Hierarchy

```
ScoutSection (Main Container)
├── ScoutNavbar
│   ├── Dashboard
│   ├── Data Sync
│   ├── Workflows
│   ├── Analysis
│   ├── Health
│   └── Settings
└── Route-based Page Component
    ├── SyncDashboard
    ├── WorkflowBrowser
    ├── FailureAnalysis
    ├── HealthMetrics
    └── ConfigPanel
```

---

## Part 2: Feature-by-Feature Translation

### **Feature 1: Data Sync (scout sync)**

#### CLI Command
```bash
scout sync --fetch-last 10 --filter-workflow "Main" --skip-parse
```

#### UI Translation
**Page**: `/scout/sync`

**Form Structure**:
```
┌─────────────────────────────────────────┐
│         Scout Data Sync Manager         │
├─────────────────────────────────────────┤
│                                         │
│ Fetch Mode (Radio Buttons)              │
│ ○ Fetch All Available                   │
│ ○ Fetch Last N Executions               │
│   └─ [Input: 10] ◄──────── Binds to --fetch-last
│ ○ Specific Workflow                     │
│   └─ [Dropdown: Select Workflow]        │
│                                         │
│ Additional Filters (Optional)           │
│ ☐ Filter by Workflow Name               │
│   └─ [Input: "Main CI"]                 │ ◄──── --filter-workflow
│                                         │
│ Skip Stages (Checkboxes)                │
│ ☐ Skip Fetch (use cached data)          │ ◄──── --skip-fetch
│ ☐ Skip Parse                            │ ◄──── --skip-parse
│ ☐ Skip Save CI Data                     │ ◄──── --skip-save-ci
│ ☐ Skip Save Analysis                    │ ◄──── --skip-save-analysis
│                                         │
│ Database Paths (Advanced/Collapsed)     │
│ CI Database: [scout.db]                 │ ◄──── --ci-db
│ Analysis DB: [scout-analysis.db]        │ ◄──── --analysis-db
│                                         │
│         [Start Sync] [Save Preset]      │
└─────────────────────────────────────────┘
```

**Real-Time Progress Display**:
```
┌─────────────────────────────────────────┐
│ ▶ Running Sync Pipeline...              │
├─────────────────────────────────────────┤
│ [████████░░] 80% Complete               │
│                                         │
│ Stage 1: Fetching Data          ✓      │
│ Stage 2: Parsing Logs           ⏳      │
│ Stage 3: Saving Results         ⌛      │
│                                         │
│ Progress (2/3 jobs completed):          │
│ [✓] Main CI - Run #42                   │
│ [⏳] Build CI - Run #41                  │
│ [ ] Test CI - Run #40                   │
│                                         │
│ [Cancel] [Pause]                        │
└─────────────────────────────────────────┘
```

**Backend API**:
```python
POST /api/scout/sync
{
    "fetch_mode": "fetch_last",           # "fetch_all", "fetch_last", "specific_workflow"
    "fetch_count": 10,
    "filter_workflow": "Main",
    "skip_fetch": false,
    "skip_parse": false,
    "skip_save_ci": false,
    "skip_save_analysis": false,
    "ci_db": "scout.db",
    "analysis_db": "scout-analysis.db"
}

Response: { job_id: "sync-12345", status: "started" }

WS /api/scout/sync/{job_id}/progress
Message: {
    "stage": "fetch",
    "percentage": 45,
    "current_job": "Main CI - Run #42",
    "stats": { "fetched": 2, "parsed": 1, "failed": 0 }
}
```

**State Management** (React Context):
```typescript
interface SyncState {
    isRunning: boolean;
    currentStage: 'fetch' | 'parse' | 'save';
    percentage: number;
    currentJob: string;
    stats: { fetched: number; parsed: number; failed: number };
    results: SyncResult[];
}
```

---

### **Feature 2: Workflow Browser (scout ci fetch + scout ci show)**

#### CLI Commands
```bash
scout ci fetch --workflow "Main" --limit 50 --with-jobs
scout ci show --run-id 12345
```

#### UI Translation
**Page**: `/scout/workflows`

**Layout**:
```
┌───────────────────────────────────────────────────────────┐
│              Workflow Runs Browser                        │
├─────────────────────┬───────────────────────────────────┤
│ Filters (Left)      │ Workflow List (Middle)             │
├─────────────────────┼───────────────────────────────────┤
│ Workflow:           │ [Search box]                       │
│ [Dropdown ▼]        │                                   │
│                     │ ✓ Main CI - #123                  │
│ Status:             │   Feb 5, 2:34 PM | 3m 45s         │
│ ○ All               │   ├─ ✓ Build (ubuntu)             │
│ ○ Success           │   ├─ ✓ Test (py3.11)              │
│ ○ Failed            │   ├─ ✗ Coverage (py3.10)          │
│                     │   └─ ✓ Deploy                      │
│ Limit Results:      │                                   │
│ [Dropdown: 50] ◄─── ├ [Details Panel ▶]                │
│                     │                                   │
│ [Refresh] [Sync]    │ ✗ Main CI - #122                 │
│                     │   Feb 5, 1:15 PM | 2m 12s         │
│                     │   ...                              │
└─────────────────────┴───────────────────────────────────┘
```

**Details Panel** (when run selected):
```
┌──────────────────────────────────────┐
│ Main CI - Run #123                   │
├──────────────────────────────────────┤
│ Status:  ✓ Success                   │
│ Started: Feb 5, 2:34 PM              │
│ Branch:  main                        │
│ Commit:  abc1234                     │
│ Duration: 3m 45s                     │
│                                      │
│ Jobs (4):                            │
│ ├─ ✓ Build [ubuntu-latest, 1m 30s]   │
│ ├─ ✓ Test [ubuntu-latest, 1m 45s]    │
│ │   └─ [View Tests ▶]                │
│ ├─ ✗ Coverage [ubuntu-latest, 2m]    │
│ │   └─ [View Error ▶]                │
│ └─ ✓ Deploy [ubuntu-latest, 30s]     │
│                                      │
│ [Compare] [Re-run] [Download Logs]   │
└──────────────────────────────────────┘
```

**Backend API**:
```python
GET /api/scout/workflows
    ?limit=50
    &status=all|success|failed
    &workflow_name=Main
    &branch=main

Response: {
    "workflows": [
        {
            "run_id": 123,
            "run_number": 42,
            "workflow_name": "Main CI",
            "status": "completed",
            "conclusion": "success",
            "started_at": "2026-02-05T14:34:00Z",
            "duration_seconds": 225,
            "branch": "main",
            "commit_sha": "abc1234",
            "jobs": [...]
        }
    ],
    "total": 42
}

GET /api/scout/workflows/{run_id}
Response: {
    "run_id": 123,
    "jobs": [
        {
            "job_id": "j-1",
            "job_name": "Build",
            "status": "completed",
            "conclusion": "success",
            "runner_os": "ubuntu-latest",
            "duration_seconds": 90,
            "test_results": [...]
        }
    ]
}

GET /api/scout/workflows/{run_id}/jobs/{job_id}
Response: {
    "job_id": "j-1",
    "test_results": [
        {
            "test_nodeid": "tests/test_cli.py::test_sync",
            "outcome": "passed",
            "duration": 1.23,
            "error_message": null
        }
    ]
}
```

---

### **Feature 3: Failure Analysis (scout analyze + scout ci analyze)**

#### CLI Commands
```bash
scout analyze --format json --output report.json
scout ci analyze --window 30 --runner-os ubuntu-latest --format console
```

#### UI Translation
**Page**: `/scout/analysis`

**Two-Tab Layout**:

**Tab 1: Quick Analysis**
```
┌────────────────────────────────────────┐
│   Failure Pattern Analysis             │
├────────────────────────────────────────┤
│ Analysis Window: [Dropdown: 30 days]   │ ◄── --window
│ Runner OS: [Checkbox: ubuntu/windows]  │ ◄── --runner-os
│ Workflow: [Optional Filter]            │
│                                        │
│ [Run Analysis] [Export as JSON]        │
├────────────────────────────────────────┤
│                                        │
│ Results: 47 failures analyzed          │
│                                        │
│ By Type:                               │
│ ├─ Timeout (12 failures)               │
│ │  └─ Tests waiting for resources      │
│ ├─ Platform (8 failures)               │
│ │  └─ Windows-only issues              │
│ ├─ Setup (15 failures)                 │
│ │  └─ Environment config problems      │
│ ├─ Dependency (12 failures)            │
│ │  └─ Missing or incompatible libs     │
│                                        │
│ [Expand All] [View Detailed Report]    │
└────────────────────────────────────────┘
```

**Tab 2: Full Report**
```
┌────────────────────────────────────────┐
│   Detailed Failure Report              │
├────────────────────────────────────────┤
│                                        │
│ Overall Statistics (30 days):          │
│ ┌──────────────────────────────────┐   │
│ │ Total Runs: 42                   │   │
│ │ Successful: 34 (81%)             │   │
│ │ Failed: 8 (19%)                  │   │
│ └──────────────────────────────────┘   │
│                                        │
│ By Runner OS:                          │
│ ┌──────────────────────────────────┐   │
│ │ ubuntu-latest: 40 runs (95%)     │   │
│ │ windows-latest: 2 runs (5%)      │   │
│ │ macos-latest: 0 runs (0%)        │   │
│ └──────────────────────────────────┘   │
│                                        │
│ [Export CSV] [Export JSON]             │
└────────────────────────────────────────┘
```

**Backend API**:
```python
POST /api/scout/analyze
{
    "window_days": 30,
    "runner_os": ["ubuntu-latest", "windows-latest"],
    "workflow_name": null
}

Response: {
    "analysis": {
        "total_runs": 42,
        "successful_runs": 34,
        "failed_runs": 8,
        "success_rate": 81.0,
        "patterns": {
            "timeout": [
                {
                    "description": "Tests waiting for resources",
                    "count": 12,
                    "test_nodeids": ["tests/test_build.py::test_compile"],
                    "suggested_fix": "Increase timeout threshold"
                }
            ],
            ...
        }
    }
}
```

---

### **Feature 4: Flaky Test Detection (scout flaky)**

#### CLI Command
```bash
scout flaky --threshold 0.5 --min-runs 5
```

#### UI Translation
**Page**: `/scout/health`

**Health Dashboard**:
```
┌──────────────────────────────────────────────┐
│         CI Health & Quality Metrics          │
├──────────────────────────────────────────────┤
│                                              │
│ Flaky Test Detection                         │
│ Sensitivity: [Slider: 50%] ◄── --threshold  │
│ Min Occurrences: [Input: 5] ◄── --min-runs  │
│                                              │
│ [Analyze] [View Trends]                      │
│                                              │
├──────────────────────────────────────────────┤
│ Flaky Tests Found: 7                         │
│                                              │
│ ├─ tests/test_io.py::test_file_read         │
│ │  Pass Rate: 70% (7/10 passed)              │
│ │  Status: [⚠️ FLAKY]                        │
│ │  Last Failed: Feb 5, 10:23 AM              │
│ │                                            │
│ ├─ tests/test_network.py::test_timeout      │
│ │  Pass Rate: 60% (3/5 passed)               │
│ │  Status: [⚠️ HIGHLY FLAKY]                 │
│ │  Last Failed: Feb 5, 9:15 AM               │
│ │                                            │
│ [Investigate] [Pin Root Cause]               │
└──────────────────────────────────────────────┘
```

**Backend API**:
```python
GET /api/scout/health/flaky-tests
    ?threshold=0.5
    &min_runs=5

Response: {
    "flaky_tests": [
        {
            "test_nodeid": "tests/test_io.py::test_file_read",
            "pass_rate": 0.70,
            "fail_rate": 0.30,
            "total_runs": 10,
            "last_failed": "2026-02-05T10:23:00Z",
            "trend": "stable"  # or "improving", "degrading"
        }
    ]
}
```

---

### **Feature 5: Workflow Comparison (scout ci compare)**

#### CLI Command
```bash
scout ci compare --local-run run-1 --ci-run 12345 --format json
```

#### UI Translation
**Page**: `/scout/comparison`

**Comparison Interface**:
```
┌─────────────────────────────────────────────────────────┐
│            Local vs CI Test Comparison                  │
├──────────────────────┬──────────────────────────────────┤
│ Selectors (Left)     │ Comparison Results (Right)       │
├──────────────────────┼──────────────────────────────────┤
│                      │                                  │
│ Local Run ID:        │ ✓ Tests Passed in Both  (28)     │
│ [Input: run-1]       │   └─ All good!                   │
│                      │                                  │
│ CI Run ID:           │ ✗ Failed in CI Only  (3)         │
│ [Input: 12345]       │   ├─ test_network.py::timeout    │
│                      │   ├─ test_db.py::connection      │
│                      │   └─ test_api.py::rate_limit     │
│                      │                                  │
│ [Compare]            │ ✗ Failed in Local Only  (1)      │
│                      │   └─ test_utils.py::format       │
│                      │                                  │
│                      │ ⚠️  Flaky (different outcomes)    │
│                      │   (None - good sign!)            │
│                      │                                  │
│                      │ [Export Results] [View Logs]     │
└──────────────────────┴──────────────────────────────────┘
```

**Backend API**:
```python
POST /api/scout/compare
{
    "local_run_id": "run-1",
    "ci_run_id": 12345
}

Response: {
    "comparison": {
        "passed_in_both": 28,
        "failed_in_ci_only": 3,
        "failed_in_local_only": 1,
        "flaky": 0,
        "details": {
            "failed_ci_only": [
                {
                    "test_nodeid": "tests/test_network.py::test_timeout",
                    "ci_outcome": "failed",
                    "local_outcome": "passed",
                    "failure_reason": "Network timeout (CI only)"
                }
            ]
        }
    }
}
```

---

### **Feature 6: Configuration (scout config)**

#### CLI Commands
```bash
scout config show
scout config get github.token
scout config set github.token "ghp_..."
```

#### UI Translation
**Page**: `/scout/config`

**Settings Panel**:
```
┌──────────────────────────────────────────┐
│        Scout Configuration              │
├──────────────────────────────────────────┤
│                                          │
│ GitHub Settings                          │
│ ├─ GitHub Token                          │
│ │  [•••••••••••] [Show] [Change]          │ ◄── set github.token
│ │  Status: ✓ Configured                  │
│ │                                        │
│ ├─ Repository                            │
│ │  [owner/repo dropdown]                 │ ◄── set github.repo
│ │  Current: lmvcruz/argos                │
│ │                                        │
│ Database Settings                        │
│ ├─ CI Database Path                      │
│ │  [scout.db] [Browse]                   │
│ │                                        │
│ ├─ Analysis Database Path                │
│ │  [scout-analysis.db] [Browse]          │
│ │                                        │
│ Advanced Settings                        │
│ ├─ Fetch Timeout (sec)                   │
│ │  [30]                                  │
│ │                                        │
│ ├─ Parse Cache                           │
│ │  ☑ Enable Cache                        │
│ │                                        │
│ [Save] [Reset to Defaults] [Export]      │
└──────────────────────────────────────────┘
```

**Backend API**:
```python
GET /api/scout/config
Response: {
    "settings": {
        "github.token": "***",
        "github.repo": "lmvcruz/argos",
        "ci_db_path": "scout.db",
        "analysis_db_path": "scout-analysis.db"
    }
}

POST /api/scout/config
{
    "key": "github.token",
    "value": "ghp_new_token"
}

GET /api/scout/config
Response: { "message": "All settings", "config": {...} }
```

---

## Part 3: State Management Strategy

### Context Structure

```typescript
interface ScoutContextType {
  // Global Scout state
  syncState: SyncState;
  workflowState: WorkflowState;
  analysisState: AnalysisState;
  healthState: HealthState;
  configState: ConfigState;

  // Action dispatchers
  startSync: (params: SyncParams) => Promise<void>;
  cancelSync: () => Promise<void>;
  fetchWorkflows: (params: FetchParams) => Promise<void>;
  runAnalysis: (params: AnalysisParams) => Promise<void>;
  updateConfig: (key: string, value: any) => Promise<void>;

  // WebSocket connection
  wsConnected: boolean;
  wsError: string | null;
}
```

### State Persistence

```json
// scout-state.json (in browser localStorage)
{
  "lastSync": "2026-02-05T14:30:00Z",
  "selectedWorkflow": "Main CI",
  "viewPreferences": {
    "analysisWindow": 30,
    "groupBy": "status"
  },
  "recentComparisons": [
    { "localRun": "run-1", "ciRun": 12345 }
  ]
}
```

---

## Part 4: Real-Time Operations

### WebSocket Strategy

**For Long-Running Operations** (fetch, parse, sync):

```typescript
// Frontend
useEffect(() => {
  if (!syncRunning) return;

  const ws = new WebSocket(`ws://localhost:8000/api/scout/sync/${jobId}/progress`);

  ws.onmessage = (event) => {
    const progress = JSON.parse(event.data);
    dispatch({
      type: 'UPDATE_SYNC_PROGRESS',
      payload: progress
    });
  };

  ws.onerror = () => {
    dispatch({ type: 'SYNC_ERROR', payload: 'Connection lost' });
  };

  return () => ws.close();
}, [syncRunning, jobId]);
```

```python
# Backend
@app.websocket("/api/scout/sync/{job_id}/progress")
async def sync_progress_stream(websocket: WebSocket, job_id: str):
    await websocket.accept()

    job = get_sync_job(job_id)
    while job.is_running:
        progress = {
            "stage": job.current_stage,
            "percentage": job.percentage_complete,
            "current_job": job.current_job,
            "stats": job.stats.dict()
        }
        await websocket.send_json(progress)
        await asyncio.sleep(0.5)
```

---

## Part 5: Component Library

### Reusable Scout Components

```typescript
// Components organized by function
scout/
├── components/
│   ├── SyncPanel.tsx          # Sync form + progress
│   ├── WorkflowBrowser.tsx    # Workflow list + details
│   ├── AnalysisPanel.tsx      # Analysis visualization
│   ├── HealthDashboard.tsx    # Flaky test metrics
│   ├── ComparisonView.tsx     # Side-by-side comparison
│   ├── ConfigPanel.tsx        # Settings management
│   └── common/
│       ├── ProgressBar.tsx
│       ├── RunStatusBadge.tsx
│       ├── JobTree.tsx
│       ├── TestResultTable.tsx
│       └── ErrorDetails.tsx
│
├── hooks/
│   ├── useScoutSync.ts        # Sync operations
│   ├── useWorkflows.ts        # Workflow queries
│   ├── useAnalysis.ts         # Analysis queries
│   └── useWebSocket.ts        # WS connection management
│
├── context/
│   └── ScoutContext.tsx       # Global state
│
└── utils/
    ├── scout-api.ts           # API client
    ├── formatters.ts          # Format duration, dates, etc
    └── constants.ts           # CLI option defaults
```

---

## Part 6: Form-to-API Mapping Examples

### Example 1: Sync Form → API Call

```typescript
// Form values
{
  fetchMode: "fetch_last",
  fetchCount: 10,
  filterWorkflow: "Main",
  skipFetch: false,
  skipParse: true,
  skipSaveCI: false,
  skipSaveAnalysis: false
}

// Transformed to API
POST /api/scout/sync
{
  "fetch_mode": "fetch_last",
  "fetch_count": 10,
  "filter_workflow": "Main",
  "skip_fetch": false,
  "skip_parse": true,
  "skip_save_ci": false,
  "skip_save_analysis": false
}
```

### Example 2: Filter Controls → Query Params

```typescript
// Filter state
{
  limit: 50,
  status: "failed",
  workflow: "Main CI",
  branch: "main"
}

// Query string
GET /api/scout/workflows?limit=50&status=failed&workflow_name=Main%20CI&branch=main
```

### Example 3: Analysis Options → Request Body

```typescript
// Form inputs
{
  window: 30,
  runnerOs: ["ubuntu-latest", "windows-latest"],
  minCount: 2
}

// API request
POST /api/scout/analyze
{
  "window_days": 30,
  "runner_os": ["ubuntu-latest", "windows-latest"],
  "min_count": 2
}
```

---

## Part 7: Error Handling & Feedback

### Error States

```typescript
interface ErrorState {
  type: 'fetch_error' | 'parse_error' | 'sync_error' | 'timeout';
  message: string;
  recovery: string;  // Suggested action
  timestamp: ISO8601;
}

// Examples
{
  type: 'fetch_error',
  message: 'GitHub token expired',
  recovery: 'Update your GitHub token in Settings'
}

{
  type: 'sync_error',
  message: 'Database locked',
  recovery: 'Wait for current sync to complete, then retry'
}
```

### Success Notifications

```typescript
{
  type: 'sync_complete',
  message: 'Synced 5 workflows, 32 jobs, 8 failures',
  duration: 45.23,  // seconds
  action: 'View Results'
}
```

---

## Part 8: Performance Considerations

### Pagination Strategy

```typescript
// For large workflow lists
GET /api/scout/workflows?page=1&limit=20&sort=-started_at

Response: {
  "workflows": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 256,
    "pages": 13,
    "has_next": true
  }
}
```

### Lazy Loading

- Load workflow details only when expanded
- Paginate test results in job details
- Stream large log outputs instead of loading all at once

### Caching Strategy

```typescript
// Cache Scout data with time-to-live
interface CachedData<T> {
  data: T;
  timestamp: number;
  ttl: number;  // milliseconds
}

// Example: workflows cached for 5 minutes
const workflows = useQuery(
  ['scout-workflows', filters],
  fetchWorkflows,
  { staleTime: 5 * 60 * 1000 }
);
```

---

## Part 9: User Workflows (Happy Paths)

### Workflow 1: Quick Data Sync

**Goal**: User wants latest CI data in Lens

1. Open `/scout/sync`
2. Select "Fetch Last 10"
3. Click "Start Sync"
4. Watch progress bar
5. Notification: "Synced 10 workflows"
6. Navigate to `/scout/workflows`

### Workflow 2: Investigate CI Failure

**Goal**: User sees failing test in Lens, wants to understand why

1. Open `/scout/workflows`
2. Select failed run
3. View job details (expand job)
4. Click on failed test
5. See error message + suggestion
6. Open `/scout/analysis` to see if it's a known pattern
7. View comparison if similar failure locally

### Workflow 3: Detect Flaky Tests

**Goal**: User wants to find unreliable tests

1. Open `/scout/health`
2. Run "Flaky Test Detection"
3. Review list sorted by pass rate
4. Click on flaky test
5. See trend (stable, improving, degrading)
6. View historical runs
7. Export list for team discussion

---

## Part 10: Implementation Roadmap

### Phase 1: Core Infrastructure (1 week)
- [ ] Scout routing structure
- [ ] ScoutContext for state management
- [ ] Base API client wrapper
- [ ] WebSocket utility hook
- [ ] Error handling framework

### Phase 2: Sync Feature (1 week)
- [ ] SyncPanel form component
- [ ] Sync progress display
- [ ] Real-time progress via WebSocket
- [ ] Result summary view

### Phase 3: Workflow Browser (1 week)
- [ ] WorkflowBrowser component
- [ ] Job detail panel
- [ ] Test result listing
- [ ] Status indicators

### Phase 4: Analysis Features (1 week)
- [ ] FailureAnalysis component
- [ ] Pattern visualization
- [ ] HealthDashboard (flaky tests)
- [ ] ComparisonView (local vs CI)

### Phase 5: Polish & Settings (1 week)
- [ ] ConfigPanel
- [ ] Presets management
- [ ] Error messages
- [ ] Dark mode support

---

## Part 11: Key Design Principles for Scout UI

### 1. Progressive Disclosure
- Show essential controls first
- Hide advanced options in "Advanced" sections
- Reveal details on demand

### 2. Async Operations
- All sync/fetch/analyze use WebSocket for progress
- Never block UI during long operations
- Show cancellation option
- Clear error states with recovery steps

### 3. Consistency
- Use same color scheme for status (red=failed, green=success, yellow=warning)
- Consistent date/time formatting
- Reuse components across features

### 4. Feedback
- Visual confirmation of every user action
- Progress indication for long operations
- Clear success/error messages
- Undo where possible (e.g., config changes)

### 5. Discoverability
- Tooltips on form fields explaining CLI equivalents
- "Learn more" links to Scout documentation
- Example values in input fields
- Inline help for advanced options

---

## Summary: The Mapping

| CLI Concept | UI Element | Example |
|---|---|---|
| Command | Section (Tab/Route) | `scout sync` → `/scout/sync` |
| Subcommand | Feature Page | `scout ci fetch` → `/scout/ci/fetch` |
| Option/Flag | Form Control | `--fetch-last` → `<input type="number">` |
| Mutually exclusive | Radio Buttons | `--fetch-all` vs `--fetch-last` |
| Boolean flag | Checkbox | `--skip-parse` → `<checkbox>` |
| Required args | Text Input | `--run-id` → `<input required>` |
| Enum choices | Dropdown | `--format [console|json|csv|html]` → `<select>` |
| CLI output stream | WebSocket + Progress | Real-time terminal output |
| Command execution | Async job + tracking | Job ID → Progress component |
| Output display | Visualization component | JSON → Table, Tree, Badge, etc. |

