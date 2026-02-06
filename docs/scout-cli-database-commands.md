# Scout CLI Database Commands

## Overview

The Scout CLI has been extended with four new commands for querying and displaying execution data stored in the Scout database. These commands provide developers with quick access to:

- **Remote executions** from GitHub Actions
- **Local execution logs** stored in the Scout database
- **Raw logs** for specific executions
- **Parsed analysis data** for specific executions

## New Commands

### 1. `scout list` - List Remote Executions from GitHub

Query GitHub API for recent workflow executions.

**Usage:**
```bash
scout list [OPTIONS]
```

**Options:**
- `--workflow WORKFLOW` - Filter by workflow name (e.g., "Tests", "CI")
- `--branch BRANCH` - Filter by branch name (e.g., "main", "develop")
- `--status STATUS` - Filter by execution status (e.g., "completed", "in_progress")
- `--last N` - Limit to last N results (default: 10)
- `--token TOKEN` - GitHub token (or use GITHUB_TOKEN env var)
- `--repo OWNER/REPO` - Repository (or use GITHUB_REPO env var)
- `-v, --verbose` - Enable verbose output
- `-q, --quiet` - Suppress non-error output

**Examples:**
```bash
# List last 10 executions of "Tests" workflow
scout list --workflow "Tests" --last 10

# List completed executions on main branch
scout list --branch main --status completed

# List with custom repo and token
scout list --token ghp_xxx --repo owner/repo --workflow "CI" --last 5
```

**Output:** Formatted table showing run IDs, workflow names, status, branches, and start times

---

### 2. `scout db-list` - List Local Execution Logs from Database

Query the Scout database for stored workflow executions.

**Usage:**
```bash
scout db-list [OPTIONS]
```

**Options:**
- `--workflow WORKFLOW` - Filter by workflow name
- `--branch BRANCH` - Filter by branch name
- `--status STATUS` - Filter by execution status
- `--last N` - Limit to last N results (default: 10)
- `--db DB` - Path to Scout database (default: scout.db)
- `-v, --verbose` - Enable verbose output
- `-q, --quiet` - Suppress non-error output

**Examples:**
```bash
# List last 10 stored executions
scout db-list --last 10

# List failed executions on main branch from database
scout db-list --branch main --status failure --last 5

# Use custom database path
scout db-list --db /path/to/custom_scout.db --last 20
```

**Output:** Formatted table showing run IDs, workflow names, status, branches, and start times from local database

**Benefits:**
- Works offline (no GitHub API required)
- Access to locally stored execution history
- Quick filtering of stored data
- No rate limiting concerns

---

### 3. `scout show-log` - Display Local Logs for Specific Execution

Retrieve and display raw logs for workflow executions stored in the Scout database.

**Usage:**
```bash
scout show-log [OPTIONS]
```

**Options:**
- `--workflow WORKFLOW` - Filter by workflow name
- `--branch BRANCH` - Filter by branch name
- `--status STATUS` - Filter by execution status
- `--last N` - Limit to show last N logs (default: 10)
- `--db DB` - Path to Scout database (default: scout.db)
- `-v, --verbose` - Enable verbose output
- `-q, --quiet` - Suppress non-error output

**Examples:**
```bash
# Show logs for last 10 executions
scout show-log --last 10

# Show logs for failed executions on main branch
scout show-log --branch main --status failure --last 3

# Show logs filtered by workflow
scout show-log --workflow "Tests" --last 5
```

**Output:** Raw execution logs displayed in console, grouped by run ID and job ID

**Use Cases:**
- Debug test failures by reviewing full logs
- Analyze execution behavior without GitHub API
- Inspect specific test runs stored locally
- Reference for CI investigation

---

### 4. `scout show-data` - Display Parsed Analysis Data from Database

Retrieve and display parsed test analysis data for workflow executions.

**Usage:**
```bash
scout show-data [OPTIONS]
```

**Options:**
- `--workflow WORKFLOW` - Filter by workflow name
- `--branch BRANCH` - Filter by branch name
- `--status STATUS` - Filter by execution status
- `--last N` - Limit to show last N results (default: 10)
- `--db DB` - Path to Scout database (default: scout.db)
- `-v, --verbose` - Enable verbose output
- `-q, --quiet` - Suppress non-error output

