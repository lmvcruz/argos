# Lens UI Implementation for Scout Database Commands

## Overview

The Lens frontend has been enhanced with a new **Database Commands** component that provides a user-friendly interface to query and inspect local Scout database executions and analysis data. This complements the Scout CLI commands with an interactive web-based UI.

## Components

### DatabaseCommands.tsx

**Location:** `frontend/src/components/Scout/DatabaseCommands.tsx`

A comprehensive React component that provides three main functionalities:

#### 1. **List Executions** (`scout list`)
- Query local Scout database for workflow executions
- Filter by:
  - Workflow name
  - Branch
  - Status (Completed, In Progress, Queued)
  - Last N executions (5, 10, 20, 50)
- Displays:
  - Run ID
  - Workflow name
  - Status with visual indicators (✓ success, ✗ failure, ⚠ in progress)
  - Branch name with icon
  - Execution start time
  - Quick action buttons for logs and analysis data

#### 2. **Show Logs** (`scout show-log`)
- Display execution logs for a specific workflow run
- Features:
  - Input field to specify run ID
  - Job-level log display with expandable sections
  - Test summary for each job:
    - Total tests
    - Passed (green)
    - Failed (red)
    - Skipped (gray)
  - Job metadata (ID, status, start/completion times)
  - Visual status indicators for quick assessment

#### 3. **Show Analysis Data** (`scout show-data`)
- Display parsed analysis results for a specific workflow run
- Includes:
  - Run header with workflow, branch, and status
  - Statistics grid:
    - Total tests count
    - Passed tests (green highlight)
    - Failed tests (red highlight)
    - Pass rate percentage (blue highlight)
  - Failure patterns section:
    - Shows categorized failure types
    - Lists affected tests (up to 5 per pattern, with "more" indicator)
    - Helps identify systematic issues

## API Integration

### Backend Endpoints

The component communicates with three REST endpoints added to `lens/backend/scout_ci_endpoints.py`:

#### 1. `GET /api/scout/list`

**Query Parameters:**
```
- workflow (optional): Filter by workflow name (case-insensitive)
- branch (optional): Filter by branch name (case-insensitive)
- status (optional): Filter by status (completed, in_progress, queued)
- last (optional, default: 10, max: 100): Limit results
```

**Response:**
```json
{
  "executions": [
    {
      "run_id": 12345,
      "workflow_name": "test.yml",
      "status": "completed",
      "conclusion": "success",
      "branch": "main",
      "started_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:45:00Z",
      "duration_seconds": 900
    }
  ]
}
```

#### 2. `GET /api/scout/show-log/{run_id}`

**Response:**
```json
{
  "run_id": 12345,
  "workflow_name": "test.yml",
  "branch": "main",
  "status": "completed",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:45:00Z",
  "jobs": [
    {
      "job_id": "job-001",
      "job_name": "Run Tests",
      "status": "completed",
      "conclusion": "success",
      "started_at": "2024-01-15T10:31:00Z",
      "completed_at": "2024-01-15T10:44:00Z",
      "test_summary": {
        "total": 150,
        "passed": 145,
        "failed": 3,
        "skipped": 2
      }
    }
  ],
  "total_jobs": 1
}
```

#### 3. `GET /api/scout/show-data/{run_id}`

**Response:**
```json
{
  "run_id": 12345,
  "workflow_name": "test.yml",
  "branch": "main",
  "status": "completed",
  "started_at": "2024-01-15T10:30:00Z",
  "statistics": {
    "total_tests": 150,
    "passed": 145,
    "failed": 3,
    "skipped": 2,
    "pass_rate": 96.7
  },
  "failure_patterns": {
    "timeout": ["test_slow_api_call", "test_database_query"],
    "assertion": ["test_expected_behavior", "test_edge_case"]
  },
  "jobs_count": 1
}
```

## UI Layout

### Header Section
- Title: "Scout Database Commands"
- Subtitle: "Query and inspect local Scout database executions and analysis data"
- Database icon for visual identification

### Command Tabs
Three tabs to switch between commands:
1. **List Executions** - Primary tab for finding executions
2. **Show Logs** - For viewing execution logs
3. **Analysis Data** - For viewing analysis results

