# Scout Architecture - Four-Stage Pipeline

Scout implements a **modular four-stage pipeline** for CI/CD data processing:

```
┌─────────────┐    ┌──────────────┐    ┌────────┐    ┌─────────────────┐
│             │    │              │    │        │    │                 │
│   FETCH     ├───→│   SAVE-CI    ├───→│ PARSE  ├───→│ SAVE-ANALYSIS   │
│             │    │              │    │        │    │                 │
│ GitHub API  │    │  Execution   │    │ Anvil  │    │  Analysis DB    │
│             │    │  Database    │    │Parsers │    │                 │
└─────────────┘    └──────────────┘    └────────┘    └─────────────────┘
```

Each stage is **independent**, **reusable**, and can be **skipped**.

---

## Architecture Principles

### 1. Case Identification (Triple)

Every data item is identified by a consistent **triple**:

```python
case = (workflow_name, execution_id, job_id)

# execution_id = run_id (GitHub) ↔ execution_number (internal)
# job_id = job_id (GitHub) ↔ action_name (user-friendly)
```

**Scout manages bidirectional mappings:**
- When user provides `run_id`, Scout stores and recovers `execution_number`
- When user provides `action_name`, Scout stores and recovers `job_id`
- All queries work with any combination of identifiers

### 2. Stage Independence

Each stage operates independently:

- **Fetch** - No dependencies, downloads from GitHub
- **Save-CI** - Depends only on fetch, stores raw content
- **Parse** - Can use either fetched or cached content
- **Save-Analysis** - Depends only on parse, stores structured results

This allows patterns like:

```bash
# Fetch today, parse tomorrow
scout fetch --workflow-name X --run-id 123 --save
# ... (later) ...
scout parse --workflow-name X --run-id 123 --save

# Parse without storing raw logs
scout sync --workflow-name X --run-id 123 --skip-save-ci

# Skip parsing, just fetch and store
scout sync --workflow-name X --run-id 123 --skip-parse --skip-save-analysis
```

### 3. Database Design

**Execution Database** (`scout.db`):
- `ExecutionLog` table - Raw logs indexed by (workflow_name, run_id, job_id)
- `AnalysisResult` table - Parsed results indexed by same triple

Benefits:
- Single file deployment
- Atomic transactions
- Efficient querying by case triple
- Full-text search capability

### 4. Identifier Resolution

Scout handles identifier lookups transparently:

```python
# User provides execution_number
case = CaseIdentifier(
    workflow_name="CI Tests",
    execution_number=42  # ← Provided by user
)

# Scout queries GitHub API or local mapping
run_id = resolve_run_id(execution_number)  # → 1234567890

# Both are stored
execution_log.run_id = 1234567890
execution_log.execution_number = 42

# Query with either identifier works
```

---

## Command Handlers

### Fetch Command (`scout fetch`)

**Module:** `scout.cli.fetch_commands`

```python
handle_fetch_command(args)           # Single execution
handle_fetch_all_command(args)       # All executions
handle_fetch_last_command(args)      # Last N executions
```

Flow:
1. Validate case identifier (if provided)
2. Connect to GitHub API
3. Download logs
4. Save to file (optional: `--output`)
5. Save to database (optional: `--save`)

### Parse Command (`scout parse`)

**Module:** `scout.cli.parse_commands`

```python
handle_parse_from_file_command(args)  # Parse from file
handle_parse_from_db_command(args)    # Parse from cached logs
```

Flow:
1. Get input (file or database)
2. Detect log format
3. Call appropriate Anvil parser
4. Save to file (optional: `--output`)
5. Save to database (optional: `--save`)

### Sync Command (`scout sync`)

**Module:** `scout.cli.sync_commands`

```python
handle_sync_command(args)            # Router
handle_sync_with_case(args)          # Single execution
handle_sync_fetch_all(args)          # All executions
handle_sync_fetch_last(args)         # Last N executions
```

Flow:
1. Route to appropriate handler
2. Stage 1: Fetch (skip if `--skip-fetch`)
3. Stage 2: Save-CI (skip if `--skip-save-ci`)
4. Stage 3: Parse (skip if `--skip-parse`)
5. Stage 4: Save-Analysis (skip if `--skip-save-analysis`)

