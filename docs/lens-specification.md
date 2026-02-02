# Lens Specification

**Version:** 1.0
**Last Updated:** February 1, 2026
**Status:** Draft

## Overview

Lens is a comprehensive build data visualization, analysis, and monitoring tool designed to provide insights into build performance, code quality metrics, and execution patterns across different environments. It operates in two modes (file-based and GUI-based) and manages multiple execution spaces (local, CI, server) with environment-specific capabilities.

### Purpose

Lens enables developers and teams to:
- Visualize build and code analysis data from Forge, Anvil, and Scout
- Compare builds and code scans across different executions
- Monitor performance trends and identify bottlenecks
- Analyze execution logs and debug failures
- Generate reports for stakeholders
- Track quality metrics over time

### Key Principles

1. **Multi-Mode Operation**: Support both headless (file-based) and interactive (GUI) workflows
2. **Space Awareness**: Adapt behavior based on execution environment (local, CI, server)
3. **Separation of Concerns**: Clear separation between frontend UI and backend operations
4. **Data Agnostic**: Work with data from multiple tools (Forge, Anvil, Scout)
5. **Extensibility**: Plugin architecture for custom visualizations and analyses

---

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Lens System                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌─────────────────┐           ┌─────────────────┐          │
│  │   File-Based    │           │   GUI-Based     │          │
│  │      Mode       │           │      Mode       │          │
│  └────────┬────────┘           └────────┬────────┘          │
│           │                             │                    │
│           └──────────┬──────────────────┘                    │
│                      │                                       │
│           ┌──────────▼──────────┐                            │
│           │   Lens Core Engine  │                            │
│           │  - Space Manager    │                            │
│           │  - Execution Engine │                            │
│           │  - Data Aggregator  │                            │
│           │  - Comparison Engine│                            │
│           └──────────┬──────────┘                            │
│                      │                                       │
│      ┌───────────────┼───────────────┐                       │
│      │               │               │                       │
│  ┌───▼────┐    ┌────▼─────┐    ┌───▼────┐                  │
│  │ Local  │    │    CI    │    │ Server │                   │
│  │ Space  │    │  Space   │    │ Space  │                   │
│  └───┬────┘    └────┬─────┘    └───┬────┘                  │
│      │              │              │                         │
│      └──────────────┼──────────────┘                         │
│                     │                                        │
│           ┌─────────▼─────────┐                              │
│           │  Data Connectors  │                              │
│           │  - Forge DB       │                              │
│           │  - Anvil DB       │                              │
│           │  - Scout DB       │                              │
│           │  - Log Files      │                              │
│           └───────────────────┘                              │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### GUI Mode (Web-Based)

```
┌─────────────────────────────────────────────────────────────┐
│                     Lens GUI Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (React/Vue)                                         │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  - Dashboard Views                                   │    │
│  │  - Build Comparison UI                               │    │
│  │  - Scan Comparison UI                                │    │
│  │  - Log Viewer                                        │    │
│  │  - Space Configuration                               │    │
│  │  - Interactive Charts (Chart.js/D3.js)              │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │ REST/WebSocket API                 │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Backend (FastAPI/Flask)                            │    │
│  │  ┌──────────────────────────────────────────────┐   │    │
│  │  │  API Layer                                   │   │    │
│  │  │  - /api/spaces                               │   │    │
│  │  │  - /api/builds                               │   │    │
│  │  │  - /api/scans                                │   │    │
│  │  │  - /api/comparisons                          │   │    │
│  │  │  - /api/logs                                 │   │    │
│  │  │  - /ws/realtime (WebSocket)                  │   │    │
│  │  └──────────────────┬───────────────────────────┘   │    │
│  │                     │                                │    │
│  │  ┌──────────────────▼───────────────────────────┐   │    │
│  │  │  Business Logic Layer                        │   │    │
│  │  │  - Space Manager                             │   │    │
│  │  │  - Build Executor                            │   │    │
│  │  │  - Scan Executor                             │   │    │
│  │  │  - Comparison Engine                         │   │    │
│  │  │  - Log Analyzer                              │   │    │
│  │  └──────────────────┬───────────────────────────┘   │    │
│  │                     │                                │    │
│  │  ┌──────────────────▼───────────────────────────┐   │    │
│  │  │  Data Access Layer                           │   │    │
│  │  │  - Database Connectors                       │   │    │
│  │  │  - File System Access                        │   │    │
│  │  │  - Cache Manager                             │   │    │
│  │  └──────────────────────────────────────────────┘   │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Operating Modes

### 1. File-Based Mode

**Description**: Headless operation using configuration files and command-line interface.

**Use Cases**:
- CI/CD pipeline integration
- Automated report generation
- Batch processing
- Scheduled analysis jobs

**Configuration**:
```yaml
# lens-config.yaml
mode: file-based
spaces:
  - name: local
    type: local
    forge_db: /path/to/forge.db
    anvil_db: /path/to/anvil.db
    scout_db: /path/to/scout.db

  - name: ci
    type: ci
    forge_db: ${CI_FORGE_DB}
    anvil_db: ${CI_ANVIL_DB}
    build_executor: github-actions
    result_parser: github-actions-parser