### Error Handling
- Global error display with:
  - Error icon
  - Title ("Error")
  - Detailed error message
  - Red color scheme for visibility

### Loading States
- All action buttons show "Loading..." text when requests are in flight
- Disabled state prevents duplicate submissions
- Smooth transitions during data load

## State Management

The component uses React hooks for state management:

```typescript
// List command state
const [executions, setExecutions] = useState<ExecutionListItem[]>([]);
const [listFilters, setListFilters] = useState({
  workflow: '',
  branch: '',
  status: '',
  last: 10,
});

// Show-log command state
const [selectedRunId, setSelectedRunId] = useState<number | null>(null);
const [logData, setLogData] = useState<LogDataType | null>(null);
const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());

// Show-data command state
const [analysisRunId, setAnalysisRunId] = useState<number | null>(null);
const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);

// Global state
const [loading, setLoading] = useState(false);
const [error, setError] = useState<string | null>(null);
```

## Navigation Integration

The component is integrated into the Scout layout with:
- **Route:** `/scout/database-commands`
- **Navigation Item:** "Database" with `Database` icon
- **Description:** "Query local database"
- **Position:** Third item in navigation (after Executions and Workflows)

## Usage Workflow

### Typical User Journey

1. **Discover Executions:**
   - Click "Database" in Scout navigation
   - View "List Executions" tab (default)
   - Apply filters (optional)
   - Click "Execute List Command" to retrieve matching executions

2. **Inspect Logs:**
   - Click "Logs" button on execution row, OR
   - Switch to "Show Logs" tab
   - Enter run ID manually
   - Click "Show Logs" to fetch logs
   - Expand jobs to see test summaries

3. **Analyze Results:**
   - Click "Data" button on execution row, OR
   - Switch to "Analysis Data" tab
   - Enter run ID manually
   - Click "Show Analysis" to fetch analysis
   - Review statistics and failure patterns

## Styling and Design

- **Color Scheme:**
  - Blue (#0066cc): Primary actions, active states, info
  - Green (#00aa00): Success status, passed tests
  - Red (#cc0000): Failure status, failed tests
  - Yellow (#ffaa00): In-progress status
  - Gray: Neutral text, borders, backgrounds

- **Components:**
  - Lucide icons for visual consistency
  - Tailwind CSS for responsive design
  - Cards with borders for content sections
  - Tables for data display
  - Status badges with icons for quick identification

- **Responsive:**
  - Grid layouts (2-4 columns based on context)
  - Overflow handling for wide tables
  - Proper spacing and padding throughout
  - Mobile-friendly where applicable

## Error Handling

The component handles various error scenarios:

1. **Network Errors:** Displays "Connection failed" with suggestion to check backend
2. **Not Found:** Displays 404 error when run ID doesn't exist
3. **Invalid Parameters:** Displays validation errors from backend
4. **Timeout:** User can retry without refreshing page

## Performance Considerations

- **Pagination:** Backend limits results to 100 items max
- **Filtering:** Applied server-side to reduce data transfer
- **Lazy Loading:** Job details only expanded on user request
- **State Management:** Minimal re-renders with proper hook optimization

## Future Enhancements

Potential improvements for future iterations:

1. **Export Functionality:**
   - Export logs to text/CSV
   - Export analysis data as JSON/PDF

2. **Search and Filtering:**
   - Full-text search across logs
   - Advanced filter builder
   - Saved filter presets

3. **Comparison:**
   - Side-by-side log comparison
   - Execution timeline visualization
   - Failure pattern trends

4. **Integration:**
   - Direct links to GitHub Actions runs
   - Integration with external bug tracking
   - Slack/email notifications for failures

5. **Performance:**
   - Virtual scrolling for large result sets
   - Client-side filtering options
   - Cached results with refresh controls

## Testing

The component is designed to work with the Scout backend endpoints. To test:

1. **Ensure Scout backend is running:**
   ```bash
   python -m lens.backend.server
   ```

2. **Populate database with test data:**
   ```bash
   scout fetch --workflow test.yml
   ```

3. **Navigate to `/scout/database-commands` in the UI**

4. **Test each command:**
   - List: Apply filters and verify results
   - Show Logs: Select an execution and view logs
   - Show Data: View analysis statistics and patterns
