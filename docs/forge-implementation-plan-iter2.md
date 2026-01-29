# Iterative Planning: Argos Iteration 2 - Tooling Ecosystem

**Goal:** Expand Argos with complementary tools for quality assurance, CI inspection, and data visualization.

**Prerequisites:** Iteration 1 (Forge) must be complete and functional.

---

## Overview

Iteration 2 expands the Argos project with three new components:

1. **Anvil** - Pre-commit validation and quality gate tool
2. **Scout** - CI/CD inspection and failure analysis tool
3. **Lens** - Build data visualization and analytics dashboard
4. **Forge** - Packaging, distribution, and CI/CD pipeline (from Iter 1)

---

## Component 1: Anvil - Pre-commit Validation Tool

**Goal:** Create a comprehensive pre-commit validation tool that enforces code quality standards before commits.

### Features

- Automated code quality checks (linting, formatting, complexity)
- Test execution with coverage validation
- Configurable quality gates
- Fast incremental checks (only modified files)
- Clear, actionable error messages

### Steps

#### Step 1.1: Core Validation Framework
- **Description:** Implement Anvil base class with plugin architecture for different validators.

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test validator framework and plugin loading
  - **Test File:** `anvil/tests/test_validator_framework.py`
  - **Test Cases:**
    - Test validator registration
    - Test validator execution order
    - Test validator result aggregation
    - Test validator error handling
    - Test validator configuration loading
  - **Success Criteria:** Framework loads and executes validators correctly, 100% coverage

#### Step 1.2: Code Quality Validators
- **Description:** Implement validators for flake8, black, isort, pylint, radon, vulture, autoflake.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test each code quality validator
  - **Test File:** `anvil/tests/test_code_quality.py`
  - **Test Cases:**
    - Test flake8 syntax checking
    - Test black formatting validation
    - Test isort import ordering
    - Test pylint static analysis
    - Test radon complexity analysis
    - Test vulture dead code detection
    - Test autoflake unused code detection
    - Test incremental checking (only changed files)
  - **Success Criteria:** All validators work correctly, incremental mode functional, 95% coverage

#### Step 1.3: Test & Coverage Validators
- **Description:** Implement pytest execution with coverage threshold validation.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test test execution and coverage validation
  - **Test File:** `anvil/tests/test_test_validation.py`
  - **Test Cases:**
    - Test pytest execution
    - Test coverage threshold checking (per-module and overall)
    - Test test failure detection
    - Test skipped test reporting
    - Test incremental test selection
    - Test coverage report generation
  - **Success Criteria:** Tests execute correctly, coverage validated, 95% coverage

#### Step 1.4: Git Hook Integration
- **Description:** Implement automatic git hook installation and management.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test git hook installation and execution
  - **Test File:** `anvil/tests/test_git_hooks.py`
  - **Test Cases:**
    - Test pre-commit hook installation
    - Test hook execution on commit
    - Test hook bypass mechanism
    - Test hook uninstallation
    - Test hook update on Anvil update
    - Test multi-repository support
  - **Success Criteria:** Hooks install and execute correctly, 100% coverage

#### Step 1.5: CLI & Configuration
- **Description:** Implement Anvil CLI with configuration file support.

- **Testing Approach:**
  - **Test Type:** Unit + Integration tests
  - **Test Description:** Test CLI and configuration
  - **Test File:** `anvil/tests/test_cli.py`
  - **Test Cases:**
    - Test `anvil check` command
    - Test `anvil install-hooks` command
    - Test `anvil config` command
    - Test configuration file loading (anvil.toml)
    - Test CLI argument parsing
    - Test verbose/quiet modes
  - **Success Criteria:** CLI functional, configuration works, 100% coverage

### Success Criteria
- **Overall:** Anvil provides comprehensive pre-commit validation, installs as git hook, all quality checks pass. Test coverage ≥95%.

---

## Component 2: Scout - CI/CD Inspection Tool

**Goal:** Create a tool to inspect, analyze, and troubleshoot CI/CD pipeline failures.

### Features

- GitHub Actions log retrieval
- Test failure parsing and analysis
- Failure pattern detection
- Cross-platform failure comparison
- Trend analysis (flaky tests, recurring failures)
- Actionable failure reports

### Steps

#### Step 2.1: CI Provider Abstraction
- **Description:** Implement abstract CI provider interface and GitHub Actions implementation.

