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