Error handling:
- If `--skip-fetch` but no cached data → Error (fail fast)
- If identifiers conflict → Error (show what conflicts)
- If execution_number and run_id both provided but don't match → Error

---

## Models

**Module:** `scout.models`

### CaseIdentifier

```python
@dataclass
class CaseIdentifier:
    workflow_name: str
    run_id: Optional[int] = None
    execution_number: Optional[int] = None
    job_id: Optional[str] = None
    action_name: Optional[str] = None

    # Properties
    @property
    def triple(self) -> Tuple[str, int, str]:
        """Get (workflow_name, run_id, job_id)"""

    def get_execution_id(self) -> int:
        """Resolve run_id (from execution_number if needed)"""

    def get_job_id(self) -> str:
        """Resolve job_id (from action_name if needed)"""
```

**Validation:**
- Requires `workflow_name`
- Requires at least one of: `run_id`, `execution_number`
- Requires at least one of: `job_id`, `action_name`
- Raises `ValueError` for invalid combinations

### Options Dataclasses

```python
@dataclass
class FetchOptions:
    output_file: Optional[str] = None
    save_execution: bool = False

@dataclass
class ParseOptions:
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    save_analysis: bool = False

@dataclass
class SyncOptions:
    skip_fetch: bool = False
    skip_save_ci: bool = False
    skip_parse: bool = False
    skip_save_analysis: bool = False
    fetch_all: bool = False
    fetch_last: Optional[int] = None
```

---

## Database Schema

**Module:** `scout.storage.schema`

### ExecutionLog

Raw logs downloaded from GitHub:

```python
class ExecutionLog(Base):
    workflow_name: str         # Indexed
    run_id: int                # Indexed (unique)
    execution_number: int      # Linked to run_id
    job_id: str                # Indexed
    action_name: str           # Linked to job_id
    raw_content: str           # Full log content
    content_type: str          # github_actions, pytest, etc.
    stored_at: datetime
    parsed: bool               # Flag for tracking
    metadata: JSON             # status, conclusion, branch, etc.

    Indexes:
    - (workflow_name, run_id, job_id)  ← Case triple
    - (workflow_name, stored_at)
    - (parsed)
```

### AnalysisResult

Parsed results from Anvil parsers:

```python
class AnalysisResult(Base):
    workflow_name: str         # Indexed
    run_id: int                # Indexed
    execution_number: int      # Linked to run_id
    job_id: str                # Indexed
    action_name: str           # Linked to job_id
    analysis_type: str         # pytest, flake8, black, isort, etc.
    parsed_data: JSON          # Validator format from Anvil
    parsed_at: datetime
    metadata: JSON             # duration, tool_version, etc.

    Indexes:
    - (workflow_name, run_id, job_id)  ← Case triple
    - (analysis_type)
    - (workflow_name, parsed_at)
```

---

## Argument Parser

**Module:** `scout.new_parser`

```python
def create_new_parser() -> argparse.ArgumentParser:
    """Creates parser with three main commands."""
```

### fetch

```
scout fetch --workflow-name X --run-id Y --job-id Z [--output FILE] [--save]
scout fetch --fetch-all --workflow-name X [--output DIR] [--save]
scout fetch --fetch-last N [--workflow-name X] [--output DIR] [--save]
```

Case identifier (optional if using --fetch-all or --fetch-last):
- `--workflow-name` - Required (except with --fetch-all)
- `--run-id` or `--execution-number` - Optional (at least one for single fetch)
- `--job-id` or `--action-name` - Optional (at least one for single fetch)

Output options (mutually exclusive):
- `--output FILE` - Save to file
- `--save` - Save to execution database

### parse

```
scout parse --input FILE [--output OUT] [--save]
scout parse --workflow-name X --run-id Y --job-id Z [--output OUT] [--save]
```

Input (mutually exclusive):
- `--input FILE` - Parse raw file
- `--workflow-name` - Parse from database (requires case identifier)