- **Testing Approach:**
  - **Test Type:** Unit tests with mocking
  - **Test Description:** Test CI provider abstraction
  - **Test File:** `scout/tests/test_providers.py`
  - **Test Cases:**
    - Test provider interface definition
    - Test GitHub Actions provider implementation
    - Test authentication handling
    - Test API rate limiting
    - Test error handling for API failures
  - **Success Criteria:** Provider interface clean, GitHub Actions works with mocked API, 100% coverage

#### Step 2.2: Log Retrieval & Storage
- **Description:** Implement log retrieval from CI providers and local caching.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test log retrieval and caching
  - **Test File:** `scout/tests/test_log_retrieval.py`
  - **Test Cases:**
    - Test workflow run listing
    - Test log download
    - Test log parsing (ANSI removal, timestamp extraction)
    - Test local cache storage
    - Test cache invalidation
    - Test incremental log updates
  - **Success Criteria:** Logs retrieved and cached correctly, 95% coverage

#### Step 2.3: Test Failure Parser
- **Description:** Implement parsing of test output to extract failure information.

- **Testing Approach:**
  - **Test Type:** Unit tests with fixtures
  - **Test Description:** Test failure parsing from various test frameworks
  - **Test File:** `scout/tests/test_failure_parser.py`
  - **Test Cases:**
    - Test pytest failure parsing
    - Test unittest failure parsing
    - Test Google Test failure parsing
    - Test failure location extraction (file, line, test name)
    - Test assertion message extraction
    - Test stack trace parsing
    - Test multiple failure handling
  - **Success Criteria:** Failures parsed from all major test frameworks, 95% coverage

#### Step 2.4: Failure Analysis Engine
- **Description:** Implement failure pattern detection and trend analysis.

- **Testing Approach:**
  - **Test Type:** Unit + Integration tests
  - **Test Description:** Test failure analysis algorithms
  - **Test File:** `scout/tests/test_analysis.py`
  - **Test Cases:**
    - Test flaky test detection (passes sometimes, fails sometimes)
    - Test recurring failure detection
    - Test platform-specific failure detection
    - Test failure grouping by similarity
    - Test trend analysis over time
    - Test actionable recommendation generation
  - **Success Criteria:** Analysis produces useful insights, recommendations actionable, 90% coverage

#### Step 2.5: Reporting & Visualization
- **Description:** Implement rich console output and HTML reports.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test report generation
  - **Test File:** `scout/tests/test_reporting.py`
  - **Test Cases:**
    - Test console failure summary
    - Test HTML report generation
    - Test failure timeline visualization
    - Test platform comparison tables
    - Test flaky test highlighting
    - Test export formats (JSON, CSV)
  - **Success Criteria:** Reports are clear and useful, 95% coverage

#### Step 2.6: CLI Interface
- **Description:** Implement Scout CLI with commands for log retrieval and analysis.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test CLI commands
  - **Test File:** `scout/tests/test_cli.py`
  - **Test Cases:**
    - Test `scout logs <workflow>` command
    - Test `scout analyze <run-id>` command
    - Test `scout trends <workflow>` command
    - Test `scout flaky` command
    - Test authentication configuration
    - Test output format options
  - **Success Criteria:** All CLI commands functional, 100% coverage

### Success Criteria
- **Overall:** Scout can retrieve CI logs, parse failures, detect patterns, and generate actionable reports. Test coverage ≥90%.

---

## Component 3: Lens - Data Visualization Dashboard

**Goal:** Create a tool to visualize and analyze Forge build data with rich graphics and insights.

### Features

- Interactive build history timeline
- Performance trend analysis
- Warning/error visualization
- Build comparison tools
- Custom query interface
- Export capabilities (PNG, PDF, CSV)

### Steps

#### Step 3.1: Data Access Layer
- **Description:** Implement data access layer that reads from Forge database.

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test database queries and data models
  - **Test File:** `lens/tests/test_data_access.py`
  - **Test Cases:**
    - Test connection to Forge database
    - Test build query methods
    - Test filtering and aggregation
    - Test date range queries
    - Test project-specific queries
    - Test data model transformations
  - **Success Criteria:** Data access works with Forge database, 100% coverage

