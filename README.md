# Argus

> Named after the all-seeing giant from Greek mythology who had a hundred eyes, Argus watches over your applications without ever being noticed—observing everything while remaining completely invisible to the monitored code.

**Argus** is a lightweight, cross-platform monitoring system that provides visibility into application health, performance, and logs. Designed for quick integration with minimal overhead, Argus embodies the principle of non-intrusive monitoring: your applications require no code changes, no special libraries, and no build system modifications.

## Overview

Argus consists of three independent components that work together to provide comprehensive application monitoring:

- **Forge** - CMake build wrapper that captures build events and metadata
- **Gaze** - Runtime inspector daemon that monitors running applications
- **Server** - Central monitoring server with web dashboard and alerting

## Key Features

- **Simple Integration**: Add monitoring in minutes with SDKs
- **Low Overhead**: Less than 5% performance impact
- **Real-Time Monitoring**: Metrics, logs, and threshold-based alerts
- **Non-Intrusive**: Zero code changes or build modifications required
- **Cross-Platform**: Windows, Linux, macOS
- **Single-Server Deployment**: Docker Compose setup

## Quick Start

### Forge - Monitor Your Builds

Wrap your CMake workflow to capture build events:

```bash
# Configure and build
python forge --source-dir . --build-dir ./build

# Build only (if already configured)
python forge --build-dir ./build

# Configure with custom options
python forge --source-dir . --build-dir ./build --cmake-args "-DCMAKE_BUILD_TYPE=Release"
```

### Gaze - Monitor Running Applications

Observe your applications at runtime:

```bash
# Monitor a process by name
python gaze --process myapp

# Monitor with log file tailing
python gaze --process myapp --logfile ./app.log

# Monitor by PID with custom name
python gaze --pid 12345 --app-name MyApplication
```

### Server - Central Dashboard

Deploy the monitoring server:

```bash
cd server
docker-compose up -d
```

Access the dashboard at `http://localhost:3000`

## Selective Test Execution (Phase 1 - NEW!)

Argos now includes **Anvil** for intelligent test execution and **Lens** for test analytics and reporting.

### Quick Start

```bash
# Run tests with a specific rule
cd anvil
anvil execute --rule quick-check

# List available execution rules
anvil rules list

# Show test statistics
anvil stats show --type test --window 20

# Find flaky tests
anvil stats flaky-tests --threshold 0.10

# View execution history
anvil history show --entity "tests/test_example.py::test_func"

# Generate test execution report
cd ../lens
lens report test-execution --format html --output report.html
```

### Available Execution Rules

- **baseline-all-tests**: Run all tests (full baseline)
- **quick-check**: Critical tests only (fast feedback)
- **argos-commit-check**: Smart selection based on failure rates (15% threshold)
- **argos-focus-flaky**: Run flaky tests only (5% failure rate)
- **argos-rerun-failures**: Re-run recently failed tests
- **failed-only**: Re-run tests that failed in last execution
- **forge-only / anvil-only / scout-only / lens-only**: Run specific project tests

### Benefits

- **87-97% faster execution**: Run only relevant tests instead of full suite
- **Automated flaky test detection**: Identify unreliable tests automatically
- **Historical tracking**: Complete execution history in SQLite database
- **Smart selection**: Failure-rate based test selection
- **Beautiful reports**: Interactive HTML reports with Chart.js visualizations

### Documentation

- [Phase 1 Complete Summary](docs/phase-1-complete.md) - Full Phase 1 documentation
- [Lens Implementation Plan](docs/lens-implementation-plan.md) - Roadmap for all phases

## Technology Stack

### Forge & Gaze
- **Python 3.8+** - Cross-platform scripting
- **SQLite** - Local data storage
- **psutil** - System metrics collection

### Server
- **Backend**: FastAPI, Python 3.8+
- **Databases**: InfluxDB (metrics), PostgreSQL (logs, alerts)
- **Frontend**: React with TypeScript, Chart.js, Bootstrap 5
- **Infrastructure**: Docker Compose, HTTPS with Let's Encrypt

## Project Structure

```
argus/
├── forge/                  # CMake build wrapper
├── gaze/                   # Runtime inspector daemon
├── server/                 # Central monitoring server
│   ├── backend/           # FastAPI backend
│   ├── frontend/          # React frontend
│   └── docker-compose.yml # Development setup
├── shared/                # Shared utilities and schemas
├── docs/                  # Documentation
└── README.md             # This file
```

## Documentation

- [Forge Specification](docs/forge-specification.md) - Detailed build wrapper documentation
- [Gaze Specification](docs/gaze-specification.md) - Detailed runtime monitoring documentation
- [Project Organization](docs/project-organization.md) - Project structure and organization
- [Project Description](docs/Argus-Project-Description.md) - Complete project overview

## Design Principles

1. **Non-Intrusive**: Zero modifications required to monitored applications
2. **Transparent**: Applications behave identically with or without monitoring
3. **Simple**: Drop-in replacement for standard commands
4. **Local-First**: Data stored locally with optional server upload
5. **Reliable**: Captures complete information regardless of success or failure

## Data Collected

### Build Events (Forge)
- Configuration metadata (CMake version, generator, compiler)
- Build timing and status
- Complete build output
- Compiler warnings and errors

### Runtime Metrics (Gaze)
- CPU usage percentage
- Memory consumption (RSS)
- Thread count
- Application logs (when specified)

## Retention Policies

- **Local SQLite**: No automatic cleanup, user-managed
- **Server InfluxDB**: 30-day metric retention
- **Server PostgreSQL**: 30-day log retention with automated cleanup

## Development Status

Argus is currently under development. Components are being built in phases:

- **v0.1**: Local data collection (Forge, Gaze with SQLite)
- **v0.2**: Server infrastructure and UI
- **v0.3**: Server integration and data upload
- **v0.4**: Advanced features and production hardening

## License

[To be determined]

## Contributing

[To be determined]

## Support

For questions, issues, or feature requests, please refer to the documentation in the `docs/` directory or open an issue in the project repository.

---

*Argus - Watch everything, change nothing.*
