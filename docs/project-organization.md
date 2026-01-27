# Argus - Project Organization

## Overview

Argus is a non-intrusive application monitoring system consisting of three independent applications plus supporting documentation and shared resources. Each component can be developed, tested, and deployed independently.

Named after the all-seeing giant from Greek mythology, Argus watches over applications without being noticed—observing everything while remaining completely invisible to the monitored code.

---

## Project Structure

```
argus/
├── forge/                      # CMake build wrapper
│   ├── forge.py               # Main script
│   ├── requirements.txt       # Python dependencies
│   ├── README.md              # Usage documentation
│   ├── tests/                 # Unit and integration tests
│   └── examples/              # Example usage scripts
│
├── gaze/                       # Runtime inspector daemon
│   ├── gaze.py                # Main script
│   ├── requirements.txt       # Python dependencies
│   ├── README.md              # Usage documentation
│   ├── tests/                 # Unit and integration tests
│   └── examples/              # Example usage scripts
│
├── server/                     # Central monitoring server
│   ├── backend/               # FastAPI backend
│   │   ├── main.py            # FastAPI application
│   │   ├── api/               # API endpoints
│   │   ├── models/            # Database models
│   │   ├── services/          # Business logic
│   │   ├── requirements.txt   # Python dependencies
│   │   └── tests/             # Backend tests
│   │
│   ├── frontend/              # React frontend
│   │   ├── src/               # React source code
│   │   │   ├── components/    # React components
│   │   │   ├── pages/         # Page components
│   │   │   ├── services/      # API clients
│   │   │   └── App.tsx        # Root component
│   │   ├── public/            # Static assets
│   │   ├── package.json       # npm dependencies
│   │   └── tests/             # Frontend tests
│   │
│   ├── docker-compose.yml     # Local development setup
│   └── README.md              # Server setup instructions
│
├── shared/                     # Shared utilities and schemas
│   ├── schemas/               # Database schemas
│   │   ├── sqlite/            # SQLite schemas (forge, gaze)
│   │   ├── postgresql/        # PostgreSQL schemas (server)
│   │   └── influxdb/          # InfluxDB schemas (server)
│   │
│   ├── utils/                 # Shared utility libraries
│   │   ├── timestamp.py       # Timestamp formatting utilities
│   │   ├── database.py        # Database connection helpers
│   │   └── http_client.py     # HTTP client for server communication
│   │
│   └── models/                # Shared data models
│       ├── build_event.py     # Build event data structure
│       ├── log_entry.py       # Log entry data structure
│       └── metric.py          # Performance metric data structure
│
├── docs/                       # Documentation
│   ├── forge-specification.md  # Forge detailed specification
│   ├── gaze-specification.md   # Gaze detailed specification
│   ├── server-specification.md # Server detailed specification (TODO)
│   ├── api-reference.md        # API documentation (TODO)
│   ├── architecture.md         # System architecture (TODO)
│   └── deployment-guide.md     # Production deployment (TODO)
│
└── project-organization.md     # This file
```

---

## Applications

### 1. Forge - Build Wrapper

**Purpose**: Wraps CMake configuration and build processes to capture build events and metadata.

**Technology**: Python 3.8+

**Key Features**:
- Executes `cmake <source-dir>` (configuration step)
- Executes `cmake --build <build-dir>` (build step)
- Captures complete output, timing, and results
- Stores data in local SQLite database
- Optional server upload (v0.3+)

**Database**: `~/.argus/argus_builds.db` (SQLite)

**Tables**:
- `configurations` - CMake configuration records
- `builds` - Build execution records

**Entry Point**: `python forge/forge.py`

**Dependencies**:
- Python standard library (subprocess, sqlite3, argparse, pathlib)
- Optional: requests/httpx (for server communication)

---

### 2. Gaze - Runtime Inspector Daemon

**Purpose**: Monitors running processes, collecting performance metrics and log entries in real-time.

**Technology**: Python 3.8+

**Key Features**:
- Attaches to processes by name or PID
- Collects CPU, memory, thread count every N seconds
- Tails log files in real-time
- Detects process termination and exits gracefully
- Stores data in local SQLite database
- Optional server upload (v0.3+)

