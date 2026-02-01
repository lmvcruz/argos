# Anvil User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Core Concepts](#core-concepts)
5. [Command Reference](#command-reference)
6. [Configuration](#configuration)
7. [Validators](#validators)
8. [Git Integration](#git-integration)
9. [CI/CD Integration](#cicd-integration)
10. [Statistics & History](#statistics--history)
11. [Best Practices](#best-practices)
12. [Examples](#examples)

## Introduction

Anvil is a flexible, language-agnostic code quality validation tool that enforces configurable quality standards across Python and C++ projects. It provides a unified interface for running multiple code quality tools and aggregating their results.

### Key Features

- **Multi-Language Support**: Built-in support for Python and C++
- **Extensible Architecture**: Easy to add new validators
- **Smart Validation**: Only validate changed files in incremental mode
- **Historical Tracking**: Track validation history and detect flaky tests
- **Git Integration**: Pre-commit and pre-push hooks
- **CI/CD Ready**: Easy integration with continuous integration pipelines
- **Rich Output**: Color-coded, formatted console output with actionable suggestions

### When to Use Anvil

- **Development**: Run quality checks before committing code
- **Code Review**: Automated quality validation in pull requests
- **CI/CD**: Quality gate in continuous integration pipelines
- **Audits**: Periodic code quality assessments

## Installation

### Prerequisites

- Python 3.8 or higher
- Git (for git hook features)
- Platform-specific tools for validators you want to use

### Install from Source

```bash
cd anvil
pip install -e .
```

### Verify Installation

```bash
anvil --version
anvil list
```

## Quick Start

### Run All Validators

```bash
# Run all configured validators
anvil check

# Run with verbose output
anvil check --verbose

# Run quietly (errors only)
anvil check --quiet
```

### Incremental Validation

```bash
# Only validate files changed since last commit
anvil check --incremental

# Validate files changed since specific commit
anvil check --incremental --since HEAD~3
```

### Language-Specific Validation

```bash
# Python only
anvil check --language python

# C++ only
anvil check --language cpp
```

### Run Specific Validators

```bash
# Run only flake8
anvil check --validator flake8

# Run multiple validators
anvil check --validator flake8 --validator black
```

## Core Concepts

### Validators

Validators are tools that check code quality. Each validator:
- Targets specific languages (Python, C++, or both)
- Produces structured output (errors, warnings)
- Has configurable thresholds and options
- Can be enabled/disabled in configuration

### Validation Modes

#### Full Mode (Default)
- Validates all files in the project
- Comprehensive quality check
- Use for audits or CI on main branch

#### Incremental Mode
- Validates only changed files (git diff)
- Fast feedback during development
- Use in pre-commit hooks or during development

### Results Aggregation

Anvil aggregates results from all validators:
- **Errors**: Critical issues that fail validation
- **Warnings**: Issues that don't fail validation but should be reviewed
- **Statistics**: Success rates, trends, flaky tests

### Exit Codes

Anvil uses standard exit codes:
- `0`: All validators passed
- `1`: One or more validators failed
- `2`: Configuration error
- `3`: Required tools missing

## Command Reference

### `anvil check`

Run code quality validators.

```bash
anvil check [OPTIONS]
```

**Options:**
- `--incremental`: Only validate changed files
- `--since COMMIT`: Validate files changed since commit (requires --incremental)
- `--language LANG`: Only run validators for language (python, cpp)
- `--validator NAME`: Run specific validator (can be repeated)
- `--verbose`: Show detailed output
- `--quiet`: Show only errors
- `--fail-fast`: Stop on first error
- `--no-stats`: Disable statistics tracking

**Examples:**

```bash
# Full validation
anvil check

# Incremental with verbose output
anvil check --incremental --verbose

# Python validators only
anvil check --language python

# Run flake8 and black only
anvil check --validator flake8 --validator black

# Fast fail on errors
anvil check --fail-fast
```

### `anvil install-hooks`

Install git hooks for automatic validation.

```bash
anvil install-hooks [OPTIONS]
```

**Options:**
- `--hook-type TYPE`: Hook type (pre-commit, pre-push) [default: pre-commit]
- `--uninstall`: Remove installed hooks

**Examples:**

```bash
# Install pre-commit hook
anvil install-hooks

# Install pre-push hook
anvil install-hooks --hook-type pre-push

# Uninstall hooks
anvil install-hooks --uninstall
```

### `anvil config`

Manage Anvil configuration.

```bash
anvil config SUBCOMMAND [OPTIONS]
```

**Subcommands:**

- `show`: Display current configuration
- `validate`: Validate anvil.toml
- `init`: Generate default configuration
- `check-tools`: Show available validators

**Examples:**

```bash
# Show configuration
anvil config show

# Validate config file
anvil config validate

# Generate default config
anvil config init

# Check which tools are available
anvil config check-tools
```

### `anvil list`

List available validators.

```bash
anvil list [OPTIONS]
```

**Options:**
- `--language LANG`: Filter by language
- `--detailed`: Show detailed information

**Examples:**

```bash
# List all validators
anvil list

# List Python validators
anvil list --language python

# Detailed information
anvil list --detailed
```

### `anvil stats`

View validation statistics.

```bash
anvil stats SUBCOMMAND [OPTIONS]
```

**Subcommands:**

- `report`: Show statistics summary
- `export`: Export statistics to file
- `flaky`: List flaky tests
- `problem-files`: List problematic files
- `trends`: Show validator trends

**Examples:**

```bash
# Statistics report
anvil stats report

# Last 30 days only
anvil stats report --days 30

# Export to JSON
anvil stats export --format json --output stats.json

# Find flaky tests
anvil stats flaky --threshold 0.7

# Show pylint trends
anvil stats trends --validator pylint
```

## Configuration

Anvil uses `anvil.toml` for configuration. Place this file in your project root.

### Minimal Configuration

```toml
[project]
name = "my-project"
languages = ["python"]
```

### Full Configuration Example

```toml
[project]
name = "my-project"
version = "1.0.0"
languages = ["python", "cpp"]

[validation]
mode = "full"  # or "incremental"
fail_fast = false
parallel = true
max_workers = 4

[python]
enabled = true

[python.flake8]
enabled = true
max_line_length = 100
exclude = ["build/", ".git/", "__pycache__/"]

[python.black]
enabled = true
line_length = 100

[python.pylint]
enabled = true
min_score = 8.0

[python.pytest]
enabled = true
min_coverage = 90.0

[cpp]
enabled = true

[cpp.clang-tidy]
enabled = true
checks = ["*", "-readability-braces-around-statements"]

[cpp.cppcheck]
enabled = true
std = "c++17"

[statistics]
enabled = true
database = ".anvil/stats.db"
retention_days = 90

[smart-filtering]
enabled = true
skip_success_threshold = 0.95
prioritize_flaky = true
```

### Configuration Sections

#### `[project]`
- `name`: Project name
- `version`: Project version
- `languages`: List of languages to validate

#### `[validation]`
- `mode`: Default validation mode (full/incremental)
- `fail_fast`: Stop on first error
- `parallel`: Run validators in parallel
- `max_workers`: Maximum parallel workers

#### `[python]` / `[cpp]`
- `enabled`: Enable language validation
- Individual validator sections (e.g., `[python.flake8]`)

#### `[statistics]`
- `enabled`: Track validation history
- `database`: Statistics database path
- `retention_days`: Days to keep history

#### `[smart-filtering]`
- `enabled`: Enable smart test filtering
- `skip_success_threshold`: Skip tests above success rate
- `prioritize_flaky`: Run flaky tests first

See [CONFIGURATION.md](CONFIGURATION.md) for complete reference.

## Validators

### Python Validators

#### flake8
Linting and style checking.

**Default Configuration:**
```toml
[python.flake8]
enabled = true
max_line_length = 100
exclude = ["build/", ".git/"]
```

#### black
Code formatting.

**Default Configuration:**
```toml
[python.black]
enabled = true
line_length = 100
check = true  # Check mode (don't modify files)
```

#### isort
Import sorting.

**Default Configuration:**
```toml
[python.isort]
enabled = true
line_length = 100
profile = "black"
```

#### pylint
Comprehensive static analysis.

**Default Configuration:**
```toml
[python.pylint]
enabled = true
min_score = 8.0
```

#### pytest
Test execution with coverage.

**Default Configuration:**
```toml
[python.pytest]
enabled = true
min_coverage = 90.0
```

### C++ Validators

#### clang-tidy
Comprehensive C++ analysis.

**Default Configuration:**
```toml
[cpp.clang-tidy]
enabled = true
checks = ["*"]
header_filter = ".*"
```

#### cppcheck
Bug detection and undefined behavior.

**Default Configuration:**
```toml
[cpp.cppcheck]
enabled = true
std = "c++17"
enable = ["warning", "style", "performance"]
```

#### clang-format
Code formatting.

**Default Configuration:**
```toml
[cpp.clang-format]
enabled = true
style = "Google"
```

#### Google Test
Test execution.

**Default Configuration:**
```toml
[cpp.gtest]
enabled = true
test_binary = "build/tests/test_runner"
```

## Git Integration

### Pre-Commit Hook

Anvil can automatically validate code before commits.

#### Installation

```bash
anvil install-hooks
```

This creates `.git/hooks/pre-commit` that runs:

```bash
anvil check --incremental
```

#### Bypass Hook

To bypass the hook temporarily:

```bash
git commit --no-verify -m "Commit message"
```

Or include bypass keyword in commit message:

```bash
git commit -m "[skip-anvil] WIP commit"
```

### Pre-Push Hook

Validate before pushing to remote.

```bash
anvil install-hooks --hook-type pre-push
```

### Custom Hook Configuration

Edit `.git/hooks/pre-commit` to customize:

```bash
#!/bin/bash
# Custom pre-commit hook

# Run incremental validation
anvil check --incremental --fail-fast

# Or run specific validators
# anvil check --validator flake8 --validator black --incremental
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Quality Gate

on: [push, pull_request]

jobs:
  anvil:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for incremental mode

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Anvil
        run: pip install -e ./anvil

      - name: Run Anvil
        run: anvil check --incremental --verbose
```

### GitLab CI

```yaml
anvil:
  stage: test
  script:
    - pip install -e ./anvil
    - anvil check --incremental --verbose
  only:
    - merge_requests
    - master
```

### Jenkins

```groovy
stage('Quality Gate') {
    steps {
        sh 'pip install -e ./anvil'
        sh 'anvil check --incremental --verbose'
    }
}
```

## Statistics & History

### Enable Statistics

```toml
[statistics]
enabled = true
database = ".anvil/stats.db"
retention_days = 90
```

### View Statistics

```bash
# Summary report
anvil stats report

# Last 30 days
anvil stats report --days 30

# Flaky tests
anvil stats flaky

# Problem files
anvil stats problem-files
```

### Smart Filtering

Smart filtering uses historical data to optimize validation:

```toml
[smart-filtering]
enabled = true
skip_success_threshold = 0.95  # Skip tests with 95%+ success rate
prioritize_flaky = true         # Run flaky tests first
```

When enabled:
- High-success tests are skipped
- Flaky tests run first
- New/modified tests always run
- Fails open (runs all if insufficient history)

## Best Practices

### Development Workflow

1. **Install pre-commit hook**
   ```bash
   anvil install-hooks
   ```

2. **Run incremental validation during development**
   ```bash
   anvil check --incremental
   ```

3. **Fix issues before committing**
   - Address errors first
   - Consider warnings
   - Run full validation before push

4. **Periodic full validation**
   ```bash
   anvil check
   ```

### CI/CD Strategy

- **PR Checks**: Run incremental validation
- **Main Branch**: Run full validation
- **Nightly**: Run full validation with stats export

### Configuration Tips

1. **Start Conservative**: Enable all validators, adjust thresholds as needed
2. **Language-Specific**: Separate configs for Python vs C++
3. **Project-Specific**: Customize validators for project requirements
4. **Track History**: Enable statistics to identify trends

### Performance Optimization

- Use `--incremental` for fast feedback
- Enable `parallel = true` for multi-core systems
- Enable smart filtering after collecting history
- Use `--fail-fast` in development

## Examples

### Example 1: Python Project Setup

```bash
# Initialize configuration
cd my-python-project
anvil config init

# Edit anvil.toml
cat > anvil.toml << EOF
[project]
name = "my-project"
languages = ["python"]

[python.flake8]
enabled = true
max_line_length = 100

[python.black]
enabled = true
line_length = 100

[python.pytest]
enabled = true
min_coverage = 85.0
EOF

# Install hooks
anvil install-hooks

# Run validation
anvil check
```

### Example 2: Mixed Python/C++ Project

```toml
[project]
name = "mixed-project"
languages = ["python", "cpp"]

[python]
enabled = true

[python.flake8]
enabled = true

[python.pytest]
enabled = true
min_coverage = 90.0

[cpp]
enabled = true

[cpp.clang-tidy]
enabled = true

[cpp.gtest]
enabled = true
test_binary = "build/tests/all_tests"
```

### Example 3: CI Pipeline with Statistics

```yaml
# .github/workflows/quality.yml
name: Quality Gate

on: [push, pull_request]

jobs:
  anvil:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          pip install -e ./anvil
          pip install -r requirements.txt

      - name: Run Anvil
        run: anvil check --incremental --verbose

      - name: Export Statistics
        if: always()
        run: anvil stats export --format json --output anvil-stats.json

      - name: Upload Statistics
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: anvil-statistics
          path: anvil-stats.json
```

### Example 4: Custom Validator Thresholds

```toml
[python.flake8]
enabled = true
max_line_length = 120  # Relaxed from default 100
max_complexity = 15

[python.pylint]
enabled = true
min_score = 7.5  # Relaxed from default 8.0
disable = ["C0111", "R0903"]  # Disable specific checks

[python.pytest]
enabled = true
min_coverage = 80.0  # Relaxed from default 90.0
```

### Example 5: Incremental Development Workflow

```bash
# Start feature development
git checkout -b feature/new-feature

# Make changes to files
vim src/my_module.py

# Quick validation (only changed files)
anvil check --incremental

# Fix issues
black src/my_module.py
flake8 src/my_module.py

# Validate again
anvil check --incremental

# Commit (hook runs automatically)
git commit -m "Add new feature"

# Before push, full validation
anvil check
git push origin feature/new-feature
```

## Troubleshooting

For common issues and solutions, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## Further Reading

- [API Documentation](API.md) - Extending Anvil with custom validators
- [Configuration Reference](CONFIGURATION.md) - Complete configuration options
- [Tutorial](../TUTORIAL.md) - Step-by-step tutorial
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions

## Support

- **Issues**: Report bugs on GitHub
- **Documentation**: Check docs/ directory
- **Examples**: See examples/ directory
