# Anvil - Code Quality Gate Tool

A flexible, language-agnostic code quality validation tool that enforces configurable quality standards across Python and C++ projects.

## Overview

Anvil is a quality gate tool that can be deployed in various contexts:
- Interactive development
- Git hooks (pre-commit, pre-push)
- CI/CD pipelines
- Manual audits

## Features

- **Multi-Language Support**: Python and C++ (Iteration 2)
- **Extensible Architecture**: Plugin system for adding new validators
- **Flexible Deployment**: Use anywhere in your workflow
- **Smart Filtering**: Historical tracking to optimize test execution
- **Rich Output**: Clear, actionable error messages with suggestions

## Installation

```bash
cd anvil
pip install -e .
```

## Quick Start

```bash
# Run all validators
anvil check

# Run incrementally (only changed files)
anvil check --incremental

# Install git hooks
anvil install-hooks
```

## Documentation

See `docs/` directory for comprehensive documentation:
- USER_GUIDE.md - User guide with examples
- API.md - API documentation for extending Anvil
- CONFIGURATION.md - Configuration reference

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run pre-commit checks
python scripts/pre-commit-check.py
```

## License

Part of the Argos Project.
