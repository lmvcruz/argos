# Scout → Anvil → Lens Integration Plan

## Overview

Integrate **CI logs from GitHub Actions** with Anvil storage and Lens analytics:
- Download CI logs with smart skipping (avoid redundant downloads/parsing)
- Parse logs using Anvil with dynamic parser selection per job type
- Store results in Anvil database (`space="ci"`)
- Visualize and run actions from Lens UI

---

## 1. Scout CI Sync Command

```bash
# Download and parse all CI logs
scout ci sync

# Limit to last N workflow executions
scout ci sync --limit 10

# Filter by specific workflow
scout ci sync --workflow "Anvil Tests"

# Combine filters: specific workflow, last 5 runs
scout ci sync --workflow "Anvil Tests" --limit 5

# Force re-download existing files
scout ci sync --force-download --limit 5

# Force re-parse and update database
scout ci sync --force-parse --limit 5

# Both (full refresh) for a specific workflow
scout ci sync --workflow "Forge Tests" --force-download --force-parse --limit 10
```

### Implementation Flow

1. **Get workflow runs** from GitHub API (paginated)
   - Filter by workflow name if `--workflow` specified
   - Otherwise retrieve all workflows
2. **For each run** (respecting `--limit`):
   - Check if `.scout/ci-logs/{workflow_id}/{job_id}/{run_id}.log` exists
     - If exists AND `!--force-download` → skip download
     - Else → download log, count lines
   - Check if execution data in Anvil DB for this run
     - If exists AND `!--force-parse` → skip parsing
     - Else → parse with selected parser, save to DB
3. **Verbose output**:
   ```
   [✓] Downloaded forge-tests [workflow=123] job=pytest
       File: .scout/ci-logs/forge-tests/pytest/456789.log (1,245 lines)

   [✓] Parsed forge-tests/pytest [120 tests, 5 failed, 0 skipped]
       Saved: anvil DB (space="ci", run_id=456789)
   ```

### Skip Logic

- Skip download if: log file exists locally AND `--force-download` NOT set
- Skip parse if: execution data in DB AND `--force-parse` NOT set
- Both can be overridden independently
- Workflow filtering is applied before download/parse decisions (only processes matching workflows)

### Workflow Filtering

**`--workflow <name>`**
- Filters GitHub Actions workflows by exact name match
- Examples:
  - `--workflow "Anvil Tests"` → syncs only the "Anvil Tests" workflow
  - `--workflow "Forge Tests"` → syncs only the "Forge Tests" workflow
- If omitted: syncs all workflows
- Can be combined with `--limit` (limits within the filtered workflow)

---

## 2. Parser Selection Mechanism

**Problem**: Different CI job types output different formats and need different parsers.

**Solution**: Job-to-parser mapping file (`.scout/parser-config.yaml`) using Anvil's built-in parsers

For the Anvil Tests workflow, we have 4 job types:

| Job | Purpose | Parser(s) | Output Info |
|-----|---------|-----------|------------|
| `test` | Runs pytest (all Python versions/OS) | `PytestParser` | Test execution time + result |
| `coverage` | Runs pytest with coverage (Ubuntu 3.11 only) | `PytestParser` | Test execution time + result + coverage % |
| `quality` | Runs pre-commit checks (flake8, black, isort) | `LintParser` (generic) | Style/format violations |
| `lint` | Runs individual linters separately | `Flake8Parser`, `BlackParser`, `IsortParser` | Detailed lint violations per tool |

```yaml
# .scout/parser-config.yaml
job_patterns:
  # Pattern: exact job name match or regex
  # Anvil Tests workflow
  - pattern: "^test$"
    parser: "PytestParser"
    description: "Runs pytest tests (all platforms/versions)"

  - pattern: "^coverage$"
    parser: "PytestParser"
    description: "Runs pytest with coverage (Ubuntu 3.11 only)"

  - pattern: "^quality$"
    parser: "LintParser"
    description: "Runs pre-commit checks (flake8, black, isort combined)"

  - pattern: "^lint$"
    parsers:
      - "Flake8Parser"
      - "BlackParser"
      - "IsortParser"
    description: "Runs individual linters separately"

  # For other workflows (future)
  - pattern: "^Forge Tests$"
    parser: "PytestParser"

  - pattern: "^Verdict Tests$"
    parser: "PytestParser"

  - pattern: "^Scout Tests$"
    parser: "PytestParser"
```

**Why these parsers?**