#### Step 3.2: Core Visualization Components
- **Description:** Implement reusable chart components using matplotlib/plotly.

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test chart generation
  - **Test File:** `lens/tests/test_charts.py`
  - **Test Cases:**
    - Test timeline chart generation
    - Test bar chart generation
    - Test pie chart generation
    - Test scatter plot generation
    - Test custom styling
    - Test export to PNG/SVG
  - **Success Criteria:** All chart types render correctly, 95% coverage

#### Step 3.3: Analysis Dashboards
- **Description:** Implement pre-built dashboards for common analysis tasks.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test dashboard generation
  - **Test File:** `lens/tests/test_dashboards.py`
  - **Test Cases:**
    - Test build performance dashboard
    - Test warning trends dashboard
    - Test success rate dashboard
    - Test target analysis dashboard
    - Test compiler comparison dashboard
    - Test dashboard customization
  - **Success Criteria:** Dashboards generate useful visualizations, 90% coverage

#### Step 3.4: Interactive Web Interface (Optional)
- **Description:** Implement web-based dashboard using Flask/FastAPI + React/Vue.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test web interface
  - **Test File:** `lens/tests/test_web_interface.py`
  - **Test Cases:**
    - Test Flask/FastAPI server startup
    - Test API endpoints for data
    - Test frontend rendering
    - Test interactive filtering
    - Test real-time updates
    - Test authentication (if needed)
  - **Success Criteria:** Web interface functional and responsive, 85% coverage

#### Step 3.5: CLI & Export Tools
- **Description:** Implement Lens CLI for generating reports from command line.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test CLI and export functionality
  - **Test File:** `lens/tests/test_cli.py`
  - **Test Cases:**
    - Test `lens dashboard <type>` command
    - Test `lens analyze <build-id>` command
    - Test `lens export` command with various formats
    - Test `lens serve` command for web interface
    - Test custom query syntax
    - Test output file handling
  - **Success Criteria:** CLI functional, exports work, 100% coverage

### Success Criteria
- **Overall:** Lens provides rich visualizations of Forge data, generates useful insights, exports in multiple formats. Test coverage ≥90%.

---

## Component 4: Forge - Packaging & Distribution

**Goal:** Complete Forge's distribution pipeline and CI/CD automation (moved from Iteration 1).

### Steps

#### Step 4.1: Packaging & Installation
- **Description:** Create setup.py/pyproject.toml for pip installation, test installation process.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test installation and package integrity
  - **Test File:** `forge/tests/test_installation.py`
  - **Test Cases:**
    - Test pip install in clean virtual environment
    - Test forge command is available after install
    - Test --version shows correct version
    - Test --help shows documentation
    - Test uninstall removes all files
    - Test upgrade from previous version
    - Test dependency installation
    - Test entry point configuration
  - **Success Criteria:** Package installs cleanly, all commands work, uninstall is clean, 100% coverage

#### Step 4.2: CI/CD Pipeline
- **Description:** Set up GitHub Actions for automated testing, building, and release.

- **Testing Approach:**
  - **Test Type:** CI/CD validation
  - **Test Description:** Validate CI/CD pipeline configuration
  - **Test Cases:**
    - Test CI runs on all commits
    - Test CI runs on all platforms (Linux, Windows, macOS)
    - Test CI fails on test failures
    - Test coverage reporting works
    - Test automatic release creation
    - Test package publication to PyPI (test)
    - Test badge generation for README
    - Test automated changelog generation
  - **Success Criteria:** CI/CD pipeline runs automatically, all tests pass, releases automated, 100% validation

#### Step 4.3: Multi-tool CI/CD Integration
- **Description:** Integrate Anvil, Scout, and Lens into CI/CD pipeline.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test multi-tool CI workflow
  - **Test Cases:**
    - Test Anvil pre-commit checks in CI
    - Test Scout failure analysis on CI failures
    - Test Lens report generation in CI
    - Test artifact publication (build reports, dashboards)
    - Test cross-tool data flow
  - **Success Criteria:** All tools work together in CI, reports published, 95% coverage

### Success Criteria
- **Overall:** Forge is packaged, distributed via PyPI, and fully automated with CI/CD. All Argos tools integrate seamlessly.

---

## Integration & Cross-Component Features

### Step 5.1: Unified Configuration
- **Description:** Implement unified configuration file (argos.toml) for all tools.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test configuration sharing across tools
  - **Test File:** `tests/integration/test_unified_config.py`
  - **Test Cases:**
    - Test argos.toml parsing
    - Test tool-specific sections (forge, anvil, scout, lens)
    - Test configuration inheritance
    - Test environment variable overrides
    - Test configuration validation
  - **Success Criteria:** All tools read from unified config, 100% coverage