operations:
  - type: build-comparison
    space: local
    build_ids: [123, 124]
    output: build-comparison.html

  - type: scan-comparison
    space: ci
    scan_ids: [456, 457]
    output: scan-comparison.json
```

**CLI Commands**:
```bash
# Run build in specified space
lens build --space local --config build-config.yaml

# Compare two builds
lens compare builds --ids 123,124 --output comparison.html

# Run code scan
lens scan --space ci --config scan-config.yaml

# Compare scans
lens compare scans --ids 456,457 --format json

# Analyze logs (comparison only, no execution)
lens analyze logs --build-id 123 --output log-analysis.json

# Generate report
lens report --template performance --period last-7-days
```

### 2. GUI-Based Mode

**Description**: Interactive web-based interface for visual analysis and configuration.

**Use Cases**:
- Interactive build analysis
- Visual debugging
- Ad-hoc comparisons
- Real-time monitoring
- Team collaboration

**Setup**:
```bash
# Start Lens web server
lens serve --port 8080 --host 0.0.0.0

# Start with configuration file
lens serve --config lens-config.yaml

# Start with specific space
lens serve --space local
```

**Features**:
- Interactive dashboards
- Drag-and-drop comparison
- Real-time build monitoring
- Visual log analysis
- Custom report builder
- Space configuration UI

---

## Space Management

### Space Definition

A **Space** represents an execution environment with specific characteristics:

```python
@dataclass
class Space:
    """Represents an execution environment."""
    name: str
    type: SpaceType  # LOCAL, CI, SERVER
    config: SpaceConfig
    executor: Executor
    parser: ResultParser
```

### Space Types

#### 1. Local Space

**Characteristics**:
- Direct file system access
- Local database connections
- Synchronous execution
- Interactive debugging

**Configuration**:
```yaml
spaces:
  local:
    type: local
    forge:
      database: /home/user/.forge/forge.db
      build_dir: /home/user/projects/myapp/build
    anvil:
      database: /home/user/.anvil/anvil.db
    scout:
      database: /home/user/.scout/scout.db
    executor:
      type: direct
      cmake_path: /usr/bin/cmake
      timeout: 3600
    parser:
      type: local
      log_format: text
```

#### 2. CI Space

**Characteristics**:
- Remote execution via CI system
- Asynchronous operation
- API-based communication
- Artifact retrieval

**Configuration**:
```yaml
spaces:
  ci:
    type: ci
    platform: github-actions  # or jenkins, gitlab-ci, etc.
    connection:
      url: https://api.github.com
      token: ${GITHUB_TOKEN}
      repository: owner/repo
    executor:
      type: github-actions
      workflow: build.yml
      ref: main
    parser:
      type: github-actions
      artifact_name: build-results
      log_format: github
```

#### 3. Server Space

**Characteristics**:
- Remote server execution
- SSH/API access
- Distributed builds
- Centralized storage

**Configuration**:
```yaml
spaces:
  server:
    type: server
    connection:
      host: build-server.company.com
      port: 22
      user: buildbot
      key_file: ~/.ssh/buildbot_key
    executor:
      type: ssh
      working_dir: /var/builds
      environment:
        CC: gcc-11
        CXX: g++-11
    parser:
      type: remote
      log_location: /var/builds/logs
```

### Space Operations

Each space implements the following operations with space-specific behavior:

```python
class SpaceOperations(ABC):
    """Abstract interface for space operations."""

    @abstractmethod
    async def execute_build(self, config: BuildConfig) -> BuildResult:
        """Execute a build in this space."""
        pass

    @abstractmethod
    async def execute_scan(self, config: ScanConfig) -> ScanResult:
        """Execute a code scan in this space."""
        pass

    @abstractmethod
    async def fetch_logs(self, build_id: str) -> BuildLogs:
        """Fetch build logs for analysis."""
        pass

    @abstractmethod
    async def compare_builds(self, build_ids: List[str]) -> BuildComparison:
        """Compare multiple builds."""
        pass

    @abstractmethod
    async def compare_scans(self, scan_ids: List[str]) -> ScanComparison:
        """Compare multiple scans."""
        pass
```

---

## Core Capabilities

### 1. Build Execution

**Description**: Execute builds in configured spaces.

**Features**:
- Space-aware execution
- Configuration templating
- Environment variable management
- Artifact collection
- Real-time progress tracking

**Example**:
```python
# Execute build in local space
result = await lens.execute_build(
    space="local",
    project_path="/path/to/project",
    config={
        "generator": "Ninja",
        "build_type": "Release",
        "targets": ["all"]
    }
)