1. **`test` job → `PytestParser`**
   - Job output: `pytest --verbose --tb=short` (no coverage)
   - Extracts: test node IDs, pass/fail/skip status, execution time per test
   - Result: Individual test results with timing
   - Example output: `tests/integration/test_end_to_end.py::TestCompleteValidationWorkflow::test_complete_python_validation_workflow PASSED [5.23s]`

2. **`coverage` job → `PytestParser`**
   - Job output: `pytest --cov=anvil --cov-report=term-missing --verbose`
   - Extracts: test node IDs, pass/fail/skip status, execution time per test, coverage percentages
   - Result: Individual test results with timing + coverage summary
   - Example output: `tests/integration/test_end_to_end.py::TestCompleteValidationWorkflow::test_complete_python_validation_workflow PASSED [5.23s]` + `anvil/parsers/black_parser.py 94%`

3. **`quality` job → `LintParser`**
   - Job output: `python scripts/pre-commit-check.py` (runs flake8, black, isort combined)
   - Extracts: file paths, linting issues (aggregated)
   - Result: Summary of style/format violations from all three tools
   - Single parser because it's treating the combined output

4. **`lint` job → `Flake8Parser`, `BlackParser`, `IsortParser`**
   - Job output: Individual commands (flake8, black --check, isort --check-only, autoflake)
   - Extracts: Detailed violations per tool with specific codes/messages
   - Result: Detailed code quality issues grouped by linter
   - Advantage: Can distinguish which tool flagged which issue

**Example: Real job names from GitHub Actions**

When you run the workflow, the actual job names appear in Scout as:
- `test` - matches pattern `^test$` (runs on all 3 OS × 5 Python versions = 15 jobs)
- `coverage` - matches pattern `^coverage$` (runs once on Ubuntu 3.11)
- `quality` - matches pattern `^quality$`
- `lint` - matches pattern `^lint$` (processes multiple parser outputs)

**Pattern Matching Rules**:
- `^test$` = exact match for "test"
- `^coverage$` = exact match for "coverage"
- `^quality$` = exact match for "quality"
- `^lint$` = exact match for "lint"
- Can also use regex: `^test .*ubuntu.*` to match specific OS combinations if needed

**Available Anvil Parsers** (if you need to parse other formats):
- `PytestParser` - Python pytest test results + coverage integration
- `Flake8Parser` - Python style/quality linting (F, E, W, C series codes)
- `BlackParser` - Python code formatting differences
- `IsortParser` - Python import sorting
- `CoverageParser` - Code coverage reports (standalone)
- `GTestParser` - C++ Google Test results
- `ClangTidyParser` - C++ clang-tidy linting
- `CppcheckParser` - C++ static analysis
- `VultureParser` - Python dead code detection
- `RadonParser` - Python complexity metrics
- `AutoflakeParser` - Python unused import detection
- `LintParser` - Generic/fallback lint output

**Runtime Resolution**:
```python
# scout/integration/parser_resolver.py
from anvil.parsers import (
    PytestParser, Flake8Parser, BlackParser, IsortParser,
    CoverageParser, GTestParser, ClangTidyParser,
    CppcheckParser, VultureParser, RadonParser, AutoflakeParser, LintParser
)

PARSER_MAP = {
    "PytestParser": PytestParser,
    "Flake8Parser": Flake8Parser,
    "BlackParser": BlackParser,
    "IsortParser": IsortParser,
    "CoverageParser": CoverageParser,
    "GTestParser": GTestParser,
    "ClangTidyParser": ClangTidyParser,
    "CppcheckParser": CppcheckParser,
    "VultureParser": VultureParser,
    "RadonParser": RadonParser,
    "AutoflakeParser": AutoflakeParser,
    "LintParser": LintParser,
}

def resolve_parser(job_name: str, config: ParserConfig) -> object:
    """
    Match job name against patterns, return appropriate Anvil parser instance.

    Args:
        job_name: Job name from GitHub Actions (e.g., "test", "coverage", "quality", "lint")
        config: Parser configuration loaded from .scout/parser-config.yaml

    Returns:
        Instantiated Anvil parser (e.g., PytestParser()) or list of parsers
    """
    for pattern_config in config.job_patterns:
        if re.match(pattern_config.pattern, job_name):
            parser_name = pattern_config.parser

            # Handle single parser or multiple parsers
            if isinstance(parser_name, list):
                return [PARSER_MAP.get(pname)() for pname in parser_name if pname in PARSER_MAP]

            parser_class = PARSER_MAP.get(parser_name)
            if parser_class:
                return parser_class()

    # Default fallback if no pattern matches
    return LintParser()
```
---