**Examples:**
```bash
# Show parsed data for last 10 executions
scout show-data --last 10

# Show analysis data for failed runs
scout show-data --status failure --last 5

# Show data for specific workflow
scout show-data --workflow "Tests" --branch main --last 3
```

**Output:** 
- **Console format** (default): Formatted analysis results with key metrics
- Displays failure patterns, test statistics, and recommendations

**Use Cases:**
- Quick review of test analysis without full reports
- Extract key metrics for trending analysis
- Compare failures across runs
- Identify recurring patterns in test failures

---

## Common Usage Patterns

### 1. Quick Database Health Check
```bash
scout db-list --last 5 -q
```

### 2. Find Recent Failures
```bash
scout db-list --status failure --branch main --last 10
```

### 3. Analyze Specific Execution
```bash
scout show-log --workflow "Tests" --branch main --last 1
scout show-data --workflow "Tests" --branch main --last 1
```

### 4. Compare Local vs Remote
```bash
scout db-list --last 5  # Show local
scout list --last 5     # Show remote (GitHub)
```

### 5. Investigation Workflow
```bash
# 1. Find failed execution
scout db-list --status failure --last 1

# 2. View the raw logs
scout show-log --status failure --last 1

# 3. Check parsed analysis
scout show-data --status failure --last 1
```

---

## Database Integration

### Schema

The commands query these database tables:

- **WorkflowRun**: Workflow execution metadata (run_id, workflow_name, branch, status, etc.)
- **ExecutionLog**: Raw logs for each workflow run
- **AnalysisResult**: Parsed test analysis data (failures, patterns, recommendations)

### Database Location

By default, Scout uses `scout.db` in the current directory. Specify a custom path with:
```bash
scout db-list --db /path/to/custom.db
```

### Database Setup

Ensure the Scout database is initialized:
```bash
scout fetch --workflow "Tests" --last 5  # Creates/updates database
scout sync                                 # Syncs to database
```

---

## Comparison: list vs db-list

| Feature | `list` | `db-list` |
|---------|--------|----------|
| Data Source | GitHub API | Local Database |
| Requires Token | ✓ (unless cached) | ✗ |
| Requires Network | ✓ | ✗ |
| Rate Limited | ✓ | ✗ |
| Historical Data | Limited | As stored |
| Speed | Slower | Faster |
| Use Case | Real-time data | Offline/local analysis |

---

## Integration with Lens UI

These commands will be exposed through the Lens web interface with:

1. **ExecutionList Component** - Display local and remote executions
2. **ExecutionDetail View** - Show logs and analysis data
3. **Execution Comparison** - Compare local vs remote executions
4. **Trending Dashboard** - Track execution metrics over time

---

## Error Handling

All commands include comprehensive error handling:

- **Missing Database**: Clear error message with suggestion to run `scout fetch` or `scout sync`
- **No Matching Data**: "No executions found" with helpful suggestions
- **GitHub API Errors**: Graceful fallback to local database
- **Corrupt Data**: Error with recovery suggestions

### Example Error Messages

```
Error: No executions found in database
Suggestion: Run 'scout fetch --workflow "Tests"' to populate the database
```

```
Error: No logs found for matching executions
Suggestion: Ensure logs have been downloaded with 'scout download --run-id <id>'
```

---

## Performance Notes

- **db-list**: O(n) query on local database, sub-second response for typical sizes
- **list**: Network request to GitHub API, ~2-5 seconds typical
- **show-log**: Retrieves logs from database, speed depends on database size
- **show-data**: Quick lookup of analysis results, typically <100ms

For large databases (>10K runs), use filtering options:
```bash
scout db-list --workflow "Tests" --branch main --last 10  # Fast
scout db-list --last 100                                   # May be slower
```

---

## Next Steps: Lens Integration

These CLI commands will be exposed through Lens UI as:

1. **ExecutionList Component Enhancement**
   - Display both local and remote executions
   - Quick filter by workflow, branch, status
   - One-click navigation to logs and analysis

2. **ExecutionDetail View**
   - Show raw logs inline
   - Display parsed analysis data
   - Compare with previous executions

3. **Database Status**
   - Show database stats (number of stored runs, disk usage, etc.)
   - Option to clean up old data
   - Sync status indicator

See [Lens Documentation](./lens-specification.md) for more details on UI integration.
