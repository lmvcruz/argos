# Linting Rules Documentation

This document lists all active linting rules and how to discover available rules for each tool.

## Table of Contents
- [Quick Reference: Active Rules](#quick-reference-active-rules)
- [Flake8 Rules](#flake8-rules)
- [Pylint Rules](#pylint-rules)
- [Mypy Rules](#mypy-rules)
- [Black Configuration](#black-configuration)
- [Isort Configuration](#isort-configuration)
- [Radon Complexity Thresholds](#radon-complexity-thresholds)
- [Vulture Configuration](#vulture-configuration)
- [Autoflake Settings](#autoflake-settings)
- [How to List All Available Rules](#how-to-list-all-available-rules)

---

## Quick Reference: Active Rules

### Blocking Checks (Must Pass)
- **Flake8**: All syntax errors (E9*) + ALL Pyflakes errors (F*)
- **Black**: Code formatting (line length: 100)
- **Isort**: Import sorting (black-compatible profile)
- **Radon**: Complexity B or better (≤10), Maintainability Index ≥20
- **Tests**: All unit tests must pass

### Informational Checks (Warnings Only)
- **Flake8**: Style warnings (E*, W*, C*, N*)
- **Autoflake**: Unused imports/variables
- **Vulture**: Dead code (80% confidence threshold)
- **Pylint**: Selected static analysis rules

---

## Flake8 Rules

### Currently Active Rules

**Configuration**: Pre-commit script separates syntax errors from style warnings.

#### Blocking (Syntax Errors)
```bash
# Command: python -m flake8 . --select=E9,F
```

| Code | Category | Description |
|------|----------|-------------|
| **E9** | Syntax Errors | Runtime/syntax errors (E901, E902, etc.) |
| **F** | Pyflakes | ALL Pyflakes errors (F401-F901) - comprehensive check |

**All 29 Pyflakes Error Codes Checked:**
- F40x: Import errors (unused, shadowed, star imports, late __future__)
- F60x: Dictionary key issues (repeated keys)
- F62x-F63x: Assignment/unpacking errors (starred expressions, tuple assertions)
- F70x: Control flow errors (break/continue/return/yield outside scope)
- F81x: Name definition errors (redefinition, comprehension scope)
- F82x: Undefined name errors (undefined names, __all__ issues, reference before assignment)
- F83x: Function errors (duplicate arguments)
- F84x: Variable errors (assigned but never used)
- F90x: Exception errors (NotImplemented vs NotImplementedError)

#### Informational (Style Warnings)
```bash
# Command: python -m flake8 . --ignore=E501
```

| Code | Category | Description | Status |
|------|----------|-------------|--------|
| **E1-E5** | PEP8 Indentation/Whitespace | Indentation, whitespace issues | ✓ Active |
| **E501** | PEP8 Line Length | Line too long (>79 chars) | ✗ Disabled (using Black) |
| **W** | PEP8 Warnings | Whitespace warnings | ✓ Active |
| **C** | McCabe Complexity | Complexity warnings | ✓ Active |
| **N** | Naming Conventions | PEP8 naming style | ✓ Active |

### Complete Flake8 Error Code Reference

#### E: PEP8 Errors
- **E1**: Indentation (E101-E106)
- **E2**: Whitespace (E201-E206, E211)
- **E3**: Blank lines (E301-E306)
- **E4**: Import statements (E401-E402)
- **E5**: Line length (E501-E502)
- **E7**: Statement structure (E701-E743)
- **E9**: Runtime/syntax (E901-E902)

#### W: PEP8 Warnings
- **W1**: Indentation warnings (W191)
- **W2**: Whitespace warnings (W291-W293)
- **W3**: Blank line warnings (W391)
- **W5**: Line break warnings (W503-W505)
- **W6**: Deprecated features (W601-W606)

#### F: Pyflakes Errors
- **F401**: Module imported but unused
- **F402**: Import module from line N shadowed by loop variable
- **F403**: `from module import *` used; unable to detect undefined names
- **F404**: Late `__future__` import
- **F405**: Name may be undefined, or defined from star imports
- **F406**: `from module import *` only allowed at module level
- **F407**: Future import not the first statement
- **F601**: Dictionary key name repeated with different values
- **F602**: Dictionary key variable name repeated with different values
- **F621**: Too many expressions in star-unpacking assignment
- **F622**: Two or more starred expressions in assignment
- **F631**: Assert test is a non-empty tuple (always true)
- **F632**: Use `==` or `is` to compare constant literals
- **F633**: Use of `>>` is invalid with `print` function
- **F634**: `if` test is a tuple, which is always `True`
- **F701**: `break` outside loop
- **F702**: `continue` outside loop
- **F704**: Yield or yield from statement outside function
- **F706**: `return` outside function
- **F707**: `except:` block as not the last exception handler
- **F811**: Redefinition of unused name from line N
- **F812**: List comprehension redefines name from line N
- **F821**: Undefined name
- **F822**: Undefined name in `__all__`
- **F823**: Local variable referenced before assignment
- **F831**: Duplicate argument name in function definition
- **F841**: Local variable assigned but never used
- **F901**: `raise NotImplemented` should be `raise NotImplementedError`

---

## Pylint Rules

### Currently Active Rules

**Configuration**: `pyproject.toml` → `[tool.pylint.messages_control]`

#### Enabled in Pre-commit Script
```bash
# Command: python -m pylint --disable=all --enable=<rules>
```

| Code | Message ID | Description | Category |
|------|------------|-------------|----------|
| **unused-import** | W0611 | Imported module not used | Warning |
| **unused-variable** | W0612 | Unused local variable | Warning |
| **unused-argument** | W0613 | Unused function argument | Warning |
| **unreachable** | W0101 | Unreachable code | Warning |
| **dangerous-default-value** | W0102 | Dangerous default value as argument | Warning |
| **redefined-builtin** | W0622 | Redefining built-in | Warning |
| **import-error** | E0401 | Unable to import module | Error |

#### Disabled Rules (in pyproject.toml)

| Code | Message ID | Description | Reason |
|------|------------|-------------|--------|
| **C0111** | missing-docstring | Missing docstrings | We have some code without docs |
| **C0103** | invalid-name | Invalid variable names | Too strict for our naming |
| **R0903** | too-few-public-methods | Class has too few methods | Dataclasses are OK |
| **R0913** | too-many-arguments | Too many arguments | Some functions need them |
| **W0212** | protected-access | Accessing protected member | Needed in tests |

### Design Thresholds (from pyproject.toml)

```toml
max-args = 7              # Maximum function arguments
max-attributes = 10       # Maximum class attributes
max-branches = 15         # Maximum branches in function
max-locals = 20          # Maximum local variables
max-returns = 8          # Maximum return statements
max-statements = 60      # Maximum statements in function
```

### All Available Pylint Message Categories

#### C: Convention
- **C01**: Basic conventions (naming, docstrings)
- **C02**: Code structure conventions
- **C03**: Design conventions
- **C04**: Typecheck conventions

#### R: Refactor
- **R00**: Complexity refactoring suggestions
- **R01**: Design refactoring suggestions
- **R02**: Import refactoring suggestions

#### W: Warning
- **W00**: Basic warnings
- **W01**: Deprecated/unreachable code warnings
- **W02**: Typecheck warnings
- **W03**: Design warnings
- **W04**: Exception warnings
- **W05**: String formatting warnings
- **W06**: Import warnings

#### E: Error
- **E00**: Basic errors
- **E01**: Import errors
- **E02**: Typecheck errors
- **E04**: Exception errors
- **E11**: Method errors
- **E12**: Function errors

#### F: Fatal
- **F00**: Fatal errors (import failures, syntax errors)

---

## Mypy Rules

### Currently Active Rules

**Configuration**: `pyproject.toml` → `[tool.mypy]`

| Option | Value | Description |
|--------|-------|-------------|
| `python_version` | `"3.11"` | Target Python version |
| `warn_return_any` | `true` | Warn about returning Any from functions |
| `warn_unused_configs` | `true` | Warn about unused config settings |
| `disallow_untyped_defs` | `false` | Allow functions without type hints |
| `check_untyped_defs` | `true` | Type-check bodies of untyped functions |
| `no_implicit_optional` | `true` | Don't assume arguments with default None are Optional |
| `warn_redundant_casts` | `true` | Warn about unnecessary casts |
| `warn_unused_ignores` | `true` | Warn about unused `# type: ignore` |
| `warn_no_return` | `true` | Warn about missing return statements |
| `strict_equality` | `true` | Prohibit equality checks with incompatible types |

### Test Overrides
- Tests have `disallow_untyped_defs = false` (type hints optional)

---

## Black Configuration

**Philosophy**: Black is opinionated with minimal configuration.

### Active Settings
```toml
line-length = 100           # Max characters per line
target-version = ['py311']  # Python version for syntax
```

### Exclusions
- `.git/`, `__pycache__/`, `.pytest_cache/`
- `.venv/`, `venv/`, `build/`, `dist/`

**Note**: Black has no "rules" to enable/disable. It enforces a single style.

---

## Isort Configuration

### Active Settings
```toml
profile = "black"                    # Compatible with Black
line_length = 100                    # Match Black's line length
force_single_line = false            # Allow multiple imports per line
force_sort_within_sections = true    # Sort alphabetically within sections
```

### Import Sections (in order)
1. `FUTURE` - `from __future__ import ...`
2. `STDLIB` - Python standard library
3. `THIRDPARTY` - Third-party packages
4. `FIRSTPARTY` - Our `forge` package
5. `LOCALFOLDER` - Relative imports

---

## Radon Complexity Thresholds

### Active Settings
```toml
cc_min = "B"    # Minimum acceptable complexity rating
mi_min = 20     # Minimum maintainability index
```

### Cyclomatic Complexity Scale

| Rating | Complexity | Risk | Status |
|--------|------------|------|--------|
| **A** | 1-5 | Low, simple | ✓ Accepted |
| **B** | 6-10 | Low, moderate | ✓ Accepted |
| **C** | 11-20 | Moderate | ✗ **BLOCKED** |
| **D** | 21-30 | High | ✗ **BLOCKED** |
| **E** | 31-40 | Very high | ✗ **BLOCKED** |
| **F** | 41+ | Extremely high | ✗ **BLOCKED** |

### Maintainability Index Scale

| Score | Maintainability | Status |
|-------|-----------------|--------|
| **100-80** | Highly maintainable | ✓ Excellent |
| **79-50** | Moderately maintainable | ✓ Good |
| **49-20** | Difficult to maintain | ⚠ Warning |
| **19-0** | Unmaintainable | ✗ **BLOCKED** |

---

## Vulture Configuration

### Active Settings
```toml
min_confidence = 80           # Only report 80%+ confidence
sort_by_size = true          # Sort by line count
```

### Ignored Decorators
- `@pytest.fixture`
- `@dataclass`

### What Vulture Detects
- Unused functions, classes, methods
- Unused variables and properties
- Unreachable code
- Unused imports (also caught by flake8/autoflake)

**Note**: Informational only - doesn't block commits.

---

## Autoflake Settings

### Active Checks
```bash
# Command: python -m autoflake --remove-all-unused-imports
#          --remove-unused-variables --check --recursive .
```

### What Autoflake Detects
- Unused imports
- Unused variables
- Duplicate keys in dictionaries

**Note**: Informational only - doesn't block commits.

---

## How to List All Available Rules

### Flake8
```bash
# List all error codes
python -m flake8 --help | grep "select"

# Show version and plugins
python -m flake8 --version

# Generate violations to see codes
python -m flake8 . --statistics
```

### Pylint
```bash
# List ALL messages
python -m pylint --list-msgs

# List only enabled messages
python -m pylint --list-msgs-enabled

# List messages by category
python -m pylint --list-msgs | grep "^:convention"
python -m pylint --list-msgs | grep "^:warning"
python -m pylint --list-msgs | grep "^:error"

# Generate full report
python -m pylint --generate-rcfile > .pylintrc
```

### Mypy
```bash
# List all config options
python -m mypy --help

# Common error codes
python -m mypy --show-error-codes <file>
```

### Radon
```bash
# Show complexity for all files
python -m radon cc . -a --total-average

# Show maintainability index
python -m radon mi . --show

# Detailed metrics with thresholds
python -m radon cc . -a -nb --min B
```

### Vulture
```bash
# Run with detailed output
python -m vulture . --min-confidence 60

# Sort by confidence
python -m vulture . --sort-by-confidence
```

---

## Updating Rules

### To Enable More Pylint Rules
Edit `scripts/pre-commit-check.py`, line ~166:
```python
"python -m pylint --disable=all "
"--enable=unused-import,unused-variable,unused-argument,unreachable,"
"dangerous-default-value,redefined-builtin,import-error,<add-more-here> "
```

### To Disable Specific Flake8 Codes
Edit pre-commit script or add to `setup.cfg`:
```ini
[flake8]
ignore = E501,W503
```

### To Change Complexity Thresholds
Edit `pyproject.toml`:
```toml
[tool.radon]
cc_min = "A"  # More strict (only complexity 1-5)
mi_min = 30   # Higher maintainability requirement
```

---

## Summary

**Total Active Rules**: 100+ checks across 8 tools

**Blocking**:
- Flake8 syntax errors (~15 codes)
- Black formatting (opinionated)
- Isort organization (5 sections)
- Radon complexity (B or better)
- All unit tests

**Informational**:
- Flake8 style (~80 codes)
- Pylint selected (~7 rules)
- Autoflake (unused code)
- Vulture (dead code)

**Philosophy**: Strict on correctness, informational on style, proactive on complexity.