# Execute build in CI space
result = await lens.execute_build(
    space="ci",
    workflow="build.yml",
    ref="main",
    inputs={
        "build_type": "Release",
        "run_tests": True
    }
)
```

### 2. Build Comparison

**Description**: Compare multiple build executions to identify differences.

**Comparison Dimensions**:
- Build time
- Compilation warnings/errors
- Target success rates
- Resource usage (CPU, memory)
- Generated artifacts
- Configuration differences

**Example**:
```python
comparison = await lens.compare_builds(
    space="local",
    build_ids=["build-123", "build-124"],
    metrics=[
        "total_time",
        "warning_count",
        "target_times",
        "peak_memory"
    ]
)

# Output:
{
    "summary": {
        "builds_compared": 2,
        "significant_differences": 3
    },
    "metrics": {
        "total_time": {
            "build-123": 45.2,
            "build-124": 38.7,
            "difference": -6.5,
            "percentage": -14.4
        },
        "warning_count": {
            "build-123": 12,
            "build-124": 8,
            "difference": -4
        }
    },
    "details": {
        "target_differences": [...]
    }
}
```

### 3. Code Scan Execution

**Description**: Execute code quality scans using Anvil.

**Features**:
- Multi-validator execution
- Incremental scanning
- Parallel execution
- Result aggregation

**Example**:
```python
result = await lens.execute_scan(
    space="local",
    project_path="/path/to/project",
    validators=["flake8", "pylint", "black"],
    mode="incremental"
)
```

### 4. Scan Comparison

**Description**: Compare code scan results across executions.

**Comparison Dimensions**:
- Issue count by severity
- New vs fixed issues
- Validator-specific metrics
- File-level changes
- Trend analysis

**Example**:
```python
comparison = await lens.compare_scans(
    space="local",
    scan_ids=["scan-456", "scan-457"],
    grouping="by_severity"
)

# Output:
{
    "summary": {
        "scans_compared": 2,
        "new_issues": 5,
        "fixed_issues": 3,
        "net_change": +2
    },
    "by_severity": {
        "error": {"new": 2, "fixed": 1, "net": +1},
        "warning": {"new": 3, "fixed": 2, "net": +1}
    },
    "by_validator": {...},
    "by_file": {...}
}
```

### 5. Log Analysis

**Description**: Analyze execution logs without running builds/scans.

**Features**:
- Pattern detection
- Error extraction
- Performance profiling
- Timeline visualization
- Comparison across executions

**Example**:
```python
analysis = await lens.analyze_logs(
    space="ci",
    build_id="build-789",
    patterns=[
        r"error:",
        r"warning:",
        r"time elapsed: ([\d.]+)s"
    ]
)

# Compare logs from different builds
comparison = await lens.compare_logs(
    space="ci",
    build_ids=["build-789", "build-790"],
    focus="compilation_time"
)
```

### 6. Selective Execution (NEW)

**Description**: Execute tests/scans selectively based on intelligent criteria to optimize validation time while maintaining quality.

**Motivation**: Large projects like Argos benefit from selective execution to balance thorough validation with developer velocity.

**Execution Criteria**:

1. **Run All** (Baseline)
   - Execute all tests/scans in the project
   - Used for comprehensive validation before releases
   - Establishes baseline for comparison

2. **Run Entities of Group**
   - Execute specific subset based on flexible grouping
   - Groups can be:
     - Folders (e.g., `forge/tests`, `anvil/storage`)
     - Files (e.g., `test_parser.py`, `test_models.py`)
     - Patterns (e.g., `**/test_*_integration.py`)
     - Mixed combinations

3. **Run Entities that Failed in Last N Executions**
   - Focus on tests/scans that have recently failed
   - Configurable window (N executions)
   - Prioritize fixing known issues

4. **Run Entities with Failure Rate > X% in Last N Executions**
   - Identify and focus on flaky or problematic tests/scans
   - Configurable threshold (X%) and window (N)
   - Statistical analysis of failure patterns

**Features**:
- Rule configuration via YAML or UI
- Historical execution tracking
- Failure rate calculation
- Statistics aggregation
- Result persistence
- Trend visualization

**Example - File-based**:
```bash
# Run all tests (baseline)
lens execute tests \
  --space local \
  --project argos \
  --criteria all

# Run specific group
lens execute tests \
  --space local \
  --project argos \
  --criteria group \
  --group "forge/tests,anvil/tests"

# Run tests that failed in last 5 executions
lens execute tests \
  --space local \
  --project argos \
  --criteria failed-in-last \
  --window 5

# Run tests with >20% failure rate in last 10 executions
lens execute tests \
  --space local \
  --project argos \
  --criteria failure-rate \
  --threshold 20 \
  --window 10