## 3. Lens Integration

### Lens Actions System

Lens provides a UI to trigger and visualize Scout-Anvil operations:

```yaml
# lens/actions/scout_ci_sync.yaml
name: "Sync CI Logs"
type: "scout_ci_sync"
description: "Download and parse latest CI logs"

parameters:
  - name: "limit"
    type: "number"
    label: "Limit to last N runs"
    default: 10

  - name: "force_download"
    type: "boolean"
    label: "Force re-download"
    default: false

  - name: "force_parse"
    type: "boolean"
    label: "Force re-parse"
    default: false

output:
  - type: "log"
    label: "Sync Output"
  - type: "chart"
    label: "Test Results by Status"
  - type: "table"
    label: "Failed Tests"
```

### Lens UI Flow

1. **Action Panel**: User clicks "Sync CI Logs", sets parameters
2. **Execution**: Lens triggers `scout ci sync` with flags
3. **Output Display**:
   - Live log streaming (downloads, parsing progress)
   - Summary statistics (total tests, pass/fail counts)
   - Failed test details (clickable, links to GitHub)
4. **Integration**: Results auto-refresh comparison reports (local vs CI)

### Implementation

```python
# lens/api/actions.py
@app.post("/actions/scout_ci_sync")
def execute_scout_ci_sync(params: SyncParams):
    """
    Execute scout ci sync with given parameters.

    Returns:
    - Streaming logs
    - Final statistics
    - Database updates trigger report refresh
    """
    cmd = build_command(
        "scout", "ci", "sync",
        limit=params.limit,
        force_download=params.force_download,
        force_parse=params.force_parse,
        verbose=True
    )

    # Stream output + capture results
    return stream_subprocess(cmd)

# lens/frontend/components/SyncAction.vue
# - Form with parameters
# - Live log viewer
# - Results table with failed tests
# - Auto-refresh report charts
```

---

## Database Schema

Anvil storage remains unchanged (already supports this):

```python
class ExecutionHistory:
    execution_id: str         # "ci-456789"
    entity_id: str            # "tests/test_*.py::test_func"
    entity_type: str          # "test"
    status: str               # "PASSED"/"FAILED"/"SKIPPED"
    duration: float
    space: str                # "ci" (from CI) or "local" (from machine)
    metadata: dict            # {
                              #   "run_id": 456789,
                              #   "job_name": "test (ubuntu-latest, 3.11)",
                              #   "platform": "ubuntu-latest",
                              #   "python_version": "3.11"
                              # }
```

---

## Proof of Concept

Let me create a working demo that:
1. Retrieves a real CI run from GitHub Actions
2. Parses the test results
3. Stores in Anvil database
4. Generates Lens report

### Step 1: Retrieve CI Run

```bash
# Using Scout (already works!)
cd scout
python -m scout.cli ci show --run-id 21589120797
```

### Step 2: Parse Test Results

We need to extract test results from the logs. GitHub Actions pytest typically outputs:
- Individual test results
- Summary statistics
- JUnit XML artifacts (if configured)

### Step 3: Store in Anvil

```python
# Same database, different space
execution_history = ExecutionHistory(
    execution_id="ci-21589120797-1",
    entity_id="forge/tests/test_argument_parser.py::test_basic",
    entity_type="test",
    status="PASSED",
    duration=1.23,
    space="ci",  # ← Marks this as CI execution
    metadata={
        "run_id": 21589120797,
        "platform": "ubuntu-latest",
        "python_version": "3.11",
        "job_name": "test"
    }
)
```

### Step 4: Generate Reports

Lens can now query both:
```sql
-- Local tests
SELECT * FROM execution_history WHERE space='local'

-- CI tests
SELECT * FROM execution_history WHERE space='ci'

-- Comparison
SELECT
    entity_id,
    SUM(CASE WHEN space='local' AND status='PASSED' THEN 1 ELSE 0 END) as local_passed,
    SUM(CASE WHEN space='ci' AND status='PASSED' THEN 1 ELSE 0 END) as ci_passed
FROM execution_history
GROUP BY entity_id
```

---

## Implementation Priority

### Quick Win (1-2 hours)

Create a simple script that:
1. Takes a CI run ID
2. Downloads logs via Scout
3. Parses pytest output (regex-based)
4. Stores in Anvil database
5. Shows comparison report