### Step 5.2: Shared Libraries
- **Description:** Extract common functionality into argos-core library.

- **Testing Approach:**
  - **Test Type:** Unit tests
  - **Test Description:** Test shared library functions
  - **Test File:** `argos-core/tests/test_common.py`
  - **Test Cases:**
    - Test common CLI utilities
    - Test common output formatting
    - Test common database access patterns
    - Test common configuration handling
    - Test common logging setup
  - **Success Criteria:** Shared code eliminates duplication, 100% coverage

### Step 5.3: Tool Interoperability
- **Description:** Implement data exchange and workflow integration between tools.

- **Testing Approach:**
  - **Test Type:** Integration tests
  - **Test Description:** Test tool-to-tool integration
  - **Test File:** `tests/integration/test_interoperability.py`
  - **Test Cases:**
    - Test Forge → Lens data flow (build data → visualization)
    - Test Forge → Scout integration (CI builds → failure analysis)
    - Test Anvil → Forge integration (quality gates → build gating)
    - Test unified CLI (`argos forge`, `argos anvil`, etc.)
    - Test data format compatibility
  - **Success Criteria:** Tools work together seamlessly, 95% coverage

---

## Documentation & Examples

### Step 6.1: Component Documentation
- **Description:** Write comprehensive documentation for each component.

- **Deliverables:**
  - Anvil User Guide (anvil/docs/USER_GUIDE.md)
  - Scout User Guide (scout/docs/USER_GUIDE.md)
  - Lens User Guide (lens/docs/USER_GUIDE.md)
  - API documentation for each component
  - Integration guide for all tools together

- **Testing Approach:**
  - Test all documentation examples
  - Validate all commands work as documented
  - Test tutorials end-to-end

### Step 6.2: Example Workflows
- **Description:** Create example workflows showing tool integration.

- **Examples:**
  - Complete CI/CD workflow with all tools
  - Local development workflow with Anvil + Forge
  - Failure investigation workflow with Scout + Lens
  - Performance optimization workflow with Forge + Lens

### Step 6.3: Video Tutorials (Optional)
- **Description:** Create video tutorials for key workflows.

- **Topics:**
  - Getting started with Argos
  - Setting up Anvil pre-commit hooks
  - Investigating CI failures with Scout
  - Visualizing build trends with Lens

---

## Summary

### Development Timeline

- **Component 1 (Anvil)**: 3 weeks
- **Component 2 (Scout)**: 3 weeks
- **Component 3 (Lens)**: 4 weeks
- **Component 4 (Forge Packaging)**: 1 week
- **Integration & Documentation**: 2 weeks

**Total Estimated Time**: 13 weeks

### Test Coverage Goals

- **Anvil**: ≥95% coverage
- **Scout**: ≥90% coverage
- **Lens**: ≥90% coverage
- **Forge Packaging**: 100% coverage
- **Integration Tests**: ≥95% coverage

### Key Deliverables

1. **Anvil** - Pre-commit validation tool with git hook integration
2. **Scout** - CI/CD inspection and failure analysis tool
3. **Lens** - Build data visualization and analytics dashboard
4. **Forge** - Complete packaging and CI/CD automation
5. **Argos Core** - Shared library for all tools
6. **Unified Documentation** - Complete guides for all tools
7. **Example Workflows** - Real-world integration examples

### Architecture

```
argos/
├── forge/          # CMake build wrapper (Iteration 1)
├── anvil/          # Pre-commit validation tool
├── scout/          # CI/CD inspection tool
├── lens/           # Data visualization dashboard
├── argos-core/     # Shared libraries and utilities
├── docs/           # Cross-component documentation
├── examples/       # Example workflows and integrations
└── tests/
    └── integration/  # Cross-component integration tests
```

---

## Next Steps

1. Complete Forge Iteration 1 (prerequisite)
2. Review Iteration 2 plan with team
3. Decide on tool naming (Anvil, Scout, Lens or alternatives)
4. Set up component directories and structure
5. Begin with Anvil (most critical for quality)
6. Follow TDD approach for all components
7. Integrate as components are completed

---

**Plan Version**: 2.0
**Created**: 2026-01-29
**Status**: Ready for implementation
**Prerequisites**: Forge Iteration 1 complete
