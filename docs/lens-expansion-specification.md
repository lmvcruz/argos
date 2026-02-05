# Lens Expansion Specification

**Version:** 1.0
**Date:** February 2026
**Status:** Design Phase

---

## 1. Overview

Lens will become a comprehensive multi-tool interface for inspecting, building, testing, and executing code across local and remote environments. The system will be extensible, configuration-driven, and provide unified output visualization.

### Core Principles
- **Extensible**: Easily add new scenarios and tools
- **Configurable**: Enable/disable features, set parameters, save presets
- **Unified UI**: Consistent output visualization across all tools
- **Tool Agnostic**: Integrate Anvil, Scout, Gaze, Forge, Verdict seamlessly

---

## 2. Scenarios & Features

### 2.1 Local Inspection

**Purpose**: Analyze local code quality, coverage, and style issues

**Core Features** (MVP):
- Tree-structure file/folder browser for selective operations
- Anvil integration:
  - Code formatting issues (Black, isort, clang-format) - *already available*
  - Linting violations (flake8, pylint, clang-tidy) - *already available*
  - Test coverage per file/folder - *already available*

**Phase 2 Enhancements** (Weeks 3-4):
- Diff preview for formatting fixes - *UI for existing Anvil output*
- Import analysis and unused imports - *Anvil already provides*
- Quick fix application (auto-format with preview) - *safe, reversible*

**Phase 3+ Enhancements** (Future):
- Coverage gap visualization (heatmap view) - *requires visualization library*
- Duplicate code detection - *requires algorithm/tool integration*
- Complexity hotspot highlighting - *requires metrics aggregation*

**Status**: Ready (Anvil integration exists, UI enhancement needed)

---

### 2.2 Local Build

**Purpose**: Configure, compile, and inspect build output

**Core Features** (MVP):
- Forge integration:
  - CMake configuration with custom parameters
  - Build execution with progress tracking
  - Compiler warnings/errors extraction and grouping
  - Build artifact inspection

**Phase 4 Enhancements** (Weeks 7-8):
- Build failure troubleshooting with suggestions - *pattern matching on errors*
- Build time tracking - *capture execution duration*

**Phase 3+ Enhancements** (Future):
- Build cache management and diagnostics - *requires CMake integration*
- Compiler warning trends (historical comparison) - *requires persistence*
- Build time analysis (file-level) - *requires tool integration*
- Dependency visualization - *requires graph parsing*
- Parallel build efficiency metrics - *requires job tracking*

**Status**: Partial (Forge CLI exists, UI integration needed)

---

### 2.3 Local Tests

**Core Features** (MVP):
- Tree-structure test discovery (folders → files → test cases)
- Test execution with filtering (by folder, file, or individual test)
- Verdict integration:
  - Test results per test case
  - Execution time tracking
  - Failure statistics and grouping

**Phase 3 Enhancements** (Weeks 5-6):
- Test result filtering and display - *organize output*
- Execution time visualization - *per-test metrics*
- Failure summary dashboard - *aggregate view*

**Phase 3+ Enhancements** (Future):
- Test history and trend analysis - *requires DB persistence*
- Flaky test detection - *requires statistical analysis*
- Test categorization (unit vs. integration) - *metadata tagging*
- Parallel test execution management - *tool feature*
- Test dependency visualization - *graph analysis*
- Performance regression detection - *baseline comparison*
- Test dependency visualization
- Performance regression detection
- Test result filtering and grouping

**Status**: Partial (Verdict integration exists, UI incomplete)

---

### 2.4 Local Execution

**Core Features** (MVP):
- Command execution with real-time output
- Output streaming with color preservation
- Execution time tracking
- Signal handling and graceful shutdown

**Phase 5 Enhancements** (Weeks 9-10):
- Log parsing and structured output (errors, warnings, info) - *simple regex matching*
- Output search and filtering - *client-side filtering*
- Environment variable inspection - *display env*

**Phase 3+ Enhancements** (Future):
- Performance profiling integration - *requires profiler tool*
- Log export (JSON, CSV, plain text) - *data serialization*
- Gaze integration (requires Gaze completion):
  - Memory consumption tracking
  - CPU usage monitoring
  - Process/thread trackingown
- Execution time tracking
- Output search and filtering
- Log export (JSON, CSV, plain text)

**Status**: Partial (Basic execution exists, monitoring incomplete)

---

### 2.5 CI Inspection

**Purpose**: Analyze CI/CD workflow execution data

**Core Features** (MVP):
- Scout integration:
  - Workflow listing and discovery
  - Run history with status
  - Job and test result access
  - Database status display (available data)