### Full Implementation (Phase 0.3 + 0.4)

Follow the implementation plan:
- Scout enhancement for test parsing
- AnvilBridge for automated sync
- Lens CI health dashboard
- Platform comparison reports

---

## Example Workflow

```bash
# 1. Sync recent CI runs - downloads all logs and parses them
scout ci sync

# 1b. Sync only the last 10 workflow executions
scout ci sync --limit 10

# 2. Force re-download files (overwrites existing logs)
scout ci sync --force-download

# 2b. Force re-parsing of logs and database update
scout ci sync --force-parse

# 2c. Both force flags combined
scout ci sync --force-download --force-parse --limit 5

# 3. View CI statistics
cd ../anvil
anvil stats show --type test --space ci

# 4. Compare local vs CI
anvil stats compare --local-vs-ci

# 5. Generate integrated report
cd ../lens
lens report comparison --local-vs-ci --format html --output ci-comparison.html

# 6. View report
start ci-comparison.html
```

### Command Behavior Details

**`scout ci sync` (base command)**
- Downloads all CI logs from GitHub Actions workflow runs
- Stores logs in a configured folder (e.g., `.scout/ci-logs/`)
- For each log, parses using Anvil validators
- Stores parsed test execution data in Anvil database (`space="ci"`)

### Command Behavior Details

#### **`scout ci sync` (base command)**

**Flow**:
1. Query GitHub Actions for all workflow runs
2. For each workflow run:
   - Check if log file exists in `.scout/ci-logs/{workflow_id}/{job_id}.log`
   - If missing or `--force-download`: download and save
   - Check if execution data in Anvil DB
   - If missing or `--force-parse`: parse and store in DB
3. Summary report

**Verbose Mode Output Example**:
```
Scout CI Sync - Verbose Report
================================

Workflow: "Test Suite" (ID: 21589120797)
  Job: "test-ubuntu" (ID: 102)
    Status: Downloaded
    File: .scout/ci-logs/21589120797/102.log (847 lines)
    File size: 156 KB

  Job: "test-windows" (ID: 103)
    Status: Skipped (already downloaded)
    File: .scout/ci-logs/21589120797/103.log (1,203 lines)

Anvil Parsing Phase:
====================

Run 21589120797 - test-ubuntu:
  Parser: pytest_output_parser (auto-detected from job_name)
  Status: Parsed successfully
  Results stored: 47 tests
    - Passed: 45
    - Failed: 2
    - Skipped: 0
  Storage: Anvil DB (space="ci", run_id=21589120797, job_id=102)
  Metadata: {"platform": "ubuntu-latest", "python": "3.11"}

Run 21589120797 - test-windows:
  Parser: junit_xml_parser (auto-detected from artifacts)
  Status: Skipped (already in DB)
  Storage reference: Execution ID = ci-21589120797-103

Summary:
========
Downloaded: 1 job (847 lines)
Skipped download: 1 job
Parsed: 1 run
Skipped parse: 1 run
Total tests synced: 92
```

#### **Flag Details**

**`--limit N`**
- Only processes the last N workflow executions
- Useful for incremental syncs or testing
- Default: all available runs

**`--force-download`**
- Re-downloads all files even if they exist locally
- Overwrites existing log files
- Still respects `--limit`
- Useful when CI logs were partially downloaded or corrupted

**`--force-parse`**
- Re-parses log files and updates database
- Clears existing execution data for those runs
- Useful if parser logic changes or data needs recalculation
- Still respects `--limit`

**`-v, --verbose`**
- Shows detailed download/parse output (see example above)
- Shows file paths, line counts, parsed test results
- Useful for debugging and monitoring

#### **Typical Sync Flow**:

```
1. Get workflow runs (GitHub API, respecting --limit)
2. For each run:
   a. For each job in run:
      - Check if .scout/ci-logs/{run_id}/{job_id}.log exists
        * If yes & !--force-download: skip download (verbose: "Skipped")
        * If no | --force-download: download log (verbose: "Downloaded")

      - Check if run/job data in Anvil DB (WHERE run_id AND job_id)
        * If yes & !--force-parse: skip parsing (verbose: "Skipped")
        * If no | --force-parse: parse with auto-selected parser (verbose: "Parsed")

      - Store/update in Anvil DB with space="ci"
3. Print summary (total downloaded, parsed, skipped)
```

---


  ├─ ActionRunner (executes scout/anvil commands)
  ├─ OutputStreamer (real-time output to frontend)
  └─ IntegrationAPI (REST endpoints for actions)
