# Scout CLI - Quick Reference

## Installation Status

✅ Entry point enabled in `pyproject.toml`
🟡 Installation on Windows pending (file permission issue)
✅ Works with `python scout/cli.py` or `python -m scout`

---

## Three Main Commands

### scout fetch
Download CI logs from GitHub

```bash
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc"
scout fetch --workflow-name "Tests" --run-id 12345 --output logs.txt
scout fetch --workflow-name "Tests" --run-id 12345 --save-ci
```

### scout parse
Transform logs via Anvil

```bash
scout parse --input logs.txt
scout parse --input logs.txt --output results.json
scout parse --workflow-name "Tests" --run-id 12345 --job-id "abc"
scout parse --workflow-name "Tests" --run-id 12345 --save-analysis
```

### scout sync (NEW!)
Run complete pipeline

```bash
scout sync --fetch-last 5 --workflow-name "Tests"
scout sync --fetch-all
scout sync --workflow-name "Tests" --run-id 12345
scout sync --fetch-last 5 --skip-parse
```

---

## Parameters Cheat Sheet

### Always Available
- `--workflow-name <NAME>` - Workflow name (required for most commands)
- `--verbose` or `-v` - Show details
- `--quiet` or `-q` - Suppress output

### Case Identifiers (Pick One)
- `--run-id <NUM>` - GitHub run ID (e.g., 12345)
- `--execution-number <NUM>` - Execution number (e.g., "21")

### Job Identifier (Optional)
- `--job-id <ID>` - GitHub job ID (e.g., "abc123")
- `--action-name <NAME>` - Action name (e.g., "code quality")

### Output Options
- `--output <FILE>` - Save to file
- `--save-ci` - Save to execution database
- `--save-analysis` - Save to analysis database

### Sync-Specific
- `--fetch-all` - Fetch all executions
- `--fetch-last <N>` - Fetch last N executions
- `--filter-workflow <NAME>` - Filter by workflow
- `--skip-fetch` - Skip fetch stage
- `--skip-save-ci` - Don't save raw logs
- `--skip-parse` - Don't parse
- `--skip-save-analysis` - Don't save analysis

---

## Common Workflows

### One-Command Full Pipeline
```bash
scout sync --fetch-last 5 --workflow-name "Tests"
```

### Fetch Only
```bash
scout fetch --workflow-name "Tests" --run-id 12345 --job-id "abc"
```

### Parse Only (from file)
```bash
scout parse --input logs.txt --output results.json
```

### Parse Only (from database)
```bash
scout parse --workflow-name "Tests" --run-id 12345 --job-id "abc"
```

### Fetch and Save
```bash
scout fetch --workflow-name "Tests" --run-id 12345 --save-ci
```

### Process Existing Data
```bash
scout sync --workflow-name "Tests" --run-id 12345 --skip-fetch
```

### Dry Run (Fetch only, no saving)
```bash
scout sync --fetch-last 5 --skip-save-ci --skip-parse
```

---

## Documentation Files

| File | Purpose |
|------|---------|
| `SCOUT_ARCHITECTURE.md` | Complete architecture reference |
| `SCOUT_CLI_USER_GUIDE.md` | Detailed user guide with examples |
| `IMPLEMENTATION_SUMMARY.md` | What was implemented and why |
| `SCOUT_CLI_QUICK_REFERENCE.md` | This file |

---

## Help Commands

```bash
scout --help          # All commands
scout fetch --help    # fetch details
scout parse --help    # parse details
scout sync --help     # sync details
```

---

## Key Features

✅ **Standardized Parameters** - Consistent naming across all commands
✅ **Flexible I/O** - File, database, or stdout
✅ **Skip Flags** - Selective stage execution
✅ **Error Handling** - Clear, actionable error messages
✅ **Dual Identifiers** - Use numeric IDs or human-readable names
✅ **4-Stage Pipeline** - Fetch → Save → Parse → Save

---

## Implementation Status

| Component | Status | File |
|-----------|--------|------|
| Command Structure | ✅ Complete | `scout/cli.py` (lines 225-390) |
| Parameter Parsing | ✅ Complete | `scout/cli.py` (lines 225-390) |
| Handlers (v1) | 🟡 Placeholder | `scout/cli.py` (lines 830-1034) |
| Error Handling | ✅ Framework done | Needs business logic |
| GitHub Integration | ❌ TODO | Needed for fetch |
| Database Schema | ❌ TODO | Needed for save stages |
| Anvil Parser | ❌ TODO | Needed for parse |
| Tests | ❌ TODO | Need comprehensive tests |

---

## Next Steps

1. **Implement Fetch** - Connect to GitHub API
2. **Implement Parse** - Connect to Anvil parser
3. **Implement Databases** - Create schema and queries
4. **Add Tests** - Comprehensive test coverage
5. **Install Command** - Fix Windows permissions for `pip install -e .`

---

## Example: Complete Workflow

```bash
# 1. Fetch last 5 test runs and store
scout sync --fetch-last 5 --workflow-name "Tests"

# 2. Check a specific run
scout ci show --run-id 12345

# 3. Analyze trends
scout ci analyze --window 30

# 4. Fetch new data without parsing (dry-run)
scout sync --fetch-last 10 --skip-save-ci --skip-parse
```

---

## Troubleshooting

**"Error: Input file not found"**
→ File doesn't exist, check path

**"Error: Case not found in database"**
→ With `--skip-fetch`, data must already be saved

**"Unicode error on Windows"**
→ Use `python scout/cli.py` instead of `scout` command (pending fix)

**"GitHub token needed"**
→ Set `GITHUB_TOKEN` env var or use `--token <TOKEN>`

---

Generated: February 5, 2026
Scout Version: 0.1.0
Architecture Version: 2 (New!)