```

**Example - Programmatic**:
```python
# Define execution rule
rule = ExecutionRule(
    name="focus-on-failures",
    criteria=ExecutionCriteria.FAILURE_RATE,
    threshold=15.0,  # 15% failure rate
    window=20,  # last 20 executions
    groups=["forge/tests", "anvil/tests"]
)

# Execute with rule
result = await lens.execute_with_rule(
    space="local",
    rule=rule,
    executor_type="pytest"
)

# Get statistics
stats = await lens.get_execution_stats(
    space="local",
    window=50,
    grouping="by_file"
)
```

**Rule Configuration (YAML)**:
```yaml
# selective-execution-rules.yaml
rules:
  - name: daily-commit-checks
    enabled: true
    criteria: failure-rate
    threshold: 10.0
    window: 10
    groups:
      - "forge/tests"
      - "anvil/tests"
      - "scout/tests"

  - name: pre-release-validation
    enabled: true
    criteria: all
    # No groups - run everything

  - name: focus-flaky-tests
    enabled: true
    criteria: failure-rate
    threshold: 5.0
    window: 30
    groups:
      - "**/test_*_integration.py"

  - name: rerun-recent-failures
    enabled: true
    criteria: failed-in-last
    window: 5
    groups:
      - "forge/**"
```

**Statistics Engine**:
```python
@dataclass
class ExecutionStatistics:
    """Statistics for test/scan executions."""
    entity_id: str  # test or scan identifier
    total_runs: int
    passed: int
    failed: int
    skipped: int
    failure_rate: float
    avg_duration: float
    last_failure: Optional[datetime]
    failure_trend: Trend  # IMPROVING, DEGRADING, STABLE

@dataclass
class GroupStatistics:
    """Statistics for group of entities."""
    group_name: str
    total_entities: int
    entity_stats: List[ExecutionStatistics]
    group_failure_rate: float
    most_flaky: List[str]  # entity IDs
    recently_fixed: List[str]
```

---

## Data Models

### Build Execution Result

```python
@dataclass
class BuildResult:
    """Result of a build execution."""
    build_id: str
    space: str
    timestamp: datetime
    status: BuildStatus  # SUCCESS, FAILURE, TIMEOUT
    duration: float
    targets: List[TargetResult]
    warnings: List[Warning]
    errors: List[Error]
    artifacts: List[Artifact]
    metadata: Dict[str, Any]

@dataclass
class TargetResult:
    """Result for individual build target."""
    name: str
    status: BuildStatus
    duration: float
    command: str
    output: str
```

### Scan Execution Result

```python
@dataclass
class ScanResult:
    """Result of a code scan execution."""
    scan_id: str
    space: str
    timestamp: datetime
    validators: List[ValidatorResult]
    summary: ScanSummary
    files_scanned: int
    total_issues: int

@dataclass
class ValidatorResult:
    """Result from individual validator."""
    name: str
    status: ValidationStatus
    duration: float
    issues: List[Issue]
    files_checked: int
```

### Comparison Result

```python
@dataclass
class BuildComparison:
    """Comparison between multiple builds."""
    comparison_id: str
    build_ids: List[str]
    timestamp: datetime
    summary: ComparisonSummary
    metrics: Dict[str, MetricComparison]
    target_comparisons: List[TargetComparison]

@dataclass
class MetricComparison:
    """Comparison of a specific metric."""
    metric_name: str
    values: Dict[str, float]  # build_id -> value
    differences: Dict[str, float]  # build_id -> diff from baseline
    trend: Trend  # IMPROVING, DEGRADING, STABLE

@dataclass
class ExecutionRule:
    """Rule for selective execution."""
    name: str
    criteria: ExecutionCriteria  # ALL, GROUP, FAILED_IN_LAST, FAILURE_RATE
    enabled: bool = True
    threshold: Optional[float] = None  # For FAILURE_RATE
    window: Optional[int] = None  # Number of past executions to consider
    groups: Optional[List[str]] = None  # Folders, files, patterns

@dataclass
class ExecutionHistory:
    """Historical record of an execution."""
    execution_id: str
    entity_id: str  # test or scan identifier
    timestamp: datetime
    status: ExecutionStatus  # PASSED, FAILED, SKIPPED, ERROR
    duration: float
    space: str
    metadata: Dict[str, Any]