```

### Lens Backend Components

**File**: `lens/backend/action_runner.py`

```python
class ActionRunner:
    """Execute scout/anvil actions and stream output."""

    def run_scout_sync(
        self,
        limit: Optional[int] = None,
        force_download: bool = False,
        force_parse: bool = False,
        verbose: bool = True
    ) -> Iterator[str]:
        """
        Execute 'scout ci sync' and yield output lines.

        Yields:
            Output lines from scout and anvil in real-time
        """
        cmd = ["python", "-m", "scout.cli", "ci", "sync"]
        if limit:
            cmd.extend(["--limit", str(limit)])
        if force_download:
            cmd.append("--force-download")
        if force_parse:
            cmd.append("--force-parse")
        if verbose:
            cmd.append("-v")

        # Stream output in real-time
        for line in run_subprocess_stream(cmd):
            yield line

    def run_anvil_parse(self, log_file: str) -> Iterator[str]:
        """Execute anvil parsing and stream results."""
        # Similar streaming implementation
        pass
```

**File**: `lens/backend/api/actions.py`

```python
# REST endpoints for Lens frontend
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/scout-sync")
async def websocket_scout_sync(
    websocket: WebSocket,
    limit: Optional[int] = None,
    force_download: bool = False,
    force_parse: bool = False
):
    """WebSocket endpoint for real-time scout sync output."""
    await websocket.accept()

    runner = ActionRunner()
    try:
        # Stream output to frontend
        for line in runner.run_scout_sync(
            limit=limit,
            force_download=force_download,
            force_parse=force_parse
        ):
            await websocket.send_text(line)
    finally:
        await websocket.close()

@app.post("/api/ci/sync")
async def trigger_ci_sync(
    limit: Optional[int] = None,
    force_download: bool = False,
    force_parse: bool = False
):
    """Trigger CI sync (returns job ID for tracking)."""
    job_id = create_background_job(
        "scout_ci_sync",
        limit=limit,
        force_download=force_download,
        force_parse=force_parse
    )
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/jobs/{job_id}/status")
async def get_job_status(job_id: str):
    """Get status of a running job."""
    return get_job_info(job_id)

@app.get("/api/jobs/{job_id}/output")
async def get_job_output(job_id: str):
    """Get output of a completed job."""
    return get_job_output_log(job_id)
