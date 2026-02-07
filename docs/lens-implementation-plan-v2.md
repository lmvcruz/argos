# Lens UI Implementation Plan

**Version:** 1.0
**Date:** February 2026
**Status:** Planning Phase
**Timeline:** 3-4 weeks (estimated)

---

## Table of Contents

1. [Phase Overview](#phase-overview)
2. [Phase 1: Project Infrastructure](#phase-1-project-infrastructure)
3. [Phase 2: Config Page & State Management](#phase-2-config-page--state-management)
4. [Phase 3: Local Inspection Page](#phase-3-local-inspection-page)
5. [Phase 4: Local Tests & CI Pages](#phase-4-local-tests--ci-pages)
6. [Phase 5: Integration & Polish](#phase-5-integration--polish)
7. [Implementation Details](#implementation-details)
8. [Risk Mitigation](#risk-mitigation)

---

## Phase Overview

| Phase | Duration | Focus | Deliverable |
|-------|----------|-------|-------------|
| 1 | 3-4 days | Backend architecture, logging, project storage | `RepoDataManager` refactor for Lens |
| 2 | 4-5 days | Config page, project management, state | Working project creation & selection |
| 3 | 5-6 days | Local Inspection, file tree, validators | Anvil integration complete |
| 4 | 5-6 days | Local Tests, CI Inspections, parsing | All 4 pages functional |
| 5 | 3-4 days | Styling, logging, testing, documentation | Production-ready UI |
| **Total** | **3-4 weeks** | Complete redesign | Fully functional Lens UI v2 |

---

## Phase 1: Project Infrastructure

### Goals

- Set up Lens logging infrastructure
- Create project storage mechanism
- Refactor backend to support projects
- Establish database schema

### Tasks

#### 1.1 Logging Infrastructure

**File**: `lens/backend/logging_config.py` (NEW)

```python
"""
Centralized logging configuration for Lens backend.

Configures both file-based and console logging with proper rotation.
"""

import logging
import logging.handlers
from pathlib import Path

# Details in Implementation Details section
```

**What it does**:
- Initializes Python logging to `~/.lens/logs/backend.log`
- Sets up log rotation (10MB, 7 day retention)
- Configures format: `[TIMESTAMP] [LEVEL] message`
- Provides logger instance for all modules

**File**: `lens/frontend/src/services/LoggingService.ts` (NEW)

**What it does**:
- JavaScript logging to IndexedDB (temporary storage)
- Exports logs to `~/.lens/logs/frontend.log` on demand
- Captures console errors automatically
- Provides `log()`, `error()`, `info()`, `warn()` methods

#### 1.2 Project Storage

**File**: `lens/backend/models/project.py` (NEW)

**Database Schema** (SQLite):

```sql
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    local_folder TEXT NOT NULL,
    repo TEXT NOT NULL,  -- owner/repo
    token TEXT,  -- Optional
    storage_location TEXT,  -- Default: ~/.scout
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE active_project (
    project_id INTEGER PRIMARY KEY,
    FOREIGN KEY (project_id) REFERENCES projects(id)
);
```

**Dataclass**:
```python
@dataclass
class Project:
    name: str
    local_folder: str
    repo: str
    token: Optional[str] = None
    storage_location: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
```

**Methods**:
- `save()` - Save to database
- `load()` - Load by ID
- `list_all()` - Get all projects
- `set_active()` - Set active project
- `get_active()` - Get active project
- `delete()` - Delete project

#### 1.3 Backend Refactor

**File**: `lens/backend/database.py` (MODIFY)

**Changes**:
- Initialize SQLite database at `~/.lens/projects.db`
- Add project tables
- Create migration system for schema updates

**File**: `lens/backend/app.py` (MODIFY)

**Changes**:
- Import logging configuration
- Initialize logging at startup
- Add project-related routes (GET, POST, DELETE)
- Error handling with logging

### Subtasks

- [ ] Create logging configuration (backend)
- [ ] Create logging service (frontend)
- [ ] Create project data model
- [ ] Set up projects database
- [ ] Add migration system
- [ ] Write tests for project storage
- [ ] Test logging output
- [ ] Commit Phase 1

**Duration**: 3-4 days
**Git Commits**: 3-5 commits (one per major feature)

---

## Phase 2: Config Page & State Management

### Goals

- Implement Config page UI
- Create project management workflow
- Set up state management (localStorage)
- Connect frontend to backend APIs

### Tasks

#### 2.1 Frontend State Management

**File**: `lens/frontend/src/context/ProjectContext.tsx` (NEW)

```typescript
interface ProjectContextType {
  projects: Project[];
  activeProject: Project | null;
  loading: boolean;
  error: string | null;

  createProject(project: Project): Promise<void>;
  updateProject(id: number, project: Partial<Project>): Promise<void>;
  deleteProject(id: number): Promise<void>;
  selectProject(id: number): void;
  loadProjects(): Promise<void>;
}

const ProjectContext = createContext<ProjectContextType | null>(null);
export const ProjectProvider: React.FC = ({ children }) => { ... };
export const useProjects = () => { ... };
```

**What it does**:
- Manages projects state globally
- Handles API calls to backend
- Persists active project to localStorage
- Provides error handling

#### 2.2 Config Page Component

**File**: `lens/frontend/src/pages/ConfigPage.tsx` (NEW)

**Components**:
- `ProjectList` - Display projects with actions
- `ProjectForm` - Create/Edit project form
- `ProjectListItem` - Individual project row
- `ConfigPage` - Main page container

**Features**:
- Show list of projects
- Create new project (button + form)
- Edit project (modal/panel)
- Delete project (with confirmation)
- Visual indicator for active project

#### 2.3 Navigation & Layout

**File**: `lens/frontend/src/components/Navigation.tsx` (MODIFY)

**Changes**:
- Add tab navigation (Config, Local Inspection, Local Tests, CI Inspections)
- Add project selector dropdown
- Add settings menu (logs, help)
- Connect to ProjectContext for active project

**File**: `lens/frontend/src/layouts/AppLayout.tsx` (NEW)

**What it does**:
- Provides consistent layout structure
- Navigation bar + content area
- Footer with logs indicator

#### 2.4 API Integration

**File**: `lens/backend/routes/projects.py` (NEW)

**Endpoints**:
```
GET    /api/projects           # List all projects
POST   /api/projects           # Create project
GET    /api/projects/:id       # Get project
PUT    /api/projects/:id       # Update project
DELETE /api/projects/:id       # Delete project
GET    /api/projects/active    # Get active project
POST   /api/projects/:id/select # Set active project
```

**Backend Logic**:
- Input validation (required fields, path existence, repo format)
- Token validation (optional)
- Database operations with error handling
- Logging all operations

### Subtasks

- [ ] Create ProjectContext and provider
- [ ] Implement ProjectList component
- [ ] Implement ProjectForm component
- [ ] Create ConfigPage
- [ ] Update Navigation bar
- [ ] Create AppLayout
- [ ] Implement backend API routes
- [ ] Add input validation
- [ ] Write tests for state management
- [ ] Test project CRUD operations
- [ ] Commit Phase 2

**Duration**: 4-5 days
**Git Commits**: 4-6 commits

---

## Phase 3: Local Inspection Page

### Goals

- Implement file tree with filtering
- Connect Anvil validator
- Display validation results
- Create two-column layout pattern

### Tasks

#### 3.1 File Tree Component

**File**: `lens/frontend/src/components/FileTree.tsx` (NEW)

**Features**:
- Hierarchical file/folder display
- Expand/collapse nodes
- Selection with visual feedback
- Filter input (inclusive/exclusive patterns)
- Icon support (folder, file types)

**Props**:
```typescript
interface FileTreeProps {
  rootPath: string;
  onSelect: (path: string) => void;
  onFilter: (pattern: string, type: 'include' | 'exclude') => void;
}
```

#### 3.2 Validation Form & Results

**File**: `lens/frontend/src/components/ValidationForm.tsx` (NEW)

**Features**:
- Language selector (All Languages, Python, C++)
- Validator selector (filtered by language)
- "Run Check" button
- Results display (issues list)
- Export button

**Props**:
```typescript
interface ValidationFormProps {
  selectedFile: string | null;
  onValidate: (language: string, validator: string) => Promise<void>;
}
```

#### 3.3 Stats Display

**File**: `lens/frontend/src/components/StatsCard.tsx` (NEW)

**Features**:
- Number of files analyzed
- Issue count by severity
- Last updated timestamp
- Refresh button

#### 3.4 Local Inspection Page

**File**: `lens/frontend/src/pages/LocalInspectionPage.tsx` (NEW)

**Layout**: Two columns with splitter
- Left: FileTree component
- Right: ValidationForm + StatsCard (stacked)

#### 3.5 Anvil Integration

**File**: `lens/backend/services/anvil_service.py` (NEW)

**What it does**:
- Wraps Anvil functionality
- Takes file/directory path
- Takes language and validator
- Returns validation results
- Logs all operations

**Methods**:
```python
class AnvilService:
    def get_supported_languages() -> List[str]
    def get_validators_for_language(language: str) -> List[str]
    def validate(path: str, language: str, validator: str) -> ValidationResult
```

#### 3.6 Backend API

**File**: `lens/backend/routes/inspection.py` (NEW)

**Endpoints**:
```
GET    /api/inspection/languages           # Supported languages
GET    /api/inspection/validators?lang=... # Validators for language
POST   /api/inspection/validate            # Run validation
GET    /api/inspection/files?path=...      # List files in directory
```

### Subtasks

- [ ] Create FileTree component
- [ ] Add tree filtering logic
- [ ] Implement ValidationForm
- [ ] Create StatsCard component
- [ ] Build LocalInspectionPage
- [ ] Create AnvilService
- [ ] Implement backend API routes
- [ ] Add error handling
- [ ] Write component tests
- [ ] Test Anvil integration
- [ ] Commit Phase 3

**Duration**: 5-6 days
**Git Commits**: 5-7 commits

---

## Phase 4: Local Tests & CI Pages

### Goals

- Implement Local Tests page with test discovery
- Implement CI Inspections with execution tree
- Create log viewer and data parser integration
- Reuse two-column pattern

### Tasks

#### 4.1 Test Discovery & Tree

**File**: `lens/frontend/src/components/TestTree.tsx` (NEW)

**Features**:
- Hierarchical test display
- Status indicators (passing, failing, skipped, not-run)
- Expand/collapse test files
- Click to select and view details

#### 4.2 Test Execution

**File**: `lens/backend/services/test_service.py` (NEW)

**What it does**:
- Discovers tests in project
- Runs tests (all, file, single)
- Parses test output
- Returns results with details

**Methods**:
```python
class TestService:
    def discover_tests(path: str) -> List[Test]
    def run_tests(path: str, scope: str, filter: str) -> TestResults
    def get_test_stats(path: str) -> TestStats
```

#### 4.3 Local Tests Page

**File**: `lens/frontend/src/pages/LocalTestsPage.tsx` (NEW)

**Layout**: Two columns (same as Local Inspection)
- Left: TestTree
- Right: TestForm (run tests) + StatsCard

#### 4.4 Execution Tree (CI Inspections)

**File**: `lens/frontend/src/components/ExecutionTree.tsx` (NEW)

**Features**:
- Workflow runs grouped by workflow
- Status indicators
- Expandable runs with jobs
- Click job to select and view logs

#### 4.5 Log Viewer & Parser

**File**: `lens/frontend/src/components/LogViewer.tsx` (NEW)

**Features**:
- Display raw log content
- Line numbers
- Scrollable text area
- Copy button
- Download button

**File**: `lens/frontend/src/components/ParsedDataViewer.tsx` (NEW)

**Features**:
- Display parsed test results
- Table format (test name, status, duration, error)
- Expandable error messages

#### 4.6 CI Inspections Page

**File**: `lens/frontend/src/pages/CIInspectionsPage.tsx` (NEW)

**Layout**: Two columns
- Left: ExecutionTree with "Fetch Executions" button
- Right: LogViewer + ParsedDataViewer (tabs)

#### 4.7 Scout Integration Service

**File**: `lens/backend/services/scout_service.py` (NEW)

**What it does**:
- Wraps Scout commands
- Fetches executions from GitHub
- Fetches and parses logs
- Handles errors gracefully

**Methods**:
```python
class ScoutService:
    def get_executions(owner: str, repo: str) -> List[Execution]
    def get_execution_log(owner: str, repo: str, run_id: int, job_id: int) -> str
    def parse_logs(owner: str, repo: str, run_id: int, job_id: int) -> ParsedData
```

#### 4.8 CI Inspection API

**File**: `lens/backend/routes/ci_inspection.py` (NEW)

**Endpoints**:
```
GET    /api/ci/executions           # List execution runs
POST   /api/ci/fetch-execution      # Fetch from GitHub
GET    /api/ci/logs/:run/:job       # Get cached log
POST   /api/ci/parse-logs           # Parse log data
GET    /api/ci/parsed-data/:run/:job # Get parsed results
```

### Subtasks

- [ ] Create TestTree component
- [ ] Implement test discovery service
- [ ] Implement test execution
- [ ] Build LocalTestsPage
- [ ] Create ExecutionTree component
- [ ] Build LogViewer component
- [ ] Build ParsedDataViewer component
- [ ] Create CIInspectionsPage
- [ ] Wrap Scout commands (scout_service.py)
- [ ] Implement backend CI routes
- [ ] Write tests for test service
- [ ] Test Scout integration
- [ ] Commit Phase 4

**Duration**: 5-6 days
**Git Commits**: 6-8 commits

---

## Phase 5: Integration & Polish

### Goals

- Implement styling and layout
- Complete logging integration
- Testing and bug fixes
- Documentation and deployment

### Tasks

#### 5.1 CSS & Styling

**Files**:
- `lens/frontend/src/styles/global.css` (MODIFY)
- `lens/frontend/src/styles/theme.css` (NEW)
- Component-level CSS modules (per component)

**What to do**:
- Define color palette (use spec values)
- Add spacing utilities (8px grid)
- Style buttons, forms, cards
- Add splitter styling
- Add responsive breakpoints
- Add hover/focus states
- Test on different screen sizes

#### 5.2 Frontend Logging Integration

**File**: `lens/frontend/src/services/LoggingService.ts` (COMPLETE)

**What to add**:
- Export logs to file (`~/.lens/logs/frontend.log`)
- Log user navigation
- Log API calls (request/response)
- Log form submissions
- Log errors with stack traces
- Add verbosity settings

#### 5.3 Logs Indicator & Access

**File**: `lens/frontend/src/components/Footer.tsx` (NEW)

**Features**:
- Logs icon in footer
- Click to open logs directory
- Show last log entry (hover tooltip)
- Logs count

#### 5.4 Error Handling & Validation

**File**: `lens/frontend/src/hooks/useApi.ts` (NEW)

**What it does**:
- Reusable API call hook
- Error handling
- Loading states
- Retry logic
- Automatic logging

#### 5.5 Testing

**Test Files** (per component):
- `*.test.tsx` for React components
- `*_test.py` for Python services

**Coverage targets**:
- Components: 80%+
- Services: 90%+
- Overall: 85%+

**Test types**:
- Unit tests (component logic)
- Integration tests (API + component)
- E2E tests (user workflows)

#### 5.6 Documentation

**Files** (NEW/UPDATE):
- `lens/README.md` - Updated with new architecture
- `lens/ARCHITECTURE.md` - Component and service layout
- `lens/API.md` - Backend API documentation
- `lens/DEVELOPMENT.md` - Setup and development guide

#### 5.7 Bug Fixes & Polish

- Test all pages thoroughly
- Fix any UI issues
- Performance optimization
- Accessibility check
- Cross-browser testing

### Subtasks

- [ ] Define CSS theme and colors
- [ ] Style all components
- [ ] Test responsive layout
- [ ] Complete frontend logging
- [ ] Add logs indicator to footer
- [ ] Implement useApi hook
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Write E2E tests
- [ ] Update documentation
- [ ] Test all workflows
- [ ] Fix bugs and polish
- [ ] Commit Phase 5

**Duration**: 3-4 days
**Git Commits**: 4-5 commits

---

## Implementation Details

### Technology Stack

**Frontend**:
- React 18+ (existing)
- TypeScript
- React Router (navigation)
- CSS Modules or styled-components (styling)
- Axios (HTTP client)

**Backend**:
- FastAPI (existing)
- SQLAlchemy (ORM)
- SQLite (projects database)
- Python logging (built-in)

### Key Design Decisions

#### 1. Why localStorage for active project?

**Pros**:
- No server state needed
- Fast access
- Works offline
- Simple implementation

**Cons**:
- Single-device only

**Decision**: Use localStorage for now, migrate to server-side session if multi-device support needed later.

#### 2. Why SQLite for projects?

**Pros**:
- No external database needed
- Built-in Python support
- Easy to ship with app
- Sufficient for local data

**Cons**:
- Single-process write (fine for local app)

**Decision**: SQLite perfect for local app, migrate to PostgreSQL if multi-user support needed.

#### 3. Why two-column layout everywhere?

**Pros**:
- Consistent UX
- Familiar pattern
- Reusable splitter component
- Efficient use of space

**Cons**:
- Requires wider screen

**Decision**: Implement and optimize for wider screens, add stacking for mobile in Phase 2.

### Component Architecture

```
src/
├── pages/
│   ├── ConfigPage.tsx
│   ├── LocalInspectionPage.tsx
│   ├── LocalTestsPage.tsx
│   └── CIInspectionsPage.tsx
├── components/
│   ├── Navigation.tsx
│   ├── FileTree.tsx
│   ├── TestTree.tsx
│   ├── ExecutionTree.tsx
│   ├── ValidationForm.tsx
│   ├── LogViewer.tsx
│   ├── ParsedDataViewer.tsx
│   ├── StatsCard.tsx
│   ├── ProjectList.tsx
│   ├── ProjectForm.tsx
│   ├── Splitter.tsx
│   └── Footer.tsx
├── context/
│   └── ProjectContext.tsx
├── services/
│   ├── api.ts
│   └── LoggingService.ts
├── hooks/
│   ├── useProjects.ts
│   └── useApi.ts
├── layouts/
│   └── AppLayout.tsx
└── styles/
    ├── global.css
    └── theme.css
```

### Database Schema

```
projects.db
├── projects
│   ├── id (int, PK)
│   ├── name (text, unique)
│   ├── local_folder (text)
│   ├── repo (text)
│   ├── token (text, nullable)
│   ├── storage_location (text, nullable)
│   ├── created_at (timestamp)
│   └── updated_at (timestamp)
└── active_project
    └── project_id (int, FK)
```

---

## Risk Mitigation

### Risk 1: Tight Timeline

**Risk**: 3-4 weeks might be tight for 5 phases.

**Mitigation**:
- Prioritize core functionality (Phases 2-4)
- Defer nice-to-have features (Logs access, Export)
- Parallel work if multiple developers
- Reduce test coverage target to 80% for Phase 1-4

**Fallback**: Skip Phase 5 polish, ship MVP earlier

### Risk 2: Scout Integration Complexity

**Risk**: Scout API changes or unexpected behavior.

**Mitigation**:
- Create scout_service.py with isolated wrapper
- Comprehensive error handling
- Logging all Scout interactions
- Test with real Scout data early

**Fallback**: Use mock Scout service for UI development

### Risk 3: Performance with Large Trees

**Risk**: File/execution trees could be slow with thousands of items.

**Mitigation**:
- Implement virtual scrolling (react-window)
- Lazy load tree nodes
- Add filtering to reduce item count
- Cache tree data with expiration

**Fallback**: Load items on demand, show pagination

### Risk 4: Logging Overhead

**Risk**: Excessive logging could slow down app.

**Mitigation**:
- Use async logging (queue-based)
- Configurable verbosity levels
- Log rotation to prevent disk space issues
- Test performance impact early

**Fallback**: Lazy-load logs, disable logs by default

### Risk 5: State Management Complexity

**Risk**: Multiple sources of state (localStorage, database, props).

**Mitigation**:
- Centralize in ProjectContext
- Single source of truth per piece of data
- Clear ownership of state updates
- Document state flow

**Fallback**: Use Redux/Zustand if complexity grows

---

## Success Metrics

### Functionality

✅ All 4 pages fully implemented and working
✅ Project creation, editing, deletion working
✅ File tree displays all files correctly
✅ Validation results displayed accurately
✅ Test discovery and execution working
✅ CI executions tree populated from GitHub
✅ Log viewer shows cached logs
✅ Parsed data displayed in table format

### Quality

✅ 85%+ test coverage
✅ All linting passes (ESLint, Flake8)
✅ No console errors or warnings
✅ No unhandled API errors

### Performance

✅ Page load < 2 seconds
✅ Tree expansion < 500ms
✅ API calls < 3 seconds
✅ Logs file rotation working

### UX

✅ Visual feedback for all interactions
✅ Proper error messages
✅ All buttons/links accessible (keyboard)
✅ Responsive to 1024px width minimum

---

## Next Steps (Post-Implementation)

1. **User Testing**: Get feedback from real users
2. **Performance Optimization**: Profile and optimize hot paths
3. **Multi-Device Support**: Add mobile and tablet support
4. **Multi-User Support**: Migrate to server-side session
5. **Enhanced Logging**: Real-time log streaming
6. **Integrations**: Slack, GitHub notifications