**Phase 6 Enhancements** (Weeks 11-12):
- Workflow run comparison (detect regressions) - *side-by-side view*
- Failure pattern analysis and grouping - *aggregate failures*
- Recent failure highlighting - *status display*
- **Workflow trigger capability** - *GitHub API dispatch*
  - Select workflow to run
  - Configure run inputs (branch, parameters)
  - Show trigger confirmation and result

**Phase 3+ Enhancements** (Future):
- Job dependency visualization - *graph rendering*
- Flaky CI test detection - *statistical analysis*
- Performance trend analysis - *requires historical data*
- CI artifact inspection - *requires metadata*
- Workflow execution cost analysis - *requires cost data*
- Critical path analysis - *requires timing analysis*

**Status**: Partial (Scout sync exists, UI enhancement needed)

---

### 2.6-2.9 Remote Variants (Future)

**Placeholder**: Local variants extended to remote execution via SSH/container/cloud

**Deferred to Phase 2** (after local features stabilized)

---

## 3. Configuration & Admin Panel

### 3.1 Feature Management

**Admin Interface Components**:

**Feature Toggles**:
- Enable/disable per scenario (checkbox list)
- Show availability status (enabled, unavailable, needs setup)

**Tool Configuration**:
- Per-tool settings (path, parameters, environment variables)
- Tool availability detection
- Missing dependency alerts

**Presets**:
- **Local Dev**: All local features enabled, development parameters
- **CI**: Local build/test/execution for CI validation
- **Code Review**: Inspection + build (no execution)
- **Debug**: Full local features with verbose output
- **Custom**: User-defined preset builder

### 3.2 Configuration Persistence

**Storage**:
- JSON-based configuration files in `lens/config/`
- User presets in `lens/user-presets/`
- Configuration schema validation

**Features**:
- Load/save presets via UI
- Import/export configurations
- Configuration diffing
- Reset to defaults

---

## 4. UI Architecture

### 4.1 Navigation Structure

```
Lens Dashboard
├── /admin
│   ├── Feature Toggles
│   ├── Tool Configuration
│   └── Presets Manager
├── /local-inspection
├── /local-build
├── /local-tests
├── /local-execution
├── /ci-inspection
└── /settings
```

### 4.2 Output Visualization

**Common Components**:
- **Header**: Feature name, status, execution time
- **Toolbar**: Filter, search, export, expand/collapse all
- **Main Panel**: Results tree or table
- **Details Panel**: Collapsible detailed information
- **Action Panel**: Quick actions (run, fix, export)

**Output Styling**:
- Color-coded severity (error=red, warning=yellow, info=blue, success=green)
- Code snippets with syntax highlighting
- Collapsible sections for grouping related items
- Diff highlighting for before/after comparisons

### 4.3 State Management

**Per-Scenario State**:
- Current configuration
- Last execution results
- User-selected filters
- Expanded/collapsed sections

---

## 5. Implementation Plan

### Phase 1: Foundation (Weeks 1-2)

**Priority**: High | **Effort**: Medium

**Tasks**:
1. Create configuration system (JSON file-based)
   - `lens/config/settings.json` schema for feature toggles and tool paths
   - Load configuration on app startup
   - Support environment variable overrides

2. Set up routing for scenario pages
   - Create React routes: `/local-inspection`, `/local-tests`, `/ci-inspection`
   - Navigation menu/sidebar to switch between scenarios
   - Placeholder pages for each scenario

3. Create base components for output visualization
   - `<FileTree />` - Collapsible folder/file browser
   - `<ResultsTable />` - Table display for issues/results
   - `<CodeSnippet />` - Syntax-highlighted code blocks
   - `<CollapsibleSection />` - Expandable detail panels
   - `<SeverityBadge />` - Color-coded severity indicators (error/warning/info/success)
   - `<OutputPanel />` - Real-time output stream display

4. Implement configuration context/state management
   - React Context for app-wide configuration access
   - Store loaded settings from JSON file
   - Store current scenario state (results, filters, selections)

**Deliverable**: Routable scenario pages with base components and config loading

---

### Phase 2: Local Inspection (Weeks 3-4)

**Priority**: High | **Effort**: Medium

**Tasks**:
1. Implement file tree browser component
2. Connect Anvil backend endpoints for file analysis
3. Build result visualization component
4. Add filtering and search
5. Implement quick-fix preview

**Deliverable**: Fully functional Local Inspection with file-level control

---

### Phase 3: Local Tests (Weeks 5-6)