**Database**: `~/.argus/argus_runtime.db` (SQLite)

**Tables**:
- `performance_metrics` - CPU/memory/thread snapshots
- `log_entries` - Captured log lines
- `process_events` - Process lifecycle events

**Entry Point**: `python gaze/gaze.py`

**Dependencies**:
- `psutil` - Process monitoring
- Python standard library (sqlite3, argparse, pathlib, threading)
- Optional: requests/httpx (for server communication)
- Optional: watchdog (advanced file watching)

---

### 3. Server - Central Monitoring Platform

**Purpose**: Centralized data aggregation, storage, and visualization for all monitored applications.

**Technology**:
- Backend: Python 3.8+ with FastAPI
- Frontend: React with TypeScript
- Databases: PostgreSQL (events), InfluxDB (time-series metrics)

**Key Features**:
- RESTful API for data ingestion (`POST /api/ingest`)
- RESTful API for data retrieval (`GET /api/builds`, `/api/logs`, `/api/metrics`)
- Web dashboard with build history, log viewer, performance charts
- Multi-application monitoring
- Alerting system (v0.4+)

**Databases**:
- PostgreSQL: `argus_db` - Stores build events, log entries, process events
- InfluxDB: `argus_metrics` bucket - Stores time-series performance metrics

**Entry Points**:
- Backend: `uvicorn server/backend/main:app`
- Frontend: `npm start` (dev) or `npm run build` (prod)

**Dependencies**:
- Backend: FastAPI, uvicorn, psycopg2, influxdb-client, pydantic
- Frontend: React, TypeScript, Bootstrap, axios, react-query, recharts

---

## Shared Resources

### Schemas (`shared/schemas/`)

**Purpose**: Centralized database schema definitions for consistency across components.

**Contents**:
- **SQLite schemas**: SQL scripts for forge and gaze local databases
- **PostgreSQL schemas**: SQL scripts for server event database
- **InfluxDB schemas**: Bucket and measurement definitions

**Usage**: Referenced during development and testing; used for database initialization

---

### Utilities (`shared/utils/`)

**Purpose**: Common functionality used across multiple components.

**Examples**:
- Timestamp formatting (ISO 8601 with millisecond precision)
- Database connection helpers
- HTTP client configuration for server communication
- Hostname detection
- Project name parsing from CMakeLists.txt

**Language**: Python (for use in forge, gaze, server backend)

---

### Models (`shared/models/`)

**Purpose**: Shared data structures for consistency between client tools and server.

**Examples**:
- Build event structure (used by forge → server)
- Log entry structure (used by gaze → server)
- Performance metric structure (used by gaze → server)
- API request/response schemas

**Language**: Python (Pydantic models for validation)

---

## Documentation (`docs/`)

**Purpose**: Comprehensive documentation for all Argus components.

**Current Documents**:
- `forge-specification.md` - Complete forge specification ✅
- `gaze-specification.md` - Complete gaze specification ✅
- `project-organization.md` - This document ✅

**Planned Documents**:
- `server-specification.md` - Server architecture and API
- `api-reference.md` - Complete API documentation with examples
- `architecture.md` - System architecture, data flow, deployment diagrams
- `deployment-guide.md` - Production deployment instructions
- `development-guide.md` - Developer setup and contribution guidelines

---

## Development Workflow

### Independent Development

Each application can be developed independently:

```bash
# Develop forge
cd argus/forge
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python forge.py --help

# Develop gaze
cd argus/gaze
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python gaze.py --help

# Develop server backend
cd argus/server/backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Develop server frontend
cd argus/server/frontend
npm install
npm start
```

### Integration Testing

Full stack testing requires all components:

```bash
# 1. Start server infrastructure
cd argus/server
docker-compose up -d  # Starts PostgreSQL, InfluxDB, backend, frontend

# 2. Build a test project with forge
cd /path/to/test-project
python /path/to/argus/forge/forge.py --source-dir . --build-dir ./build --server http://localhost:8000

# 3. Run the test application with gaze
./build/myapp &
python /path/to/argus/gaze/gaze.py --process myapp --logfile myapp.log --server http://localhost:8000

# 4. View results in web dashboard
open http://localhost:3000
```