Output (mutually exclusive):
- `--output FILE` - Save to file
- `--save` - Save to analysis database

### sync

```
scout sync --workflow-name X --run-id Y --job-id Z [--skip-STAGE] [...]
scout sync --fetch-all --workflow-name X [--skip-STAGE] [...]
scout sync --fetch-last N [--workflow-name X] [--skip-STAGE] [...]
```

Skip options:
- `--skip-fetch` - Use cached data (error if not found)
- `--skip-save-ci` - Don't store raw logs
- `--skip-parse` - Don't parse
- `--skip-save-analysis` - Don't store parsed results

---

## Data Flow Examples

### Example 1: Complete Pipeline

```
User: scout sync --workflow-name "CI" --run-id 123 --job-id abc

Flow:
1. Fetch logs from GitHub
   → ExecutionLog(workflow="CI", run_id=123, job_id="abc", raw_content="...")

2. Save execution log
   → stored_at = now, parsed = false

3. Parse using Anvil
   → parsed_result = {"tests": {...}, "lint": {...}}

4. Save analysis result
   → AnalysisResult(workflow="CI", run_id=123, job_id="abc",
                    analysis_type="pytest", parsed_data={...})
```

### Example 2: Skip Parsing

```
User: scout sync --workflow-name "CI" --run-id 123 --job-id abc --skip-parse

Flow:
1. Fetch logs
2. Save execution log
3. Skip parsing
4. Skip analysis save

Result: Logs cached, ready for later parsing
```

### Example 3: Parse Previously Cached

```
User: scout parse --workflow-name "CI" --run-id 123 --job-id abc --save

Flow:
1. Retrieve ExecutionLog (from database)
2. Parse using Anvil
3. Save AnalysisResult

Result: Only parsing + save, no fetch
```

### Example 4: Batch Process Recent Runs

```
User: scout sync --fetch-last 5 --workflow-name "CI Tests"

Flow:
For each of last 5 runs (oldest-first):
  1. Fetch
  2. Save
  3. Parse
  4. Save analysis
```

---

## Integration with Anvil

Scout integrates with **Anvil's parsing layer** to convert raw logs to structured format:

```
ExecutionLog.raw_content
    ↓
[Anvil Parser]  ← Detects type: pytest, flake8, black, isort, pylint, coverage
    ↓
AnalysisResult.parsed_data (JSON)
    ↓
[Anvil Validator Format]  ← Compatible with Verdict
```

---

## Error Handling Strategy

### Fail-Fast Validation

Before any operation, validate inputs:

```python
# In CaseIdentifier.__post_init__
- workflow_name must not be empty
- Must have execution_id (run_id OR execution_number)
- Must have job_id (job_id OR action_name)
```

### Conflicting Identifiers

Error on conflicts (no guessing):

```bash
scout fetch \
  --run-id 123456789 \
  --execution-number 999  # ✗ Error: Conflicting execution IDs
```

### Missing Data

Error if required data not found:

```bash
scout sync --skip-fetch --workflow-name X --run-id 123  # ✗ Error: No cached data
```

### Ambiguous Scenarios

Require explicit specification:

```bash
scout fetch --workflow-name X  # ✗ Error: Need execution ID (run-id or execution-number)
```

---

## Testing Strategy

### Unit Tests

- `CaseIdentifier` validation
- Options dataclass creation
- Argument parser routing

### Integration Tests

- Command handlers with mock databases
- Pipeline stage interactions
- Skip option combinations

### E2E Tests

- Actual GitHub API calls (with test repo)
- Database roundtrips
- Anvil parser integration

---

## Future Extensibility

### New Commands

Adding new commands requires:
1. Create command module in `scout.cli.*_commands.py`
2. Create option dataclass in `scout.models`
3. Add parser in `scout.new_parser`
4. Add handler dispatch in CLI

### New Parsers

To support additional tools:
1. Extend Anvil with new parser
2. Add analysis_type to AnalysisResult
3. Update parse command dispatch

### New Output Formats

Current: JSON (stdout/file), Database
Future: HTML, CSV, Database query output, etc.
