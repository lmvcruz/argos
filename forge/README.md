# Forge - CMake Build Wrapper

[![Forge Tests](https://github.com/lmvcruz/argos/actions/workflows/forge-tests.yml/badge.svg)](https://github.com/lmvcruz/argos/actions/workflows/forge-tests.yml)
[![Coverage](https://img.shields.io/badge/coverage-96.88%25-brightgreen)](https://github.com/lmvcruz/argos)

A non-intrusive CMake build wrapper that captures build events, output, and metadata without requiring any modifications to monitored projects.

## Status

🚧 **Under Development** - Following TDD principles

Current: **Iteration 8, Step 8.3** - Cross-Platform Testing ✅

**Completed:**
- ✅ Iterations 1-7: Core implementation (CLI, CMake execution, output inspection, persistence, integration)
- ✅ Step 8.1: Sample project testing
- ✅ Step 8.2: Edge case testing
- 🔄 Step 8.3: Cross-Platform testing (in progress)

## Quick Start

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run tests with coverage
pytest --cov=forge --cov-report=html
```

## Development

This project follows Test-Driven Development (TDD) principles. See [forge-implementation-plan.md](../docs/forge-implementation-plan.md) for the complete development roadmap.

### Code Quality Checks

Before committing, run the pre-commit checks to ensure code quality:

```bash
# Run all pre-commit checks (flake8 + black)
python scripts/pre-commit-check.py

# Or install as a git hook (optional)
python scripts/setup-git-hooks.py
```

The checks include:
- **Syntax errors**: flake8 checks for Python syntax errors and undefined names
- **Code style**: flake8 checks for PEP 8 compliance (warnings only)
- **Formatting**: black checks code formatting

To auto-format your code:
```bash
python -m black .
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_project_structure.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=forge --cov-report=term-missing
```

## Project Structure

```
forge/
├── cli/                   # Command-line argument parsing
├── cmake/                 # CMake parameter management and execution
├── inspector/             # Build output analysis
├── storage/               # Database persistence
├── models/                # Data models
├── utils/                 # Utility functions
├── scripts/               # Development scripts
│   ├── pre-commit-check.py  # Code quality checks
│   └── setup-git-hooks.py   # Git hooks installer
├── tests/                 # Test suite
│   └── fixtures/         # Test fixtures and sample data
├── requirements.txt       # Dependencies
├── pytest.ini            # Pytest configuration
└── README.md             # This file
```

## Documentation

- [Project Description](../docs/Argus-Project-Description.md)
- [Forge Specification](../docs/forge-specification.md)
- [Forge Architecture](../docs/forge-architecture.md)
- [Implementation Plan](../docs/forge-implementation-plan.md)

## License

[To be determined]
