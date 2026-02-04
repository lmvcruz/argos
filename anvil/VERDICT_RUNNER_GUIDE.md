# Custom Verdict Runner Guide

## Overview

The Custom Verdict Runner is a simplified, extensible test discovery and execution framework that automatically discovers test cases from folder and YAML file structures, and executes them against configured validator adapters.

**Key Features:**
- ✅ Auto-discovery of test cases from filesystem (no manual configuration)
- ✅ Simplified YAML config format (just `validators: {name: {callable, root}}`)
- ✅ Clean CLI interface: `verdict --list`, `verdict black`, `verdict black --cases scout_ci.job_180`
- ✅ Hierarchical case filtering with dot notation (e.g., `scout_ci.job_180`)
- ✅ Support for both folder-based and YAML file-based test cases
- ✅ UTF-8 encoding support for cross-platform compatibility

## Installation & Setup

### 1. Install Pre-Commit Hook (Required)
```bash
cd forge
python scripts/setup-git-hooks.py
```

### 2. Verify Environment
```bash
cd anvil
python -m pytest tests/test_verdict_runner.py  # Should pass all 21 tests
```

## Configuration

### Config File Location
`tests/validation/config.yaml`

### Config Format
```yaml
validators:
  validator_name:
    callable: module.path.to.adapter_function
    root: path/to/test/cases
```

### Example
```yaml
validators:
  black:
    callable: anvil.validators.adapters.validate_black_parser
    root: cases/black_cases
  flake8:
    callable: anvil.validators.adapters.validate_flake8_parser
    root: cases/flake8_cases
  isort:
    callable: anvil.validators.adapters.validate_isort_parser
    root: cases/isort_cases
```

## Test Case Structure

### Folder-Based Cases
A folder is automatically discovered as a test case if it contains:
- `input.txt`: The raw input to the validator
- `expected_output.yaml`: The expected output structure

**Directory Structure Example:**
```
cases/black_cases/
├── scout_ci/
│   ├── job_180/
│   │   ├── input.txt
│   │   └── expected_output.yaml
│   ├── job_201/
│   │   ├── input.txt
│   │   └── expected_output.yaml
│   └── job_client/
│       ├── input.txt
│       └── expected_output.yaml
├── empty_output/
│   ├── input.txt
│   └── expected_output.yaml
```

### YAML File-Based Cases
Any `.yaml` file in the root cases directory with `input` and `expected` keys:

```yaml
name: "Black parser - empty output"
description: "Test black parser with empty output"

input:
  type: "text"
  content: ""

expected:
  validator: "black"
  total_violations: 0
  files_scanned: 0
  errors: 0
  warnings: 0
  info: 0
  by_code:
    BLACK001: 0
  file_violations: []
```

### Case Naming Convention
- **Folder cases**: Dot-notation path relative to cases root
  - `scout_ci/job_180/` → Case name: `scout_ci.job_180`
  - `scout_ci/job_client/` → Case name: `scout_ci.job_client`

- **YAML file cases**: Filename without extension
  - `empty_output.yaml` → Case name: `empty_output`
  - `regex_test.yaml` → Case name: `regex_test`

## CLI Usage

### List All Validators
```bash
python scripts/verdict.py --list
```

**Output:**
```
black
flake8
isort
```

### List All Cases for a Validator
```bash
python scripts/verdict.py --list black
```

**Output:**
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
  many_files
  mixed_content
  ... (11 more cases)
```

### Execute All Cases for a Validator
```bash
python scripts/verdict.py black
```

**Output:**
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
  [PASS] empty_output
  [FAIL] long_paths
    Expected: {...}
    Got:      {...}
  ...

Total: 17 | Passed: 15 | Failed: 2
```

### Execute Specific Case
```bash
python scripts/verdict.py black --cases scout_ci.job_client
```

### Execute Cases by Partial Path (Hierarchical Filtering)
```bash
python scripts/verdict.py black --cases scout_ci
```
Matches all cases under `scout_ci` folder:
- `scout_ci.job_180`
- `scout_ci.job_201`
- `scout_ci.job_302`
- `scout_ci.job_701`
- `scout_ci.job_829`
- `scout_ci.job_client`

## Implementation Details

