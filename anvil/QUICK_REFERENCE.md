# Custom Verdict Runner - Quick Reference

## Installation

```bash
cd anvil
python scripts/setup-git-hooks.py  # Install pre-commit hook
python -m pytest tests/test_verdict_runner.py  # Verify installation
```

## Basic Usage

### List All Validators
```bash
python scripts/verdict.py --list
```

### List Test Cases for a Validator
```bash
python scripts/verdict.py --list black
python scripts/verdict.py --list flake8
python scripts/verdict.py --list isort
```

### Run All Test Cases
```bash
python scripts/verdict.py black
python scripts/verdict.py flake8
python scripts/verdict.py isort
```

### Run Specific Test Case
```bash
# Single case
python scripts/verdict.py black --cases scout_ci.job_180

# Multiple cases by partial path
python scripts/verdict.py black --cases scout_ci
```

## Example Output

### List Validators
```
Available validators:
============================================================
  black
  flake8
  isort
```

### List Cases
```
black cases:
============================================================
  scout_ci.job_180
  scout_ci.job_201
  scout_ci.job_302
  scout_ci.job_701
  scout_ci.job_829
  scout_ci.job_client
  empty_output
  long_paths
  ... (11 more)
```

### Execute Cases
```
======================================================================
BLACK
======================================================================
  [PASS] scout_ci.job_180
  [PASS] scout_ci.job_201
  [PASS] scout_ci.job_302
  [PASS] scout_ci.job_701
  [PASS] scout_ci.job_829
  [PASS] scout_ci.job_client

Total: 6 | Passed: 6 | Failed: 0
```

## Configuration

**File:** `tests/validation/config.yaml`

```yaml
validators:
  validator_name:
    callable: module.path.to.adapter_function
    root: path/to/test/cases
```

## Adding New Test Cases

### Folder-Based Case
```
cases/black_cases/new_case/
├── input.txt          # Raw validator input
└── expected_output.yaml  # Expected JSON structure
```

Case name: `new_case`

### YAML-Based Case
**File:** `cases/black_cases/new_case.yaml`

```yaml
name: "Description"
description: "What this tests"

input:
  type: "text"
  content: "..."

expected:
  validator: "black"
  total_violations: 0
  files_scanned: 0
  ...
```

Case name: `new_case`

## Testing

```bash
# Run all tests
python -m pytest tests/test_verdict_runner.py -v

# Run specific test class
python -m pytest tests/test_verdict_runner.py::TestCaseDiscovery -v

# Run with coverage
python -m pytest tests/test_verdict_runner.py --cov=anvil.testing.verdict_runner
```

## Pre-Commit Checks

```bash
# Run all checks (syntax, formatting, imports, tests)
python scripts/pre-commit-check.py

# Format code with black
python -m black anvil/testing/ tests/test_verdict_runner.py

# Check imports with isort
python -m isort anvil/testing/ tests/test_verdict_runner.py
```

## Common Issues

**Q: Case not discovered?**
A: Check folder has `input.txt` and/or `expected_output.yaml`. For YAML files, must be in root with `.yaml` extension.

**Q: Encoding error on Windows?**
A: Already fixed! Files opened with UTF-8 encoding.

**Q: Config file not found?**
A: Run from anvil directory: `cd anvil && python scripts/verdict.py --list`

**Q: Adapter import fails?**
A: Verify callable path is correct, e.g., `anvil.validators.adapters.validate_black_parser`

## Files

- **Core:** `anvil/testing/verdict_runner.py` (547 lines)
- **Tests:** `tests/test_verdict_runner.py` (299 lines, 21 tests)
- **Config:** `tests/validation/config.yaml`
- **CLI:** `scripts/verdict.py`
- **Docs:** `VERDICT_RUNNER_GUIDE.md`, `IMPLEMENTATION_SUMMARY.md`

## Status

✅ All 21 tests passing
✅ All pre-commit checks passing
✅ Production ready
