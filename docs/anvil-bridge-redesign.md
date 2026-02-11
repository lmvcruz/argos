# AnvilBridge Architecture Redesign

## Summary

AnvilBridge has been redesigned from a **database sync tool** to a **parser adapter**. It no longer writes to Anvil's database. Instead, it provides Scout with access to Anvil's specialized validator parsers, while keeping data separation intact.

## Architecture Principles

### Database Separation

- **Anvil DB (`~/.anvil/*/anvil_stats.db`)**: LOCAL executions ONLY
  - Local test runs via `anvil run`
  - Local validator results
  - Project-specific validation history

- **Scout DB (`~/.scout/*/scout.db`)**: CI executions ONLY
  - GitHub Actions workflow runs
  - CI job logs
  - CI validator results
  - CI test results

**No data flows from Scout DB → Anvil DB**

## AnvilBridge Role

### Old (WRONG):
```
Scout DB → AnvilBridge → Anvil DB ❌
```
**Problem**: Mixed local and CI data in Anvil DB

### New (CORRECT):
```
GitHub → Scout (fetch) → Scout DB (metadata + logs)
                ↓
         AnvilLogExtractor (extract validator output)
                ↓
         AnvilBridge (parse using Anvil parsers)
                ↓
         Scout DB (save parsed results)
```

**AnvilBridge is a stateless parser adapter**:
- ✅ Uses Anvil's specialized parsers (black, flake8, pylint, pytest, etc.)
- ✅ Returns parsed `ValidationResult` dictionaries
- ✅ NO database connections
- ✅ NO writes to Anvil DB
- ✅ Scout saves results to Scout DB

## Implementation

### AnvilBridge API

```python
from scout.integration.anvil_bridge import AnvilBridge

# Create parser adapter (no DB connections)
bridge = AnvilBridge()

# Get supported validators
validators = bridge.get_supported_validators()
# ['black', 'flake8', 'isort', 'pylint', 'pytest', 'autoflake', ...]

# Parse validator output
result = bridge.parse_validator_output(
    validator_name="black",
    output=black_output_string,
    files=[Path("scout/cli.py")],
    output_format="text"
)

# Returns dictionary:
# {
#     "validator_name": "black",
#     "passed": False,
#     "errors": [...],  # List of Issue dicts
#     "warnings": [...],
#     "execution_time": 1.23,
#     "files_checked": 5
# }

# Scout saves result to Scout DB
```

### AnvilLogExtractor API

```python
from scout.integration.anvil_bridge import AnvilLogExtractor

# Full CI log from GitHub Actions
ci_log = job.log_content

# Detect which validators ran
validators = AnvilLogExtractor.detect_validators_in_log(ci_log)
# ['black', 'flake8', 'pytest']

# Extract validator-specific output
black_output = AnvilLogExtractor.extract_validator_output(ci_log, "black")
flake8_output = AnvilLogExtractor.extract_validator_output(ci_log, "flake8")

# Parse each with AnvilBridge
bridge = AnvilBridge()
black_result = bridge.parse_ci_log_section("black", black_output)
flake8_result = bridge.parse_ci_log_section("flake8", flake8_output)

# Scout saves to Scout DB
```

## Supported Validators

AnvilBridge provides parsing for:

**Python:**
- black (formatter)
- flake8 (linter)
- isort (import sorter)
- pylint (linter)
- pytest (test runner)
- autoflake (unused import remover)
- vulture (dead code detector)
- radon (complexity metrics)
- coverage (coverage analyzer)

**C/C++:**
- clang-tidy (linter)
- clang-format (formatter)
- cpplint (linter)
- cppcheck (static analyzer)
- gtest (test runner)

## Workflow Example

### Scout Parse Command

```bash
# 1. Fetch CI data from GitHub
scout fetch --repo owner/repo --workflow test.yml --limit 5

# 2. Parse logs and extract validator results
scout parse --repo owner/repo <run_id>
```

**What happens internally:**

```python
# In scout parse command handler:

# 1. Load CI log from Scout DB
workflow_job = get_workflow_job(run_id, job_id)
ci_log = workflow_job.log_content

# 2. Detect and extract validator outputs
extractor = AnvilLogExtractor()
validators = extractor.detect_validators_in_log(ci_log)

# 3. Parse each validator output
bridge = AnvilBridge()
for validator_name in validators:
    output = extractor.extract_validator_output(ci_log, validator_name)
    result = bridge.parse_ci_log_section(validator_name, output)

    # 4. Save to Scout DB (NOT Anvil DB)
    save_validator_result_to_scout_db(run_id, job_id, result)

print("✓ Parsed validator results saved to Scout DB")
print("✗ NO data written to Anvil DB")
```

## Migration Notes

### Deprecated Features

- ❌ `scout sync` command (removed - used to sync to Anvil DB)
- ❌ `AnvilBridge.sync_ci_run_to_anvil()` (removed)
- ❌ `AnvilBridge.sync_recent_runs()` (removed)
- ❌ `AnvilBridge.compare_local_vs_ci()` (removed)
- ❌ `AnvilBridge.identify_ci_specific_failures()` (removed)

### New Features

- ✅ `AnvilBridge.parse_validator_output()` (parser adapter)
- ✅ `AnvilBridge.parse_ci_log_section()` (convenience method)
- ✅ `AnvilBridge.get_supported_validators()` (list parsers)
- ✅ `AnvilLogExtractor.extract_validator_output()` (log extraction)
- ✅ `AnvilLogExtractor.detect_validators_in_log()` (auto-detection)

### Database Schema Changes

**Scout DB remains unchanged** - already designed to store CI data

**Anvil DB remains unchanged** - only stores local execution data

**No migration required** - databases are now properly separated

## Examples

See [examples/anvil_bridge_usage.py](../examples/anvil_bridge_usage.py) for complete usage examples.

## Benefits

1. **Clear Separation**: Anvil DB = local, Scout DB = CI
2. **No Data Mixing**: Each database serves one purpose
3. **Reusable Parsers**: Scout leverages Anvil's parser expertise
4. **No Duplication**: Single source of truth for validator parsing
5. **Stateless**: AnvilBridge has no side effects, easy to test
6. **Extensible**: New validators added to Anvil automatically available in Scout

## Next Steps

1. ✅ AnvilBridge redesigned as parser adapter
2. ⏳ Update `scout parse` command to use AnvilBridge
3. ⏳ Add validator result storage to Scout DB schema
4. ⏳ Update Lens to query Scout DB for CI validator results
5. ⏳ Remove deprecated `scout sync` command from CLI