```

---

## API Specification

### REST API Endpoints

#### Space Management

```
GET    /api/spaces                    # List all configured spaces
GET    /api/spaces/{name}             # Get space details
POST   /api/spaces                    # Create new space
PUT    /api/spaces/{name}             # Update space configuration
DELETE /api/spaces/{name}             # Delete space
POST   /api/spaces/{name}/test        # Test space connection
```

#### Build Operations

```
POST   /api/builds                    # Execute new build
GET    /api/builds                    # List builds
GET    /api/builds/{id}               # Get build details
DELETE /api/builds/{id}               # Delete build record
GET    /api/builds/{id}/logs          # Get build logs
GET    /api/builds/{id}/artifacts     # List build artifacts
POST   /api/builds/compare            # Compare builds
```

#### Scan Operations

```
POST   /api/scans                     # Execute new scan
GET    /api/scans                     # List scans
GET    /api/scans/{id}                # Get scan details
DELETE /api/scans/{id}                # Delete scan record
GET    /api/scans/{id}/issues         # Get scan issues
POST   /api/scans/compare             # Compare scans
```

#### Log Operations

```
GET    /api/logs/{build_id}           # Get logs for build
POST   /api/logs/analyze              # Analyze logs
POST   /api/logs/compare              # Compare logs
GET    /api/logs/{build_id}/download  # Download raw logs
```

#### Comparison Operations

```
POST   /api/comparisons/builds        # Create build comparison
POST   /api/comparisons/scans         # Create scan comparison
POST   /api/comparisons/logs          # Create log comparison
GET    /api/comparisons/{id}          # Get comparison results
DELETE /api/comparisons/{id}          # Delete comparison
```

#### Selective Execution Operations (NEW)

```
POST   /api/rules                     # Create execution rule
GET    /api/rules                     # List all rules
GET    /api/rules/{id}                # Get rule details
PUT    /api/rules/{id}                # Update rule
DELETE /api/rules/{id}                # Delete rule
POST   /api/rules/{id}/execute        # Execute with specific rule

POST   /api/execute                   # Execute with criteria
GET    /api/executions                # List execution history
GET    /api/executions/{id}           # Get execution details
GET    /api/executions/{id}/results   # Get execution results

GET    /api/statistics                # Get overall statistics
GET    /api/statistics/entity/{id}    # Get entity-specific stats
GET    /api/statistics/group/{name}   # Get group statistics
POST   /api/statistics/calculate      # Recalculate statistics
```

### WebSocket API

```
WS     /ws/builds/{id}                # Real-time build updates
WS     /ws/scans/{id}                 # Real-time scan updates
WS     /ws/spaces/{name}              # Space status updates
WS     /ws/executions/{id}            # Real-time execution updates (NEW)
WS     /ws/statistics                 # Real-time statistics updates (NEW)
```

---

## Configuration Files

### Main Configuration (lens-config.yaml)

```yaml
# Lens Configuration
version: 1.0
mode: gui  # or file-based

# Server settings (GUI mode)
server:
  host: 0.0.0.0
  port: 8080
  debug: false
  workers: 4

# Database settings
database:
  type: sqlite  # or postgresql
  path: ~/.lens/lens.db
  # For PostgreSQL:
  # host: localhost
  # port: 5432
  # name: lens
  # user: lens
  # password: ${DB_PASSWORD}

# Space definitions
spaces:
  - name: local
    type: local
    enabled: true
    config:
      forge_db: /path/to/forge.db
      anvil_db: /path/to/anvil.db
      scout_db: /path/to/scout.db

  - name: ci-github
    type: ci
    enabled: true
    platform: github-actions
    config:
      url: https://api.github.com
      token: ${GITHUB_TOKEN}
      repository: owner/repo

  - name: build-server
    type: server
    enabled: false
    config:
      host: build.company.com
      port: 22
      user: buildbot
      key_file: ~/.ssh/buildbot_key

# Default settings
defaults:
  space: local
  timeout: 3600
  artifacts_retention_days: 30

# Visualization settings
visualization:
  theme: dark  # or light
  chart_library: plotly  # or matplotlib
  export_formats: [html, png, pdf, json]

# Notification settings
notifications:
  enabled: false
  channels:
    - type: email
      recipients: [team@company.com]
    - type: slack
      webhook_url: ${SLACK_WEBHOOK}

# Selective execution settings (NEW)
selective_execution:
  enabled: true
  default_rule: daily-commit-checks
  history_retention_days: 90
  statistics_update_interval: 300  # seconds
  rules_file: ~/.lens/rules.yaml
```

### Build Configuration (build-config.yaml)

```yaml
# Build Configuration for Lens
project:
  name: myapp
  path: /path/to/project

build:
  generator: Ninja
  build_type: Release
  source_dir: .
  build_dir: build

  options:
    CMAKE_CXX_COMPILER: g++
    CMAKE_C_COMPILER: gcc
    BUILD_TESTING: ON

  targets:
    - all
    - test

  parallel_jobs: 8
  timeout: 1800

  artifacts:
    - pattern: "build/*.so"
      destination: artifacts/libs
    - pattern: "build/bin/*"
      destination: artifacts/bin
```

### Scan Configuration (scan-config.yaml)

```yaml
# Scan Configuration for Lens
project:
  name: myapp
  path: /path/to/project