---

## Version Roadmap

### v0.1 - Forge (Local-Only Build Monitoring)
- **Components**: forge only
- **Dependencies**: None (standalone)
- **Database**: SQLite (`argus_builds.db`)
- **Status**: Specification complete, ready for implementation

### v0.2 - Gaze (Local-Only Runtime Monitoring)
- **Components**: forge, gaze
- **Dependencies**: forge and gaze are independent
- **Database**: SQLite (`argus_builds.db`, `argus_runtime.db`)
- **Status**: Specification complete, ready for implementation

### v0.3 - Server (Centralized Monitoring)
- **Components**: forge, gaze, server
- **Dependencies**: forge and gaze POST to server
- **Databases**: SQLite (local caching), PostgreSQL, InfluxDB
- **Status**: Planning phase

### v0.4 - Advanced Features
- **Components**: All components enhanced
- **New Features**: Alerting, custom dashboards, log correlation, advanced charts
- **Status**: Planning phase

---

## Deployment Scenarios

### Scenario 1: Local Development (v0.1-v0.2)

**Use Case**: Individual developer monitoring their own builds and applications

**Components**:
- forge (standalone)
- gaze (standalone)

**Databases**:
- SQLite on developer's machine

**Workflow**:
```bash
python forge --source-dir . --build-dir ./build
./build/myapp &
python gaze --process myapp --logfile myapp.log
```

---

### Scenario 2: Team Server (v0.3+)

**Use Case**: Team sharing monitoring data via central server

**Components**:
- forge (on developer machines)
- gaze (on developer machines or CI/CD runners)
- server (on team server)

**Databases**:
- SQLite on each machine (local caching)
- PostgreSQL + InfluxDB on server

**Workflow**:
```bash
# Developer machines
python forge --source-dir . --build-dir ./build --server https://argus.team.com
python gaze --process myapp --logfile myapp.log --server https://argus.team.com

# View on shared dashboard
open https://argus.team.com
```

---

### Scenario 3: Production Monitoring (v0.3+)

**Use Case**: Monitoring production applications

**Components**:
- gaze (on production servers)
- server (on monitoring infrastructure)

**Databases**:
- PostgreSQL + InfluxDB (production-grade setup)

**Workflow**:
```bash
# Production server (as systemd service)
systemctl start gaze-myapp

# Monitoring team
open https://argus.company.com
```

---

## Testing Strategy

### Unit Tests

**Location**: `<component>/tests/unit/`

**Focus**: Individual functions, data models, utilities

**Example**:
- `forge/tests/unit/test_project_name_detection.py`
- `gaze/tests/unit/test_metric_collection.py`
- `server/backend/tests/unit/test_api_models.py`

---

### Integration Tests

**Location**: `<component>/tests/integration/`

**Focus**: Component interactions, database operations, API calls

**Example**:
- `forge/tests/integration/test_cmake_build.py`
- `gaze/tests/integration/test_process_monitoring.py`
- `server/backend/tests/integration/test_api_endpoints.py`

---

### End-to-End Tests

**Location**: `argus/tests/e2e/`

**Focus**: Full workflow from forge/gaze → server → dashboard

**Example**:
- Build project with forge, verify server receives data
- Monitor process with gaze, verify dashboard displays metrics
- Test complete workflow: build → run → monitor → visualize

---

## Contributing Guidelines

### Development Principles

1. **Independent Components**: Each application must be self-contained
2. **Non-Intrusive**: Never require monitored applications to change
3. **Local-First**: Always support local-only operation
4. **Test Coverage**: Minimum 80% code coverage for all components
5. **Documentation**: Update specifications when changing behavior

### Code Standards

- **Python**: PEP 8 compliance, type hints, docstrings
- **TypeScript**: ESLint + Prettier, strict mode
- **SQL**: Consistent naming (snake_case), indexed foreign keys

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Update relevant documentation
4. Submit PR with clear description
5. Pass CI checks (tests, linting, type checking)
6. Obtain code review approval

---

## License

**TODO**: Specify license (MIT, Apache 2.0, etc.)

---

**Version**: 1.0.0
**Last Updated**: 2026-01-27
**Maintained By**: [Project Team/Organization]