**Priority**: High | **Effort**: High

**Tasks**:
1. Implement test discovery tree (folder → file → test)
2. Connect test execution endpoints
3. Build real-time progress tracking
4. Create statistics dashboard (pass rate, execution time)
5. Implement test filtering and selection

**Deliverable**: Functional test execution and result display

---

### Phase 4: Local Build (Weeks 7-8)

**Priority**: Medium | **Effort**: High

**Tasks**:
1. Create build configuration UI (CMake parameters)
2. Connect Forge backend for compilation
3. Implement real-time progress and output streaming
4. Build compiler error/warning extraction
5. Create build artifact inspector

**Deliverable**: Full build pipeline integration

---

### Phase 5: Local Execution (Weeks 9-10)

**Priority**: Medium | **Effort**: Medium

**Tasks**:
1. Implement command execution form
2. Create real-time output display with color support
3. Add log parsing and structuring
4. Implement memory/CPU monitoring (when Gaze ready)
5. Create output export functionality

**Deliverable**: General-purpose execution environment

---

### Phase 6: CI Inspection Enhancement (Weeks 11-12)

**Priority**: Medium | **Effort**: Medium

**Tasks**:
1. Enhance Scout sync UI with status
2. Build workflow history visualization
3. Create run comparison views
4. Implement failure pattern analysis
5. Add performance trending

**Deliverable**: Rich CI data exploration interface

---

### Phase 7: Polish & Testing (Weeks 13-14)

**Priority**: High | **Effort**: Medium

**Tasks**:
1. Integration testing across all scenarios
2. Performance optimization
3. Error handling and edge cases
4. Documentation and help system
5. User acceptance testing

**Deliverable**: Production-ready first release

---

## 6. Backend Integration Points

### Anvil Integration
- `GET /api/files/{path}/analysis` - Get file quality metrics
- `GET /api/folder/{path}/summary` - Get folder-level statistics
- `POST /api/format` - Apply formatting changes
- `GET /api/coverage/{path}` - Get coverage data

### Forge Integration
- `POST /api/build/configure` - Configure CMake
- `POST /api/build/execute` - Start build
- `WS /api/build/stream` - WebSocket for build output
- `GET /api/build/artifacts` - List build products

### Scout Integration
- `GET /api/ci/workflows` - List workflows
- `GET /api/ci/runs` - Get run history
- `POST /api/ci/sync` - Trigger data sync (existing)
- `GET /api/ci/results/{run_id}` - Detailed run results
- `POST /api/ci/workflow/dispatch` - Trigger GitHub workflow
  - Input: workflow_id, branch, parameters
  - Returns: run_id confirmation

### Verdict Integration
- `GET /api/tests/discover` - Test discovery
- `POST /api/tests/execute` - Run tests
- `WS /api/tests/stream` - WebSocket for test output
- `GET /api/tests/history` - Historical data

### Gaze Integration (Future)
- `WS /api/monitor/process` - Process monitoring stream
- `GET /api/monitor/summary` - Resource summary

---

## 7. Feature Priority & Dependencies

### Tier 1 (MVP - Weeks 1-6)
- Configuration system ✓
- Admin panel ✓
- Local Inspection ✓
- Local Tests ✓

### Tier 2 (Phase - Weeks 7-10)
- Local Build
- Local Execution
- Enhanced CI Inspection

### Tier 3 (Future)
- Remote variants
- Advanced analytics
- Performance profiling
- Gaze integration

---

## 8. Success Criteria

✓ All 4 core local scenarios implemented and tested
✓ Configuration system allows enabling/disabling features
✓ Presets simplify common workflows
✓ Output visualization consistent and readable
✓ 90%+ feature availability in target environment
✓ Sub-second response times for UI interactions
✓ Clear error messages and recovery guidance

---

## 9. Open Questions & Considerations

1. **Test Discovery**: Verdict CLI capabilities for test discovery?
2. **Output Streaming**: Should all tools support real-time output via WebSocket?
3. **Authentication**: How to handle remote execution authentication in future?
4. **Performance**: Polling vs. WebSocket for long-running operations?
5. **Storage**: Where to persist execution history (SQLite, PostgreSQL)?

---

## 10. Future Enhancements (Phase 2+)

- Mobile-responsive UI for remote viewing
- Dark mode and theme customization
- Keyboard shortcuts for power users
- CLI companion tool (run same commands from terminal)
- Integration with IDE (VS Code extension)
- Webhook support for CI notifications
- Machine learning for anomaly detection
- Team collaboration features (shared presets, run sharing)