```

### Lens Frontend Components

**File**: `lens/frontend/components/ActionPanel.vue` (or React equivalent)

```vue
<template>
  <div class="action-panel">
    <h2>CI Sync Actions</h2>

    <!-- Configuration Form -->
    <form @submit.prevent="startSync">
      <label>
        Limit to last N executions:
        <input v-model.number="config.limit" type="number" min="1">
      </label>

      <label>
        <input v-model="config.forceDownload" type="checkbox">
        Force re-download logs
      </label>

      <label>
        <input v-model="config.forceParse" type="checkbox">
        Force re-parse data
      </label>

      <label>
        <input v-model="config.verbose" type="checkbox">
        Verbose output
      </label>

      <button type="submit" :disabled="isRunning">
        {{ isRunning ? 'Running...' : 'Start CI Sync' }}
      </button>
    </form>

    <!-- Live Output -->
    <div v-if="isRunning || output.length > 0" class="output-panel">
      <h3>Output</h3>
      <div class="output-log">
        <div v-for="(line, i) in output" :key="i" class="log-line">
          {{ line }}
        </div>
      </div>
    </div>

    <!-- Results Summary -->
    <div v-if="summary" class="summary">
      <h3>Summary</h3>
      <p>Downloaded: {{ summary.downloaded }}</p>
      <p>Parsed: {{ summary.parsed }}</p>
      <p>Skipped: {{ summary.skipped }}</p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      config: {
        limit: null,
        forceDownload: false,
        forceParse: false,
        verbose: true
      },
      isRunning: false,
      output: [],
      summary: null,
      ws: null
    }
  },

  methods: {
    startSync() {
      this.isRunning = true;
      this.output = [];
      this.summary = null;

      // Open WebSocket for real-time updates
      this.ws = new WebSocket(
        `ws://localhost:8000/ws/scout-sync?` +
        `limit=${this.config.limit}&` +
        `force_download=${this.config.forceDownload}&` +
        `force_parse=${this.config.forceParse}`
      );

      this.ws.onmessage = (event) => {
        this.output.push(event.data);
        // Auto-scroll to bottom
        this.$nextTick(() => {
          const log = this.$el.querySelector('.output-log');
          log.scrollTop = log.scrollHeight;
        });
      };

      this.ws.onclose = () => {
        this.isRunning = false;
        this.parseSummary();
      };
    },

    parseSummary() {
      // Parse last few lines to extract summary
      const summaryLine = this.output
        .reverse()
        .find(line => line.includes("Summary:"));

      if (summaryLine) {
        // Extract counts from summary
        // ...
      }
    }
  }
}
</script>
```

### Lens Dashboard View

Add new tab: **CI Dashboard**

```
┌─────────────────────────────────────────┐
│        Lens CI Dashboard                │
├─────────────────────────────────────────┤
│ [Actions Panel]  [Statistics]  [Trends] │
├─────────────────────────────────────────┤
│                                         │
│  Recent CI Runs:                        │
│  ┌─────────────────────────────────────┐│
│  │ Run #21589120797 (2 hours ago)      ││
│  │ Platform: ubuntu-latest             ││
│  │ Status: ✓ 92 tests passed           ││
│  │ Jobs: test-ubuntu, test-windows     ││
│  └─────────────────────────────────────┘│
│                                         │
│  Sync Status:                           │
│  ┌─────────────────────────────────────┐│
│  │ [Start Sync] or [Run with Options]  ││
│  │ Last sync: 2 hours ago              ││
│  │ Pending: 3 runs (--limit 10)        ││
│  └─────────────────────────────────────┘│
│                                         │
│  CI vs Local Comparison:                │
│  ┌─────────────────────────────────────┐│
│  │ Passing:  Local: 150 | CI: 92       ││
│  │ Failing:  Local: 2   | CI: 0        ││
│  │ Skipped:  Local: 5   | CI: 3        ││
│  └─────────────────────────────────────┘│
└─────────────────────────────────────────┘
```

---

## Implementation Timeline

### Phase 0.5: Scout Enhancement
- [ ] Enhance `scout ci sync` with all flags and verbose mode
- [ ] Implement parser selector mechanism
- [ ] Create job-parser-mapping.yaml configuration
- [ ] Test with real GitHub Actions runs

### Phase 0.6: Lens Backend
- [ ] Create ActionRunner component
- [ ] Implement WebSocket endpoints
- [ ] Add background job tracking
- [ ] Integrate with Anvil database

### Phase 0.7: Lens Frontend
- [ ] Create ActionPanel component
- [ ] Build CI Dashboard view
- [ ] Add real-time output streaming
- [ ] Implement summary parsing

### Phase 0.8: Testing & Polish
- [ ] End-to-end testing (Scout → Anvil → Lens)
- [ ] Error handling and recovery
- [ ] Documentation and examples
- [ ] Performance optimization

---

## Expected Output

### Console Report
```
CI vs Local Test Comparison
==========================================================================================

Total Tests: 739
Local Executions: 1,875
CI Executions: 245 (last 10 runs)

Platform-Specific Failures:
  Windows-only failures: 3 tests
  - test_symlink_collection (expected - Windows symlink limitation)
  - test_file_permissions
  - test_path_handling

  Linux-only failures: 0 tests

Local-only failures: 2 tests
  - test_database_lock (likely timing issue)
  - test_concurrent_access

CI-only failures: 5 tests
  - test_network_dependency (CI network isolation)
  - test_timeout_threshold (CI resource constraints)
```

### HTML Report Features
- Side-by-side success rate comparison
- Platform breakdown heatmap
- Failure pattern identification
- Reproduction commands for CI-specific failures

---

## Benefits

1. **Platform-Specific Issue Detection**: See which tests fail only on CI (or only locally)
2. **Complete Visibility**: Track all test executions (local + CI) in one place
3. **Root Cause Analysis**: Identify environmental differences
4. **Reproducibility**: CI failures can be reproduced locally with environment info
5. **Trend Analysis**: CI health over time

---

## Next Steps

Would you like me to:

**Option A: Quick Demo**
- Create script to parse one CI run
- Store in Anvil database
- Show basic comparison

**Option B: Full Implementation**
- Implement Scout test result parser
- Create AnvilBridge for automated sync
- Extend Lens with CI reports
- Add platform comparison features

**Option C: Minimal Viable Product**
- Parse pytest output from CI logs
- Store as `space="ci"`
- Extend existing Lens report to filter by space
- Add simple local/CI comparison table

Let me know which approach you'd like, and I'll implement it!