scan:
  mode: incremental  # or full
  language: python

  validators:
    - name: flake8
      enabled: true
      config:
        max_line_length: 100

    - name: pylint
      enabled: true
      config:
        disable: [C0111, C0103]

    - name: black
      enabled: true
      config:
        check: true

  exclude_patterns:
    - "*/tests/*"
    - "*/venv/*"
    - "*.pyc"

### Execution Rule Configuration (execution-rules.yaml) (NEW)

```yaml
# Execution Rules Configuration for Selective Execution
version: 1.0

# Global settings
settings:
  history_retention: 90  # days
  default_window: 20
  default_threshold: 10.0

# Execution rules
rules:
  - name: daily-commit-checks
    description: Quick checks for daily commits
    enabled: true
    criteria: failure-rate
    threshold: 10.0
    window: 10
    groups:
      - "forge/tests"
      - "anvil/tests"
      - "scout/tests"
    executor:
      type: pytest
      options:
        verbose: true
        capture: no

  - name: pre-release-full-validation
    description: Comprehensive validation before releases
    enabled: true
    criteria: all
    executor:
      type: pytest
      options:
        verbose: true
        coverage: true

  - name: focus-flaky-tests
    description: Target tests with >5% failure rate
    enabled: true
    criteria: failure-rate
    threshold: 5.0
    window: 30
    groups:
      - "**/test_*_integration.py"
      - "**/test_*_e2e.py"

  - name: rerun-recent-failures
    description: Rerun tests that failed in last 5 runs
    enabled: true
    criteria: failed-in-last
    window: 5
    groups:
      - "forge/**"
      - "anvil/**"

  - name: coverage-critical-modules
    description: Coverage check for critical modules
    enabled: true
    criteria: group
    groups:
      - "forge/models"
      - "anvil/storage"
      - "scout/analysis"
    executor:
      type: pytest-cov
      options:
        cov-report: html
        cov-fail-under: 90

  - name: lint-changed-files
    description: Lint only recently changed files
    enabled: true
    criteria: group
    groups:
      - "${CHANGED_FILES}"  # Dynamically populated
    executor:
      type: flake8
      options:
        max-line-length: 100
```

---

## User Interface (GUI Mode)

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Lens Dashboard                                    [User] ⚙  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Spaces: [Local ▼] [CI] [Server]                            │
│                                                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐          │
│  │   Builds    │  │    Scans    │  │    Logs     │          │
│  │             │  │             │  │             │          │
│  │   [Run]     │  │   [Run]     │  │  [Analyze]  │          │
│  └─────────────┘  └─────────────┘  └─────────────┘          │
│                                                               │
│  Recent Activity                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ build-123  ✓  Release build     45.2s    2 hours ago│    │
│  │ scan-456   ✓  Python scan       12.3s    3 hours ago│    │
│  │ build-124  ✗  Debug build       38.1s    5 hours ago│    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  Performance Trends                                           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │         [Chart: Build Time Over Last 7 Days]        │    │
│  │                                                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Build Comparison View