### Module Structure
```
anvil/testing/verdict_runner.py
├── ConfigLoader: Loads YAML configuration
├── CaseDiscovery: Auto-discovers test cases from filesystem
│   ├── discover(): Find all cases
│   ├── filter_by_path(): Filter by hierarchical path
│   ├── _discover_folder_cases(): Find folder-based cases
│   └── _discover_yaml_cases(): Find YAML file-based cases
├── CaseExecutor: Executes test cases against adapters
│   ├── execute(): Run a single test case
│   ├── _load_file(): Load text files with UTF-8
│   └── _load_yaml_file(): Load YAML files with UTF-8
├── VerdictRunner: Orchestrates discovery and execution
│   ├── list_validators(): List all configured validators
│   ├── list_cases(): List cases for a validator
│   └── execute(): Execute test cases with optional filtering
└── VerdictCLI: Command-line interface
    ├── parse_args(): Parse command-line arguments
    ├── handle_list(): Implement --list flag
    └── handle_validate(): Execute validators
```

### Key Classes

**ConfigLoader**
```python
loader = ConfigLoader(Path("tests/validation/config.yaml"))
config = loader.load()  # Returns: {validators: {validator_name: {callable, root}}}
```

**CaseDiscovery**
```python
discovery = CaseDiscovery(Path("cases/black_cases"))
cases = discovery.discover()  # All cases
filtered = list(discovery.filter_by_path("scout_ci.job_180"))  # Specific case
```

**CaseExecutor**
```python
executor = CaseExecutor("anvil.validators.adapters.validate_black_parser")
result = executor.execute(case)
# Returns: {name, passed, expected, actual}
```

**VerdictRunner**
```python
runner = VerdictRunner(Path("tests/validation/config.yaml"))
validators = runner.list_validators()
cases = runner.list_cases("black")
results = runner.execute("black", case_filter="scout_ci")
```

## Error Handling

### Encoding Issues
All file operations use UTF-8 encoding to ensure cross-platform compatibility:
```python
with open(path, encoding="utf-8") as f:
    return yaml.safe_load(f)
```

### Adapter Callable Validation
Config loader validates that callable paths can be imported:
```python
config = loader.load()
# Raises ImportError if module or function not found
```

### Missing Test Cases
If no cases match the filter, execution returns empty results:
```
Total: 0 | Passed: 0 | Failed: 0
```

## Testing

### Run All Tests
```bash
cd anvil
python -m pytest tests/test_verdict_runner.py -v
```

**Expected Result:** All 21 tests should pass
- TestConfigLoader: 3 tests
- TestCaseDiscovery: 6 tests
- TestCaseExecutor: 3 tests
- TestVerdictRunner: 5 tests
- TestIntegration: 3 tests

### Test Coverage
The verdict runner achieves 70% coverage for the core module. Low overall project coverage is expected since only the new verdict_runner module is tested.

## Troubleshooting

### Case Not Discovered
**Problem:** Expected test case doesn't appear in `--list` output

**Solutions:**
1. Check case folder structure: Must have `input.txt` and/or `expected_output.yaml`
2. Check YAML files: Must be in root cases directory with `.yaml` extension
3. Verify relative paths: Cases are discovered recursively from the `root` path in config

### Execution Fails with Encoding Error
**Problem:** `charmap_encode` or `charmap_decode` errors

**Solution:** Ensure all files use UTF-8 encoding. The verdict runner automatically opens files with UTF-8.

### Config File Not Found
**Problem:** `FileNotFoundError` for config path

**Solution:**
1. Run scripts from the anvil directory: `cd anvil && python scripts/verdict.py ...`
2. Or provide absolute path to config file
3. Config relative paths are resolved from config file's directory

### Adapter Import Fails
**Problem:** `ImportError` when loading config

**Solution:**
1. Verify callable path is correct: `module.submodule.function_name`
2. Check that adapter function is defined in specified module
3. Verify all imports in the adapter module are available

## Performance

### Case Discovery
- First discovery is cached by OS filesystem
- Subsequent `--list` calls are instantaneous
- Large case directories (100+ cases) discovered in <1 second

### Case Execution
- Depends on validator implementation (typically 1-100ms per case)
- All cases executed sequentially
- Results printed as each case completes

## Future Enhancements

Potential improvements:
- [ ] Parallel case execution with `--parallel` flag
- [ ] JSON output format with `--format json`
- [ ] Test case templates for faster creation
- [ ] Coverage tracking with `--coverage` flag
- [ ] CI integration with GitHub Actions/GitLab CI
- [ ] Watch mode with `--watch` flag for TDD

## Contributing

When adding new test cases:
1. Create case folder or YAML file in appropriate cases directory
2. Add `input.txt` and `expected_output.yaml` (or use YAML file format)
3. Run `verdict --list validator` to verify discovery
4. Run `verdict validator --cases your.new.case` to verify execution
5. Commit with message: "test: Add test case for [validator name]"

## License

See main project LICENSE file.
