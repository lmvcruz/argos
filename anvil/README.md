# Anvil - Code Quality Gate Tool

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A flexible, language-agnostic code quality validation tool that enforces configurable quality standards across Python and C++ projects.

## Overview

Anvil is a comprehensive quality gate tool that integrates multiple code quality validators into a unified workflow. It can be deployed in various contexts:

- 🔧 **Interactive Development**: Run checks during coding
- 🎣 **Git Hooks**: Automatic validation on commits/pushes
- 🚀 **CI/CD Pipelines**: Quality gates in continuous integration
- 📊 **Manual Audits**: Periodic code quality assessments

## Features

### Core Capabilities

- **Multi-Language Support**: Python and C++ validators
- **Extensible Architecture**: Plugin system for custom validators
- **Flexible Deployment**: Works anywhere in your workflow
- **Smart Validation**: Incremental mode validates only changed files
- **Rich Output**: Color-coded, formatted console output with actionable suggestions

### Advanced Features

- **Historical Tracking**: Statistics database for trend analysis
- **Smart Filtering**: Optimize test execution based on success rates
- **Flaky Test Detection**: Identify unreliable tests automatically
- **Parallel Execution**: Multi-core validation for speed
- **Configurable Thresholds**: Customize quality standards per project

## Installation

### Prerequisites

- Python 3.8 or higher
- Git (for hook features)

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

### 1. Initialize Configuration

```bash
# Generate default configuration
anvil config init

# Edit anvil.toml to customize settings
```

### 2. Run Validation

```bash
# Run all validators
anvil check

# Run incrementally (only changed files)
anvil check --incremental

# Run specific validators
anvil check --validator flake8 --validator black

# Run with verbose output
anvil check --verbose
```

### 3. Install Git Hooks

```bash
# Install pre-commit hook
anvil install-hooks

# Test the hook
git commit -m "Test commit"
```

## Supported Validators

### Python

- **flake8**: Linting and style checking
- **black**: Code formatting
- **isort**: Import sorting
- **pylint**: Static analysis
- **pytest**: Testing with coverage
- **autoflake**: Unused code detection
- **radon**: Complexity analysis
- **vulture**: Dead code detection

### C++ (Planned)

- **clang-tidy**: Static analysis
- **cppcheck**: Bug detection
- **cpplint**: Style checking
- **clang-format**: Code formatting
- **include-what-you-use**: Include optimization
- **Google Test**: Test execution

## Configuration Example

```toml
[project]
name = "my-project"
languages = ["python"]

[validation]
mode = "full"
parallel = true

[python.flake8]
enabled = true
max_line_length = 100

[python.black]
enabled = true
line_length = 100

[python.pytest]
enabled = true
min_coverage = 90.0
```

## Documentation

Comprehensive documentation is available in the `docs/` directory:

- **[User Guide](docs/USER_GUIDE.md)**: Complete guide with examples
- **[Configuration Reference](docs/CONFIGURATION.md)**: All configuration options
- **[API Documentation](docs/API.md)**: Extending Anvil with custom validators
- **[Troubleshooting Guide](docs/TROUBLESHOOTING.md)**: Common issues and solutions
- **[Tutorial](TUTORIAL.md)**: Step-by-step tutorial for new users

## Usage Examples

### Development Workflow

```bash
# Make changes to code
vim src/my_module.py

# Quick validation (incremental)
anvil check --incremental

# Fix issues
black src/my_module.py

# Commit (hook runs automatically)
git commit -m "Add new feature"
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Run Anvil Quality Gate
  run: |
    pip install -e ./anvil
    anvil check --incremental --verbose
```

### Statistics and Trends

```bash
# View validation statistics
anvil stats report

# Find flaky tests
anvil stats flaky

# Export statistics
anvil stats export --format json --output stats.json
```

## Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
python scripts/setup-git-hooks.py
```

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov --cov-report=html

# Run specific test file
pytest tests/test_argument_parser.py
```

### Pre-commit Checks

```bash
# Run all quality checks
python scripts/pre-commit-check.py

# Individual checks
python -m flake8 anvil/ tests/
python -m black --check anvil/ tests/
python -m pytest --cov
```

### Code Quality Standards

- **Line Length**: 100 characters maximum
- **Test Coverage**: 90% minimum
- **Docstrings**: Google-style for all public functions
- **Type Hints**: Required for function parameters and returns

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all quality checks pass
5. Submit a pull request

See [TUTORIAL.md](TUTORIAL.md) for development guide.

## Project Structure

```
anvil/
├── anvil/              # Main package
│   ├── cli/            # Command-line interface
│   ├── config/         # Configuration management
│   ├── core/           # Core validation logic
│   ├── git/            # Git integration
│   ├── models/         # Data models
│   ├── parsers/        # Output parsers
│   ├── reporting/      # Result reporting
│   ├── storage/        # Statistics database
│   ├── utils/          # Utility functions
│   └── validators/     # Validator implementations
├── docs/               # Documentation
├── tests/              # Test suite
├── scripts/            # Development scripts
└── anvil.toml          # Configuration file
```

## License

Part of the Argos Project.

## Acknowledgments

Anvil integrates and builds upon excellent open-source tools:
- flake8, black, isort, pylint, pytest (Python)
- clang-tidy, cppcheck, cpplint (C++)

## Related Projects

- **Forge**: CMake build system wrapper (part of Argos)
- **Gaze**: Code visualization tool (part of Argos)

## Support

- **Documentation**: See `docs/` directory
- **Issues**: Report bugs on GitHub
- **Tutorial**: See [TUTORIAL.md](TUTORIAL.md)
