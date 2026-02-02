# Anvil Project Integration Plan
## Using Anvil for Code Validation Across the Argos Project

**Created:** February 1, 2026
**Goal:** Establish Anvil as the unified code quality gate for all Argos components (anvil, forge, and future components)

---

## Executive Summary

This plan outlines how to use Anvil to control all code validation across the entire Argos project, including:
- **anvil/** - The code quality gate tool itself
- **forge/** - The CMake build wrapper
- **Future components** - Scout (CI inspection), Lens (visualization), etc.

The integration will provide:
1. Unified quality standards across all components
2. Centralized validation result storage and tracking
3. Cross-component quality visualization
4. Automated quality gates in CI/CD

---

## Table of Contents

1. [Current State Analysis](#1-current-state-analysis)
2. [Configuration Requirements](#2-configuration-requirements)
3. [Missing Features & Implementation Needs](#3-missing-features--implementation-needs)
4. [Visualization & Reporting](#4-visualization--reporting)
5. [Implementation Roadmap](#5-implementation-roadmap)
6. [Success Criteria](#6-success-criteria)

---

## 1. Current State Analysis

### 1.1 Existing Components

**Anvil** (`anvil/`)
- Status: ✅ Complete and functional
- Python version: 3.8+
- Configuration: Uses `anvil.toml` in its own directory
- Testing: 986 tests, 92.38% coverage
- Validators: Python (flake8, black, isort, pylint, pytest, radon, vulture, autoflake)
- Storage: SQLite database (`.anvil/stats.db`)
- Reporting: Console output + JSON export

**Forge** (`forge/`)
- Status: ✅ Complete and functional
- Python version: 3.11+
- Configuration: Uses `pyproject.toml` (black, isort, pytest config)
- Testing: pytest suite exists
- Current validation: Manual or basic pre-commit checks
- No centralized statistics tracking

### 1.2 Current Limitations

1. **Isolated Validation**: Each component runs its own validation independently
2. **No Cross-Component Tracking**: Cannot see project-wide quality metrics
3. **Inconsistent Standards**: Different Python versions, different quality thresholds
4. **Manual Coordination**: No automated way to run validation across all components
5. **Limited Visibility**: No unified dashboard or reporting

---

## 2. Configuration Requirements

### 2.1 Project-Level Configuration

Create **root-level** `anvil.toml` that orchestrates validation across all components:

```toml
# d:\playground\argos\anvil.toml
[project]
name = "argos"
version = "1.0.0"
description = "Unified quality tooling ecosystem"

# Components to validate
[components]
# Each component is a sub-project with its own configuration
anvil = { path = "anvil", enabled = true }
forge = { path = "forge", enabled = true }
# scout = { path = "scout", enabled = false }  # Future
# lens = { path = "lens", enabled = false }    # Future

# Global validation settings (apply to all components unless overridden)
[validation]
mode = "full"                    # Default mode: "full" or "incremental"
fail_fast = false                # Continue on errors to see all issues
parallel = true                  # Run component validations in parallel
max_workers = 4                  # Parallel worker limit
timeout = 600                    # Global timeout (10 minutes for full project)

# Global Python standards (baseline for all components)
[python]
min_version = "3.8"              # Support oldest version across all components
max_complexity = 10              # Cyclomatic complexity threshold
min_coverage = 90                # Minimum test coverage

[python.validators]
flake8 = { enabled = true }
black = { enabled = true }
isort = { enabled = true }
pylint = { enabled = true }
pytest = { enabled = true }
radon = { enabled = true }
vulture = { enabled = true }
autoflake = { enabled = true }

# Statistics and tracking
[statistics]
enabled = true
database_path = ".anvil/argos_stats.db"  # Centralized database
retention_days = 365                      # Keep 1 year of history

# Smart filtering (optimize test execution)
[smart_filtering]
enabled = true
skip_threshold = 0.95            # Skip tests with >95% success rate
minimum_runs = 10                # Require 10 runs before filtering
```

### 2.2 Component-Level Configuration

Each component maintains its own `anvil.toml` for component-specific settings:

#### Anvil Component (`anvil/anvil.toml`)

```toml
[project]
name = "anvil"
version = "0.1.0"
languages = ["python"]

[python]
version = "3.8"                  # Anvil's specific Python version
# Inherits global settings, but can override
max_complexity = 12              # Slightly more complex due to CLI handling
min_coverage = 90

[python.validators.flake8]
enabled = true
max_line_length = 100
ignore = ["E203", "W503"]
exclude = ["anvil/cli/*"]        # CLI excluded from coverage

[python.validators.black]
enabled = true
line_length = 100

[python.validators.isort]
enabled = true
profile = "black"

[python.validators.pytest]
enabled = true
min_coverage = 90
coverage_exclude = [
    "anvil/cli/*.py",
    "anvil/cli/__init__.py",
    "anvil/cli/main.py",
    "anvil/cli/commands.py",
    "*/anvil/cli/*",
]

# Component-specific exclusions
[validation]
exclude_dirs = [
    "htmlcov/",
    "__pycache__/",
    ".pytest_cache/",
    "*.egg-info/",
]
```

#### Forge Component (`forge/anvil.toml`)

```toml
[project]
name = "forge"
version = "0.1.0"
languages = ["python"]

[python]
version = "3.11"                 # Forge's specific Python version
# Inherits global settings
max_complexity = 10
min_coverage = 90

[python.validators.flake8]
enabled = true
max_line_length = 100
ignore = ["E203", "W503"]

[python.validators.black]
enabled = true
line_length = 100
target_version = ["py311"]

[python.validators.isort]
enabled = true
profile = "black"
known_first_party = ["forge"]

[python.validators.pytest]
enabled = true
min_coverage = 90
testpaths = ["tests"]

# Forge-specific exclusions
[validation]
exclude_dirs = [
    "tutorial/",                 # Sample projects, not production code
    "__pycache__/",
    ".pytest_cache/",
    "*.egg-info/",
]
```

### 2.3 CI/CD Configuration

#### GitHub Actions Integration

```yaml
# .github/workflows/quality-gate.yml
name: Quality Gate

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  validate-project:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.8', '3.11', '3.12']

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install Anvil
        run: |
          cd anvil
          pip install -e .

      - name: Run Project-Wide Validation
        run: |
          anvil check-project \
            --config anvil.toml \
            --export-results .anvil/results.json \
            --upload-stats

      - name: Upload Results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: quality-results-py${{ matrix.python-version }}
          path: .anvil/results.json

      - name: Comment PR with Results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('.anvil/results.json'));
            // Post comment with summary
```

---

## 3. Missing Features & Implementation Needs

### 3.1 Critical Features (Must Have)

#### 3.1.1 Multi-Component Orchestration

**Feature**: `anvil check-project` command
**Status**: ❌ Not implemented
**Description**: Run validation across multiple components in a single invocation

**Implementation Requirements**:

```python
# anvil/cli/commands.py

def check_project_command(
    args,
    config: str = "anvil.toml",
    component: Optional[List[str]] = None,
    parallel: bool = True,
    export_results: Optional[str] = None,
    upload_stats: bool = False,
) -> int:
    """
    Run validation across multiple project components.

    Args:
        config: Path to project-level anvil.toml
        component: Specific components to validate (None = all)
        parallel: Run components in parallel
        export_results: Path to export combined results JSON
        upload_stats: Upload results to centralized database

    Returns:
        Exit code (0 = all pass, 1 = any failures)

    Workflow:
        1. Load project-level config from root anvil.toml
        2. Discover enabled components
        3. For each component:
           - Change to component directory
           - Load component anvil.toml
           - Merge with global config
           - Run validation
           - Collect results
        4. Aggregate results
        5. Store in centralized database
        6. Generate unified report
    """
    pass
```

**Testing Requirements**:
- Test loading project-level config
- Test component discovery
- Test config inheritance/merging
- Test parallel execution
- Test result aggregation
- Test centralized storage

**Estimated Effort**: 2-3 days

---

#### 3.1.2 Unified Results Storage

**Feature**: Centralized database for all components
**Status**: ⚠️ Partial (exists but not multi-component aware)
**Description**: Store validation results from all components in single database

**Implementation Requirements**:

**Database Schema Extension**:

```sql
-- Add component tracking to validation_runs table
ALTER TABLE validation_runs ADD COLUMN component_name TEXT;
ALTER TABLE validation_runs ADD COLUMN component_version TEXT;
CREATE INDEX idx_component ON validation_runs(component_name);

-- New table: component_metadata
CREATE TABLE component_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component_name TEXT NOT NULL UNIQUE,
    python_version TEXT,
    last_validated TIMESTAMP,
    total_runs INTEGER DEFAULT 0,
    last_status TEXT
);

-- New table: cross_component_metrics
CREATE TABLE cross_component_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_components INTEGER,
    components_passed INTEGER,
    components_failed INTEGER,
    total_errors INTEGER,
    total_warnings INTEGER,
    total_duration_seconds REAL
);
```

**Code Changes**:

```python
# anvil/storage/statistics_database.py

@dataclass
class ValidationRun:
    # Existing fields...
    component_name: Optional[str] = None      # NEW
    component_version: Optional[str] = None   # NEW

# Add methods:
def get_component_history(component_name: str, days: int = 30)
def get_cross_component_metrics(days: int = 30)
def get_component_comparison()
```

**Estimated Effort**: 1-2 days

---

#### 3.1.3 Configuration Inheritance & Merging

**Feature**: Hierarchical configuration (project → component → CLI)
**Status**: ❌ Not implemented
**Description**: Merge configs from multiple levels with proper precedence

**Implementation Requirements**:

```python
# anvil/config/configuration.py

class ConfigurationMerger:
    """
    Merge configurations from multiple sources with precedence.

    Precedence (highest to lowest):
        1. CLI arguments
        2. Component anvil.toml
        3. Project anvil.toml
        4. Built-in defaults
    """

    @staticmethod
    def merge(
        project_config: Dict[str, Any],
        component_config: Dict[str, Any],
        cli_overrides: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Deep merge configurations.

        Rules:
            - Lists: component overrides project (not appended)
            - Dicts: deep merge (component extends/overrides project)
            - Primitives: component/CLI overrides project
            - None: use lower precedence value
        """
        pass

    @staticmethod
    def validate_merged_config(config: Dict[str, Any]) -> List[str]:
        """Validate merged configuration, return list of errors."""
        pass
```

**Estimated Effort**: 1 day

---

### 3.2 Important Features (Should Have)

#### 3.2.1 Component Dependency Validation

**Feature**: Validate components in dependency order
**Status**: ❌ Not implemented
**Description**: Ensure dependencies pass before dependent components

**Configuration**:

```toml
[components.forge]
path = "forge"
enabled = true
depends_on = ["anvil"]  # Forge depends on Anvil

[components.scout]
path = "scout"
enabled = false
depends_on = ["anvil", "forge"]  # Scout depends on both
```

**Estimated Effort**: 1 day

---

#### 3.2.2 Incremental Cross-Component Validation

**Feature**: Smart detection of which components need validation
**Status**: ❌ Not implemented
**Description**: Only validate components with changes

**Algorithm**:

```python
def detect_changed_components(since_commit: str) -> List[str]:
    """
    Detect which components have changed files.

    Returns list of component names that need validation.

    Example:
        - Changes in anvil/core/ → validate anvil
        - Changes in forge/cli/ → validate forge
        - Changes in docs/ → validate nothing (docs only)
        - Changes in root anvil.toml → validate all
    """
    pass
```

**Estimated Effort**: 1 day

---

#### 3.2.3 Consolidated JSON Export

**Feature**: Export unified project validation results
**Status**: ⚠️ Partial (exists per-component only)
**Description**: Single JSON with all component results

**Format**:

```json
{
  "project": {
    "name": "argos",
    "version": "1.0.0",
    "timestamp": "2026-02-01T10:30:00Z",
    "overall_passed": false,
    "total_duration": 125.3
  },
  "components": [
    {
      "name": "anvil",
      "version": "0.1.0",
      "passed": true,
      "duration": 45.2,
      "summary": {
        "total_validators": 8,
        "validators_passed": 8,
        "total_errors": 0,
        "total_warnings": 2
      },
      "validators": [...]
    },
    {
      "name": "forge",
      "version": "0.1.0",
      "passed": false,
      "duration": 80.1,
      "summary": {
        "total_validators": 8,
        "validators_passed": 7,
        "total_errors": 5,
        "total_warnings": 0
      },
      "validators": [...]
    }
  ],
  "cross_component_summary": {
    "total_components": 2,
    "components_passed": 1,
    "components_failed": 1,
    "total_errors": 5,
    "total_warnings": 2
  }
}
```

**Estimated Effort**: 0.5 days

---

### 3.3 Nice-to-Have Features (Future)

#### 3.3.1 Component Quality Badges

Generate badges for README files:

```markdown
[![Anvil Quality](https://img.shields.io/badge/quality-passing-green.svg)]()
[![Forge Quality](https://img.shields.io/badge/quality-failing-red.svg)]()
```

**Estimated Effort**: 0.5 days

---

#### 3.3.2 Quality Trend Comparison

Compare quality trends across components:

```bash
anvil stats compare --components anvil,forge --days 30
```

Output:
```
Component Quality Trends (Last 30 Days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Anvil:  ████████████████████░ 95% pass rate (↑2%)
Forge:  ███████████████░░░░░░ 78% pass rate (↓5%)

Top Issues:
  Anvil:  2 complexity warnings (radon)
  Forge:  15 formatting errors (black)
```

**Estimated Effort**: 1 day

---

## 4. Visualization & Reporting

### 4.1 Console Output

#### 4.1.1 Project-Level Summary

```bash
$ anvil check-project

╔═══════════════════════════════════════════════════════════════╗
║              Argos Project Quality Gate                       ║
╚═══════════════════════════════════════════════════════════════╝

Validating 2 components...

┌───────────────────────────────────────────────────────────────┐
│ Component: anvil                                              │
├───────────────────────────────────────────────────────────────┤
│ ✓ flake8         0 errors     2 warnings    (2.3s)           │
│ ✓ black          0 errors     0 warnings    (1.8s)           │
│ ✓ isort          0 errors     0 warnings    (1.2s)           │
│ ✓ pytest         986 passed   26 skipped    (45.1s)          │
│ ✓ radon          0 errors     2 complexity  (3.2s)           │
│                                                               │
│ Result: ✓ PASSED (54.2s)                                     │
│ Coverage: 92.38%                                              │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│ Component: forge                                              │
├───────────────────────────────────────────────────────────────┤
│ ✗ flake8         5 errors     0 warnings    (2.1s)           │
│ ✗ black          15 errors    0 warnings    (1.9s)           │
│ ✓ isort          0 errors     0 warnings    (1.4s)           │
│ ✓ pytest         234 passed   5 skipped     (32.5s)          │
│                                                               │
│ Result: ✗ FAILED (38.3s)                                     │
│ Coverage: 88.21%                                              │
└───────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════╗
║                    Project Summary                            ║
╠═══════════════════════════════════════════════════════════════╣
║ Components:        2                                          ║
║ Passed:            1 (50%)                                    ║
║ Failed:            1 (50%)                                    ║
║ Total Errors:      20                                         ║
║ Total Warnings:    2                                          ║
║ Total Duration:    92.5s                                      ║
║                                                               ║
║ Overall Status:    ✗ FAILED                                  ║
╚═══════════════════════════════════════════════════════════════╝

Detailed errors in: .anvil/results.json
```

---

### 4.2 JSON Export

The consolidated JSON export (see 3.2.3) provides machine-readable results for:
- CI/CD integration
- Badge generation
- Trend analysis
- Custom reporting tools

**Usage**:

```bash
# Export to file
anvil check-project --export-results .anvil/results.json

# Use in CI to generate PR comments
cat .anvil/results.json | jq '.cross_component_summary'
```

---

### 4.3 Web Dashboard (Future: Lens Integration)

The **Lens** tool (from Iteration 2 plan) will provide:

1. **Project Overview Dashboard**
   - All components at a glance
   - Pass/fail status
   - Quality trend graphs

2. **Component Detail View**
   - Per-component metrics
   - Historical trends
   - Validator breakdown

3. **Cross-Component Comparison**
   - Side-by-side quality metrics
   - Relative performance
   - Shared issues

4. **Quality Heatmap**
   - File-level quality visualization
   - Hot spots (frequently failing files)
   - Coverage gaps

**Example Dashboard Layout**:

```
┌──────────────────────────────────────────────────────────────┐
│ Argos Project Quality Dashboard                             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│ Overall Status: ✓ PASSING (1 component warning)            │
│ Last Updated: 2026-02-01 10:30:00                           │
│                                                              │
│ ┌─────────────────┬──────────┬─────────┬──────────────────┐ │
│ │ Component       │ Status   │ Errors  │ Coverage         │ │
│ ├─────────────────┼──────────┼─────────┼──────────────────┤ │
│ │ Anvil           │ ✓ Pass   │ 0       │ ██████████ 92%  │ │
│ │ Forge           │ ⚠ Warn   │ 0 (2w)  │ ████████░░ 88%  │ │
│ │ Scout (Future)  │ - N/A    │ -       │ -                │ │
│ │ Lens (Future)   │ - N/A    │ -       │ -                │ │
│ └─────────────────┴──────────┴─────────┴──────────────────┘ │
│                                                              │
│ Quality Trends (Last 30 Days)                               │
│ ┌────────────────────────────────────────────────────────┐  │
│ │ Pass Rate:                                             │  │
│ │ 100% ┤                                        ░░░░     │  │
│ │  90% ┤                               ░░░░░░░░          │  │
│ │  80% ┤                      ░░░░░░░░                   │  │
│ │  70% ┤             ░░░░░░░░                            │  │
│ │  60% ┤    ░░░░░░░░                                     │  │
│ │      └────────────────────────────────────────────────│  │
│ │       Jan 1      Jan 15     Jan 30     Feb 1          │  │
│ └────────────────────────────────────────────────────────┘  │
│                                                              │
│ Top Issues This Week:                                       │
│ • Complexity: 5 functions exceed threshold (radon)          │
│ • Formatting: 2 files need black formatting (forge)         │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Data Source**: SQLite database (`.anvil/argos_stats.db`)

**Access Methods**:
1. **Static HTML**: `anvil stats dashboard --export dashboard.html`
2. **Live Server**: `anvil stats serve --port 8080` (future)
3. **Lens Integration**: Full-featured web app (future)

---

### 4.4 Statistics Commands

Extend existing `anvil stats` commands for project-level queries:

```bash
# Project-level report
anvil stats report --project

# Component comparison
anvil stats compare --components anvil,forge

# Cross-component trends
anvil stats trends --project --days 30

# Component-specific flaky tests
anvil stats flaky --component anvil

# Export project statistics
anvil stats export --project --format json --output project-stats.json
```

**Output Example**:

```bash
$ anvil stats report --project

Argos Project Statistics (Last 30 Days)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Overall Project Health
  Total Runs:        156
  Success Rate:      89.7%
  Average Duration:  95.3s

Component Breakdown
┌──────────┬───────┬─────────────┬────────────┐
│ Component│ Runs  │ Success Rate│ Avg Duration│
├──────────┼───────┼─────────────┼────────────┤
│ anvil    │ 78    │ 94.9%       │ 52.1s      │
│ forge    │ 78    │ 84.6%       │ 43.2s      │
└──────────┴───────┴─────────────┴────────────┘

Top Issues (All Components)
  1. black formatting (forge): 45 occurrences
  2. complexity warnings (anvil): 12 occurrences
  3. unused imports (forge): 8 occurrences

Quality Trends
  ↑ Anvil:  94.9% (+2.1% from last week)
  ↓ Forge:  84.6% (-3.2% from last week)
```

---

## 5. Implementation Roadmap

### Phase 1: Core Multi-Component Support (Week 1)

**Goal**: Basic project-wide validation

- [ ] **Day 1-2**: Implement `ConfigurationMerger` class
  - Hierarchical config loading
  - Merge logic with precedence
  - Unit tests (100% coverage)

- [ ] **Day 3-4**: Implement `anvil check-project` command
  - Component discovery
  - Sequential execution (parallel later)
  - Result aggregation
  - Basic console output

- [ ] **Day 5**: Update database schema
  - Add component tracking
  - Migration script
  - Update persistence layer

**Deliverable**: Can run `anvil check-project` and see results from all components

---

### Phase 2: Enhanced Storage & Reporting (Week 2)

**Goal**: Centralized tracking and visualization

- [ ] **Day 1-2**: Centralized database features
  - Cross-component queries
  - Component comparison
  - Trend analysis

- [ ] **Day 3**: Consolidated JSON export
  - Unified result format
  - Component breakdown
  - Cross-component summary

- [ ] **Day 4-5**: Enhanced console reporting
  - Project-level summary
  - Component comparison output
  - Statistics commands for project

**Deliverable**: Rich console output and exportable results

---

### Phase 3: CI/CD Integration (Week 3)

**Goal**: Automated quality gates

- [ ] **Day 1-2**: GitHub Actions workflow
  - Matrix testing across Python versions
  - Result upload
  - PR comment generation

- [ ] **Day 3**: Incremental validation
  - Changed component detection
  - Smart component selection
  - Dependency-aware execution

- [ ] **Day 4-5**: Documentation
  - Configuration guide
  - CI/CD setup guide
  - Migration guide for existing components

**Deliverable**: Full CI/CD integration with automated PR feedback

---

### Phase 4: Advanced Features (Week 4)

**Goal**: Polish and optimize

- [ ] **Day 1-2**: Parallel component execution
  - Concurrent validation
  - Resource limits
  - Error isolation

- [ ] **Day 3**: Component dependencies
  - Dependency graph
  - Ordered execution
  - Failure propagation

- [ ] **Day 4**: Static HTML dashboard
  - Generate dashboard from stats DB
  - Component comparison view
  - Trend visualization

- [ ] **Day 5**: Testing and refinement
  - Integration tests
  - Performance optimization
  - Bug fixes

**Deliverable**: Production-ready multi-component validation system

---

## 6. Success Criteria

### 6.1 Functional Requirements

- [ ] **F1**: Can validate all components with single command
- [ ] **F2**: Component-specific configurations are respected
- [ ] **F3**: Results stored in centralized database
- [ ] **F4**: Consolidated JSON export available
- [ ] **F5**: Project-level statistics queries work
- [ ] **F6**: CI/CD workflow validates all components
- [ ] **F7**: Incremental mode detects changed components
- [ ] **F8**: Parallel execution reduces validation time

### 6.2 Quality Requirements

- [ ] **Q1**: All new code has 100% test coverage
- [ ] **Q2**: No regression in existing Anvil functionality
- [ ] **Q3**: Documentation complete and accurate
- [ ] **Q4**: Configuration examples tested and working
- [ ] **Q5**: Performance: Full project validation <2 minutes
- [ ] **Q6**: Error handling: Clear messages for all failure modes

### 6.3 Usability Requirements

- [ ] **U1**: Configuration file is intuitive
- [ ] **U2**: Console output is clear and actionable
- [ ] **U3**: JSON export is well-structured
- [ ] **U4**: Statistics commands are discoverable
- [ ] **U5**: CI/CD setup takes <30 minutes

---

## 7. Migration Path for Existing Components

### 7.1 Anvil (Self-Hosted)

**Current State**: Already uses Anvil internally

**Migration Steps**:
1. ✅ No changes needed (already using anvil.toml)
2. ✅ Update database to include component tracking
3. ✅ Update pre-commit hook to use project-level config

**Validation**:
```bash
cd anvil
anvil check  # Should still work as before
cd ..
anvil check-project --component anvil  # New command
```

---

### 7.2 Forge

**Current State**: Uses pyproject.toml for black/isort config, manual pytest

**Migration Steps**:

1. **Create `forge/anvil.toml`**:
   ```bash
   cd forge
   anvil config init
   # Edit to match existing pyproject.toml settings
   ```

2. **Update pre-commit hooks**:
   ```bash
   anvil install-hooks
   ```

3. **Test locally**:
   ```bash
   anvil check  # Verify forge-specific validation
   cd ..
   anvil check-project --component forge  # Project-level test
   ```

4. **Migrate from pyproject.toml** (optional):
   - Keep tool-specific config in pyproject.toml
   - Use anvil.toml for validation orchestration
   - Or consolidate into anvil.toml only

**Validation**:
```bash
# Before migration
cd forge
python -m pytest tests/
python -m black --check .
python -m isort --check .

# After migration
cd forge
anvil check
# Should produce same results with better reporting
```

---

### 7.3 Future Components (Scout, Lens)

**Approach**: Start with Anvil from day one

**Setup Template**:
```bash
# Create new component
mkdir scout
cd scout

# Initialize with Anvil
anvil config init
# Edit scout/anvil.toml for component-specific settings

# Set up development
anvil install-hooks
```

**Benefit**: Consistent quality standards from project inception

---

## 8. Example Usage Scenarios

### Scenario 1: Developer Daily Workflow

```bash
# Developer makes changes to forge/cli/commands.py

# Before commit: Check only changed component
git status
# modified:   forge/cli/commands.py

anvil check-project --incremental
# Output: Only validates forge (detected changes)
# Duration: ~40s (instead of ~90s for full project)

# Fix issues
anvil check --validator black
# make fixes...

# Commit with confidence
git commit -m "Add new command"
# Pre-commit hook runs automatically
```

---

### Scenario 2: CI/CD Pull Request Validation

```bash
# PR opened: Changes in both anvil and forge

# GitHub Action runs:
anvil check-project --export-results .anvil/results.json

# Result posted as PR comment:
```

**Comment:**
```markdown
## 🚦 Quality Gate: PASSED ✅

| Component | Status | Errors | Warnings | Coverage |
|-----------|--------|--------|----------|----------|
| anvil     | ✅ Pass | 0      | 2        | 92.38%   |
| forge     | ✅ Pass | 0      | 0        | 91.54%   |

**Project Summary**: 2/2 components passed

<details>
<summary>📊 Details</summary>

**Anvil** (52.1s)
- ✅ flake8: passed
- ✅ black: passed
- ✅ pytest: 986 passed, 26 skipped
- ⚠️ radon: 2 complexity warnings

**Forge** (43.2s)
- ✅ All validators passed
- ✅ Tests: 234 passed, 5 skipped

</details>
```

---

### Scenario 3: Weekly Quality Review

```bash
# Team lead reviews project health

# Get project statistics
anvil stats report --project --days 7

# Compare components
anvil stats compare --components anvil,forge

# Identify issues
anvil stats problem-files --project --threshold 0.8

# Export for presentation
anvil stats export --project --format json --output weekly-report.json

# Generate static dashboard
anvil stats dashboard --export dashboard.html
# Open dashboard.html in browser for visual review
```

---

### Scenario 4: Release Quality Gate

```bash
# Before releasing v1.0.0

# Full validation with strict mode
anvil check-project \
  --no-warnings \
  --fail-fast=false \
  --export-results release-validation.json

# Review historical quality
anvil stats trends --project --days 30

# Ensure all components meet criteria
jq '.cross_component_summary.components_passed == .cross_component_summary.total_components' \
  release-validation.json

# Tag release only if all pass
```

---

## 9. Appendix

### A. Configuration Schema Reference

**See**: `anvil/docs/CONFIGURATION.md` for detailed schema

**Key Sections**:
- `[project]`: Project metadata
- `[components]`: Component definitions
- `[validation]`: Validation behavior
- `[python]`: Python standards
- `[python.validators.*]`: Validator-specific config
- `[statistics]`: Statistics tracking
- `[smart_filtering]`: Test optimization

---

### B. Database Schema

**Primary Database**: `.anvil/argos_stats.db`

**Key Tables**:
- `validation_runs`: All validation runs (with component_name)
- `component_metadata`: Component tracking
- `cross_component_metrics`: Project-level metrics
- `validator_run_records`: Per-validator results
- `test_case_records`: Test execution history
- `file_validation_records`: File-level issues

**See**: `anvil/storage/statistics_database.py` for full schema

---

### C. CLI Command Reference

**New Commands**:
- `anvil check-project`: Validate all components
- `anvil stats report --project`: Project-level statistics
- `anvil stats compare`: Component comparison
- `anvil stats dashboard`: Generate HTML dashboard

**Modified Commands**:
- `anvil check --incremental`: Now component-aware
- `anvil stats *`: Accept `--project` and `--component` flags

**See**: `anvil/docs/USER_GUIDE.md` for full CLI reference

---

### D. API Reference

**Key Classes**:
- `ConfigurationMerger`: Hierarchical config merging
- `ProjectValidator`: Multi-component orchestration
- `ComponentDiscovery`: Component detection
- `ResultAggregator`: Cross-component result collection

**See**: `anvil/docs/API.md` for full API documentation

---

### E. Testing Strategy

**Test Coverage Goals**:
- All new code: 100% coverage
- Integration tests: All workflows covered
- E2E tests: Full project validation scenarios

**Test Types**:
1. **Unit Tests**: ConfigurationMerger, ComponentDiscovery
2. **Integration Tests**: check-project command, database storage
3. **E2E Tests**: Full CI/CD workflow, multi-component validation
4. **Performance Tests**: Parallel execution, large projects

---

## 10. Conclusion

This plan provides a comprehensive path to using Anvil as the unified code quality gate for the entire Argos project. The implementation is designed to:

1. **Maintain Backward Compatibility**: Existing Anvil usage unchanged
2. **Minimize Configuration Burden**: Sensible defaults, optional overrides
3. **Scale to Future Components**: Easy to add Scout, Lens, etc.
4. **Provide Rich Insights**: Statistics, trends, visualizations
5. **Integrate with CI/CD**: Automated quality gates, PR feedback
6. **Support Developer Workflow**: Fast incremental checks, clear output

**Estimated Total Effort**: 4 weeks (1 developer)

**Dependencies**:
- Anvil 0.1.0 (complete)
- Python 3.8+ support
- SQLite 3.x
- Git (for incremental mode)

**Next Steps**:
1. Review and approve plan
2. Create implementation issues/tasks
3. Begin Phase 1: Core multi-component support
4. Iterate based on feedback

---

**Document Version**: 1.0
**Last Updated**: February 1, 2026
**Author**: GitHub Copilot
**Status**: Draft for Review
