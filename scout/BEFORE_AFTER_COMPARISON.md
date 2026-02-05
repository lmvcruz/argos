# Scout CLI - Before & After Comparison

## Parameter Standardization

### BEFORE (Old Architecture)
```
scout fetch --workflow "Tests" --last 5 --output data.json --branch main
scout parse --input data.json --output results.json --db scout.db
scout ci fetch --run-id 12345 --job-id abc
scout ci parse --run-id 12345
scout ci sync ...
```

**Problems:**
- Different parameter names: `--workflow` vs `--workflow-name`
- Inconsistent: `--last` (fetch) vs no equivalent in parse
- No distinction between run-id and execution-number
- No distinction between job-id and action-name
- Top-level commands mixed with `ci` subcommands
- No unified sync pipeline

### AFTER (New Architecture)
```
scout fetch --workflow-name "Tests" --run-id 12345 --job-id abc --output logs.txt --save-ci
scout parse --input logs.txt --output results.json --save-analysis
scout parse --workflow-name "Tests" --run-id 12345 --job-id abc --save-analysis
scout sync --fetch-last 5 --workflow-name "Tests"
scout sync --fetch-last 5 --skip-parse
```

**Improvements:**
✅ Consistent parameter names across all commands
✅ Supports both numeric IDs and human-readable numbers
✅ Unified case identification model
✅ Top-level commands for common workflows
✅ Flexible skip flags for conditional execution
✅ Clear database options (--save-ci, --save-analysis)

---

## Command Structure Comparison

### Fetch Command

#### OLD
```bash
scout fetch --workflow "Tests" --last 5 --output file.json [--branch main]
```

**Limitations:**
- Always outputs to file (JSON)
- No option to display results
- No option to save to database
- Single workflow (no case filtering)
- No job-level selection

#### NEW
```bash
# Display only
scout fetch --workflow-name "Tests" --run-id 12345 --job-id abc

# Save to file
scout fetch --workflow-name "Tests" --run-id 12345 --job-id abc --output logs.txt

# Save to database
scout fetch --workflow-name "Tests" --run-id 12345 --job-id abc --save-ci

# Multiple options
scout fetch --workflow-name "Tests" --run-id 12345 --job-id abc --output logs.txt --save-ci

# Alternative identifiers
scout fetch --workflow-name "Tests" --execution-number "21" --action-name "code quality"
```

**Improvements:**
✅ Flexible output options (stdout, file, database)
✅ Case-level selection (run + job)
✅ Alternative identifiers supported
✅ Clearer parameter naming

---

### Parse Command

#### OLD
```bash
scout parse --input file.json --output results.json [--db scout.db]
```

**Limitations:**
- Only accepts file input
- No option to query from database
- No option to save to database
- Always outputs to file or stdout

#### NEW
```bash
# From file to stdout
scout parse --input logs.txt

# From file to file
scout parse --input logs.txt --output results.json

# From file to database
scout parse --input logs.txt --save-analysis

# From database to stdout
scout parse --workflow-name "Tests" --run-id 12345 --job-id abc

# From database to database
scout parse --workflow-name "Tests" --run-id 12345 --job-id abc --save-analysis

# From database to file
scout parse --workflow-name "Tests" --run-id 12345 --job-id abc --output results.json
```

**Improvements:**
✅ Dual input sources (file or database)
✅ Flexible output options
✅ Case-specific selection
✅ Easier batch processing

---

### Sync Command

#### OLD
```bash
scout ci sync [--run-id <ID>]
```

**Limitations:**
- Single run only
- No batch capabilities
- No skip options
- No control over pipeline stages
- Unclear what "sync" does

#### NEW
```bash
# Fetch all and sync
scout sync --fetch-all

# Fetch last N and sync
scout sync --fetch-last 5
scout sync --fetch-last 10 --workflow-name "Tests"

# Specific case
scout sync --workflow-name "Tests" --run-id 12345 --job-id abc

# With skip flags (conditional)
scout sync --fetch-last 5 --skip-fetch               # Use cached data
scout sync --fetch-last 5 --skip-save-ci             # Fetch only, no save
scout sync --fetch-last 5 --skip-parse               # Fetch/save only
scout sync --fetch-last 5 --skip-save-analysis       # Don't save results

# Complex: Re-analyze without fetching
scout sync --workflow-name "Tests" --run-id 12345 --skip-fetch --skip-save-ci
```

**Improvements:**
✅ Batch processing support (--fetch-all, --fetch-last)
✅ Conditional execution (skip flags)
✅ Clear 4-stage pipeline
✅ Flexible workflow control
✅ Single command for common workflows

---

## Case Identification Evolution

### OLD
```
Case = (workflow, run_id, job_id)

# Only numeric IDs
scout fetch --workflow "Tests" --last 5
scout ci show --run-id 12345
scout ci parse --job-id abc123
```

**Limitations:**
- Only numeric IDs
- No human-readable alternatives
- Unclear mapping between ID types

### NEW
```
Case = (workflow_name, {run_id | execution_number}, {job_id | action_name})

# Numeric identifiers
scout sync --workflow-name "Tests" --run-id 12345 --job-id abc123

# Human-readable alternatives
scout sync --workflow-name "Tests" --execution-number "21" --action-name "code quality"

# Mixed (Scout auto-maps both)
scout sync --workflow-name "Tests" --run-id 12345 --action-name "code quality"

# Scout stores and retrieves both representations
```

**Improvements:**
✅ Dual identifiers (numeric + human-readable)
✅ Flexible querying
✅ Automatic mapping
✅ Better UX for different teams

---

## Database Organization