```
┌─────────────────────────────────────────────────────────────┐
│  Compare Builds                                    [Export]  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Select Builds:                                               │
│  ┌─────────────┐  ┌─────────────┐                           │
│  │ build-123   │  │ build-124   │  [+ Add]                  │
│  │ 2h ago      │  │ 5h ago      │                           │
│  └─────────────┘  └─────────────┘                           │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ Metric          build-123    build-124    Δ         │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ Total Time      45.2s        38.7s        -6.5s ✓   │    │
│  │ Warnings        12           8            -4 ✓      │    │
│  │ Errors          0            1            +1 ✗      │    │
│  │ Targets OK      25/25        24/25        -1 ✗      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  Target-Level Comparison                                      │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ [Chart: Side-by-side target build times]            │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Technology Stack

### Backend

- **Framework**: FastAPI (primary) or Flask
- **Database**: SQLite (development), PostgreSQL (production)
- **ORM**: SQLAlchemy
- **Task Queue**: Celery (for async operations)
- **WebSocket**: FastAPI WebSocket or Flask-SocketIO
- **Visualization**: Matplotlib, Plotly
- **Testing**: pytest, pytest-asyncio

### Frontend

- **Framework**: React (primary) or Vue.js
- **UI Library**: Material-UI or Ant Design
- **Charts**: Chart.js or D3.js
- **State Management**: Redux or Vuex
- **HTTP Client**: Axios
- **WebSocket**: Socket.IO client
- **Testing**: Jest, React Testing Library

### Infrastructure

- **Web Server**: Uvicorn (FastAPI) or Gunicorn (Flask)
- **Reverse Proxy**: Nginx (production)
- **Container**: Docker
- **Orchestration**: Docker Compose (development), Kubernetes (production)

---

## File Structure

```
lens/
├── backend/
│   ├── __init__.py
│   ├── __main__.py
│   ├── app.py                  # FastAPI application
│   ├── config.py               # Configuration management
│   ├── api/
│   │   ├── __init__.py
│   │   ├── spaces.py           # Space endpoints
│   │   ├── builds.py           # Build endpoints
│   │   ├── scans.py            # Scan endpoints
│   │   ├── logs.py             # Log endpoints
│   │   └── comparisons.py      # Comparison endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── space_manager.py    # Space management
│   │   ├── executor.py         # Build/scan execution
│   │   ├── comparator.py       # Comparison engine
│   │   ├── analyzer.py         # Log analysis
│   │   ├── rule_engine.py      # Selective execution rules (NEW)
│   │   └── statistics.py       # Statistics calculation (NEW)
│   ├── spaces/
│   │   ├── __init__.py
│   │   ├── base.py             # Abstract space interface
│   │   ├── local.py            # Local space implementation
│   │   ├── ci.py               # CI space implementation
│   │   └── server.py           # Server space implementation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── space.py            # Space data models
│   │   ├── build.py            # Build data models
│   │   ├── scan.py             # Scan data models
│   │   ├── comparison.py       # Comparison data models
│   │   ├── rule.py             # Execution rule models (NEW)
│   │   ├── execution.py        # Execution history models (NEW)
│   │   └── statistics.py       # Statistics models (NEW)
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connector.py        # DB connection management
│   │   └── schema.py           # Database schema
│   └── utils/
│       ├── __init__.py
│       ├── parsers.py          # Result parsers
│       └── validators.py       # Input validation
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js
│   │   ├── index.js
│   │   ├── components/
│   │   │   ├── Dashboard.js
│   │   │   ├── BuildView.js
│   │   │   ├── ScanView.js
│   │   │   ├── ComparisonView.js
│   │   │   ├── LogViewer.js
│   │   │   └── SpaceConfig.js
│   │   ├── services/
│   │   │   ├── api.js          # API client
│   │   │   └── websocket.js    # WebSocket client
│   │   ├── store/
│   │   │   └── index.js        # Redux store
│   │   └── utils/
│   │       └── formatters.js
│   ├── package.json
│   └── webpack.config.js
│
├── cli/
│   ├── __init__.py
│   ├── main.py                 # CLI entry point
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── build.py
│   │   ├── scan.py
│   │   ├── compare.py
│   │   ├── analyze.py
│   │   ├── serve.py
│   │   ├── execute.py          # Selective execution CLI (NEW)
│   │   └── rules.py            # Rule management CLI (NEW)
│   └── formatters/
│       ├── __init__.py
│       ├── text.py
│       ├── html.py
│       └── json.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_spaces.py
│   ├── test_executor.py
│   ├── test_comparator.py
│   ├── test_analyzer.py
│   ├── test_api.py
│   └── integration/
│       ├── test_build_flow.py
│       ├── test_scan_flow.py
│       └── test_comparison_flow.py
│
├── docs/
│   ├── USER_GUIDE.md
│   ├── API.md
│   ├── CONFIGURATION.md
│   └── DEVELOPMENT.md
│
├── examples/
│   ├── lens-config.yaml
│   ├── build-config.yaml
│   └── scan-config.yaml
│
├── scripts/
│   └── setup-dev.sh
│
├── requirements.txt
├── setup.py
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## Usage Examples

### File-Based Mode Examples

#### 1. Execute Build and Generate Report

```bash
# Execute build in local space
lens build \
  --space local \
  --config build-config.yaml \
  --output build-result.json

# Generate HTML report
lens report \
  --build-id build-123 \
  --template detailed \
  --output build-123-report.html
```

#### 2. Compare Two Builds

```bash
# Compare builds
lens compare builds \
  --ids build-123,build-124 \
  --metrics time,warnings,errors \
  --format html \
  --output comparison.html
```

#### 3. Execute Scan in CI Space

```bash
# Run scan in CI
lens scan \
  --space ci \
  --config scan-config.yaml \
  --wait \
  --output scan-result.json

# Compare with baseline
lens compare scans \
  --ids scan-baseline,scan-456 \
  --show-new-issues \
  --format json
```

#### 4. Analyze Logs

```bash
# Analyze build logs
lens analyze logs \
  --build-id build-789 \
  --patterns "error|warning|failed" \
  --output log-analysis.json

# Compare logs from multiple builds
lens compare logs \
  --ids build-789,build-790 \
  --focus compilation \
  --output log-comparison.html
```

### GUI Mode Examples

#### 1. Start Lens Server

```bash
# Start with default configuration
lens serve

# Start with custom configuration
lens serve --config lens-config.yaml --port 8080

# Start with specific space
lens serve --space local --debug
```

#### 2. Access Web Interface

