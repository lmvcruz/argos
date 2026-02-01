# Scout - CI/CD Inspection Tool

Scout is a comprehensive CI/CD inspection and failure analysis tool, part of the Argos ecosystem.

## Features

- **GitHub Actions Integration**: Retrieve and analyze GitHub Actions workflow runs
- **Test Failure Parsing**: Extract and parse test failures from CI logs
- **Failure Pattern Detection**: Identify flaky tests and recurring failures
- **Cross-Platform Analysis**: Compare failures across different platforms
- **Trend Analysis**: Track failure patterns over time
- **Actionable Reports**: Generate clear, actionable failure reports

## Installation

```bash
pip install argos-scout
```

## Quick Start

```bash
# Retrieve logs from latest workflow run
scout logs <workflow-name>

# Analyze a specific run
scout analyze <run-id>

# Detect flaky tests
scout flaky

# Show failure trends
scout trends <workflow-name>
```

## Documentation

See [User Guide](docs/USER_GUIDE.md) for detailed documentation.

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=scout --cov-report=html
```

## License

MIT License - see LICENSE file for details.