### OLD
```
Single scout.db
  - WorkflowRun (workflow, run_id, status, logs, etc.)
  - No separate analysis database
  - No clear separation of concerns
```

### NEW
```
Two Databases (Clear Separation)

scout.db (Execution Database)
  ├─ execution_logs
  │  ├─ workflow_name
  │  ├─ run_id / execution_number (paired)
  │  ├─ job_id / action_name (paired)
  │  ├─ raw_log_text
  │  └─ fetch_timestamp
  └─ [other execution data]

scout-analysis.db (Analysis Database)
  ├─ analysis_results
  │  ├─ workflow_name
  │  ├─ run_id / execution_number (paired)
  │  ├─ job_id / action_name (paired)
  │  ├─ parsed_json
  │  └─ analysis_timestamp
  └─ [other analysis data]
```

**Improvements:**
✅ Clear separation between raw and parsed data
✅ Independent scaling of databases
✅ Better data integrity
✅ Easier maintenance and backup

---

## Pipeline Visibility

### OLD
```
scout ci sync --run-id 12345
[implicit pipeline, unclear what happens]
```

### NEW
```
scout sync --fetch-last 5

Starting sync pipeline...
  [1/4] Fetch: Downloading logs from GitHub...
  [2/4] Save-CI: Storing raw logs...
  [3/4] Parse: Transforming via Anvil...
  [4/4] Save-Analysis: Storing results...
[OK] Sync pipeline completed
```

**Improvements:**
✅ Clear 4-stage pipeline
✅ Progress visibility
✅ Error attribution to specific stage
✅ Understanding of what's happening

---

## Error Handling

### OLD
```bash
scout fetch --workflow "Unknown"
[Silent failure or unclear error]

scout parse --input missing.json
[File not found error - unclear what to do]
```

### NEW
```bash
scout fetch --workflow-name "Unknown"
Error: Workflow "Unknown" not found in available workflows

scout parse --input missing.json
Error: Input file not found: missing.json

scout sync --workflow-name "Tests" --run-id 12345 --skip-fetch
Error: Case not found in execution database. Run fetch first or remove --skip-fetch
```

**Improvements:**
✅ Clear, actionable error messages
✅ Suggestions for fixes
✅ No silent failures
✅ Better debugging experience

---

## Migration Path

### Phase 1: Coexistence (NOW)
- Old commands still work (with deprecation warning)
- New commands available alongside old ones
- Documentation guides toward new syntax

### Phase 2: Deprecation (Future)
- Old commands show warning on every use
- Documentation emphasizes new commands
- Support period for migration

### Phase 3: Removal (Future)
- Old commands disabled
- Clean codebase
- Full migration to new architecture

---

## Feature Comparison Matrix

| Feature | OLD | NEW |
|---------|-----|-----|
| Parameter consistency | ❌ | ✅ |
| Dual identifiers | ❌ | ✅ |
| Flexible I/O | ✅ (limited) | ✅ (full) |
| Batch processing | ❌ | ✅ |
| Skip flags | ❌ | ✅ |
| 4-stage pipeline | ✅ (hidden) | ✅ (visible) |
| Error messages | 🟡 | ✅ |
| Database separation | ❌ | ✅ |
| Pipeline visibility | ❌ | ✅ |
| Job-level control | 🟡 | ✅ |
| Help text | 🟡 | ✅ |

---

## Typical Use Cases

### Quick Sync (5 executions)

**OLD:**
```bash
scout ci fetch --limit 5
scout ci sync
```

**NEW:**
```bash
scout sync --fetch-last 5
```

### Detailed Analysis (File-Based)

**OLD:**
```bash
scout fetch --workflow "Tests" --last 1 --output logs.json
scout parse --input logs.json --output results.json
cat results.json
```

**NEW:**
```bash
scout fetch --workflow-name "Tests" --run-id 12345 --output logs.txt
scout parse --input logs.txt --output results.json
cat results.json
```

### Batch Analysis

**OLD:**
```bash
# Loop required
for run_id in $(scout ci list --limit 20); do
  scout ci sync --run-id $run_id
done
```

**NEW:**
```bash
# Single command
scout sync --fetch-last 20
```

### Conditional Processing

**OLD:**
```bash
# No direct support
scout ci fetch --limit 5
# [manual decision]
scout ci parse  # if fetch succeeded
```

**NEW:**
```bash
# Skip flags support conditional flows
scout sync --fetch-last 5 --skip-parse       # Just fetch
scout sync --fetch-last 5 --skip-save-ci     # Fetch but don't store raw
scout sync --fetch-last 5 --skip-fetch       # Use cached data
```

---

## Summary: Why the New Architecture?

| Aspect | Issue | Solution |
|--------|-------|----------|
| **Parameters** | Inconsistent naming | Standardized across all commands |
| **Identifiers** | Only numeric | Support both numeric and human-readable |
| **Flexibility** | Limited I/O options | File, database, or stdout - your choice |
| **Batch Processing** | Manual looping | Built-in support with `--fetch-all`, `--fetch-last` |
| **Pipeline Control** | Implicit stages | Explicit skip flags for fine control |
| **Error Visibility** | Unclear failures | Clear, actionable error messages |
| **Organization** | Mixed concerns | Separated execution and analysis DBs |
| **Usability** | Complex workflows | Simple commands for common tasks |

---

## Backwards Compatibility

All old commands still work:
- `scout fetch --workflow X --last N` - Still supported
- `scout parse --input FILE` - Still supported
- `scout ci sync` - Still supported

**Deprecation notices** will guide users toward new syntax, but there's no breaking change.

---

Generated: February 5, 2026
Scout Version: 0.1.0 → 0.2.0 (with new architecture)