```
Open browser: http://localhost:8080

Dashboard → Select Space → Run Build/Scan
Results → Compare → Select builds → View Comparison
Logs → Select Build → Analyze
```

### Programmatic API Examples

#### 1. Python Client

```python
from lens import LensClient

# Initialize client
client = LensClient(
    base_url="http://localhost:8080",
    api_key="your-api-key"
)

# Execute build
build_result = await client.execute_build(
    space="local",
    config={
        "project_path": "/path/to/project",
        "build_type": "Release"
    }
)

# Compare builds
comparison = await client.compare_builds(
    build_ids=["build-123", "build-124"],
    metrics=["time", "warnings", "errors"]
)

# Print results
print(f"Build time difference: {comparison.metrics.time.difference}s")
print(f"Warning reduction: {comparison.metrics.warnings.difference}")
```

#### 2. REST API

```bash
# Execute build
curl -X POST http://localhost:8080/api/builds \
  -H "Content-Type: application/json" \
  -d '{
    "space": "local",
    "project_path": "/path/to/project",
    "build_type": "Release"
  }'

# Get build result
curl http://localhost:8080/api/builds/build-123

# Compare builds
curl -X POST http://localhost:8080/api/comparisons/builds \
  -H "Content-Type: application/json" \
  -d '{
    "build_ids": ["build-123", "build-124"],
    "metrics": ["time", "warnings", "errors"]
  }'
```

---

## Integration Points

### With Forge

- Read build metadata from Forge database
- Execute builds using Forge CLI
- Compare Forge build results
- Visualize Forge performance data

### With Anvil

- Read code quality metrics from Anvil database
- Execute code scans using Anvil CLI
- Compare scan results
- Track quality trends over time
- **Selective execution based on historical data**
- **Rule-based execution criteria**
- **Failure rate calculation and tracking**
- **Smart test/scan selection**

### With Scout

- Read inspection data from Scout database
- Analyze Scout findings
- Correlate Scout issues with builds
- Generate combined quality reports

### With CI/CD Systems

- GitHub Actions integration
- Jenkins integration
- GitLab CI integration
- Azure DevOps integration
- Trigger builds remotely
- Retrieve artifacts and logs

---

## Security Considerations

### Authentication & Authorization

```yaml
# Authentication configuration
auth:
  enabled: true
  method: jwt  # or oauth, ldap
  secret_key: ${JWT_SECRET}
  expiration: 3600

  # User roles
  roles:
    - name: admin
      permissions: [all]
    - name: developer
      permissions: [read, execute]
    - name: viewer
      permissions: [read]
```

### Secure Communication

- HTTPS/TLS for web interface
- SSH key-based authentication for server spaces
- API token authentication for CI spaces
- Encrypted storage of credentials

### Data Protection

- Database encryption at rest
- Secure credential storage (using keyring)
- Audit logging
- Role-based access control

---

## Performance Considerations

### Scalability

- Async execution for long-running operations
- Task queue for background processing
- Connection pooling for database access
- Caching of frequently accessed data

### Optimization

- Lazy loading of large datasets
- Pagination for API responses
- Incremental data loading in UI
- WebSocket for real-time updates
- Database indexing for common queries

### Resource Management

- Configurable timeouts
- Memory limits for visualizations
- Disk space management for artifacts
- Cleanup of old data

---

## Testing Strategy

### Unit Tests

- Space implementations
- Executor logic
- Comparison algorithms
- Parser functionality
- API endpoints

### Integration Tests

- End-to-end build workflows
- End-to-end scan workflows
- Multi-space operations
- Database operations
- WebSocket communication

### E2E Tests

- GUI workflows
- Complete comparison workflows
- Multi-user scenarios
- CI integration scenarios

---

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**
   - Build time prediction
   - Failure prediction
   - Anomaly detection
   - Optimization suggestions

2. **Advanced Visualizations**
   - Interactive 3D charts
   - Custom dashboard builder
   - Real-time streaming charts
   - Collaborative annotations

3. **Extended Integrations**
   - Jira integration for issue tracking
   - Slack/Teams notifications
   - Grafana export
   - Prometheus metrics

4. **Mobile Support**
   - Mobile-responsive UI
   - Native mobile apps
   - Push notifications

5. **Advanced Analysis**
   - Root cause analysis
   - Performance regression detection
   - Cost analysis
   - Resource optimization

---

## Appendix

### Glossary

- **Space**: An execution environment (local, CI, server)
- **Executor**: Component that runs builds/scans in a space
- **Parser**: Component that interprets execution results
- **Comparison**: Analysis of differences between multiple executions
- **Artifact**: Output file from a build/scan
- **Metric**: Measurable value from an execution

### References

- Forge Specification
- Anvil Specification
- Scout Specification
- FastAPI Documentation
- React Documentation

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-01 | Initial specification |

