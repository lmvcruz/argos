# Lens UI Specification v2

**Version:** 2.0
**Date:** February 2026
**Status:** In Development
**Focus:** Project-based architecture with improved UX and integrated logging

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Page Specifications](#page-specifications)
4. [User Interface Guidelines](#user-interface-guidelines)
5. [Logging Architecture](#logging-architecture)
6. [Technical Considerations](#technical-considerations)

---

## Overview

Lens is a **visual inspection and analysis platform** for CI/CD execution data and local code validation. The redesigned Lens UI introduces a project-based workflow that allows users to manage, analyze, and debug local code and CI executions seamlessly.

### Key Principles

- **Project-Centric**: All operations are scoped to a project (local folder + remote repo)
- **Progressive Disclosure**: Complex features are revealed only when relevant
- **Minimal Aesthetics**: Clean, functional design with subtle improvements
- **Integrated Logging**: All activities logged to `~/.lens/logs/` for debugging
- **Two-Column Layout**: Consistent pattern across all pages for predictability

### Core Concepts

**Project**: A configuration that ties together:
- Local source code folder (for local inspection/testing)
- Remote GitHub repository (owner/repo)
- Personal access token (for CI access)
- Optional custom storage location (default: `~/.scout/<owner>/<repo>/`)

---

## Architecture

### Page Structure

```
Lens UI
├── Navigation Bar (Top)
│   ├── Project Selector
│   ├── Page Tabs
│   └── Settings/Help
├── Content Area (4 Pages)
│   ├── 1. Config Page
│   ├── 2. Local Inspection Page
│   ├── 3. Local Tests Page
│   └── 4. CI Inspections Page
└── Footer (Status)
    └── Logs indicator
```

### Component Reusability

**Common Components** (used across multiple pages):

1. **TwoColumnLayout**
   - Left sidebar (tree/list views)
   - Right panel (forms/results)
   - Configurable widths (adjustable splitter)

2. **ExpandableForm**
   - Collapsible header
   - Form fields
   - Submit button
   - Status/error messages

3. **TreeView**
   - Hierarchical data display
   - Selection support (visual feedback)
   - Expandable/collapsible nodes
   - Optional filtering

4. **StatusCard**
   - Shows success/error/loading states
   - Icon + message + action button
   - Dismissible

---

## Page Specifications

### Page 1: Config

**Purpose**: Manage projects and Lens configuration
**Navigation**: First tab in navigation bar
**Layout**: Single column (no two-column layout)

#### Subsections

##### A. Project List

**Container**: Left section
- **Display**: List of saved projects
- **Item Structure**:
  - Project name
  - Repo (owner/repo)
  - Local folder path
  - Quick action buttons (Select / Edit / Delete)
- **Empty State**: "No projects yet. Create one to get started."

**Interactions**:
- **Click on project**: Sets project as active (stored in localStorage)
- **Edit button**: Opens project editor (see below)
- **Delete button**: Removes project (with confirmation)
- **Active indicator**: Highlight current active project

##### B. Create/Edit Project Form

**Trigger**: "New Project" button above the project list

**Form Fields** (in order):

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| Project Name | Text input | Yes | User-friendly name (e.g., "MyApp") |
| Local Folder | Folder picker | Yes | Path to source code directory |
| Repository | Text input | Yes | Format: `owner/repo` (e.g., lmvcruz/argos) |
| GitHub Token | Password input | No | Leave blank to use env var or .scoutrc |
| Storage Location | Folder picker | No | Default: `~/.scout` |

**Form States**:
- **Create mode**: Empty fields, title "Create New Project"
- **Edit mode**: Pre-filled fields, title "Edit Project"
- **Saving**: Submit button disabled, spinner shown
- **Success**: Form hidden, project added/updated to list
- **Error**: Error message displayed above form, form remains visible

**UI Pattern** (choose one based on preference):
- **Option A**: Modal popup (recommended for focus)
- **Option B**: Embedded panel (slides in from side)

---

### Page 2: Local Inspection

**Purpose**: Analyze local source code using Anvil validators
**Navigation**: Second tab
**Layout**: Two columns (splitter)
**Prerequisite**: Active project with local folder configured

#### Left Column: Source Tree

**Content**: File/folder tree of local source directory

**Features**:

1. **Filtering**
   - **Location**: Above the tree
   - **Filter Types** (radio buttons or toggle):
     - **Inclusive**: Show only files matching pattern (e.g., `*.py`)
     - **Exclusive**: Hide files matching pattern (e.g., `*.md;*.txt`)
   - **Input field**: Pattern entry (supports wildcards)
   - **Apply button**: Refresh tree with filter

2. **Selection**
   - **Visual feedback**: Highlight selected node (background color change)
   - **File icon**: Show file type icons
   - **Multi-select**: Optional (Ctrl+Click)

3. **Tree Actions**
   - **Expand/collapse**: Arrows on folders
   - **Double-click**: Expand/collapse

#### Right Column: Analysis Tools

Two expandable forms (collapsible sections):

##### Form 1: Check

**Purpose**: Run Anvil validators on selected file/directory

**Controls**:

1. **Language Dropdown**
   - Options: All Languages, Python, C++
   - Default: All Languages
   - Updates validator options

2. **Validator Dropdown**
   - Options: Filtered by selected language
   - Shows available validators for language
   - Disabled if "All Languages" selected (or shows all)

3. **Action Button**: "Run Check"
   - Disabled until file/directory is selected
   - Shows spinner during execution

**Results Area**:
- **Location**: Below button
- **Content**:
  - Status message (Checking... / Success / Error)
  - List of issues found (if any)
  - No issues message (if successful)
  - Export button (export as JSON/CSV - future enhancement)

##### Form 2: Stats

**Purpose**: Show database statistics

**Content**:
- Number of files analyzed
- Number of issues found (by severity: Error / Warning / Info)
- Last updated timestamp
- Refresh button

---

### Page 3: Local Tests

**Purpose**: Run and analyze local test suites
**Navigation**: Third tab
**Layout**: Two columns (identical to Local Inspection)
**Prerequisite**: Active project with local folder configured

#### Left Column: Test Tree

**Content**: Hierarchical view of tests discovered in local folder

**Structure**:
```
Test Suite
├── Test File 1
│   ├── Test 1 (passing)
│   ├── Test 2 (failing)
│   └── Test 3 (skipped)
├── Test File 2
│   └── Test 1
└── ...
```

**Visual Indicators**:
- ✅ Passing test (green icon)
- ❌ Failing test (red icon)
- ⊘ Skipped test (gray icon)
- (No indicator) Not yet run

**Features**:
- Click test to view details
- Expand/collapse test files

#### Right Column: Test Analysis

Two expandable forms:

##### Form 1: Run Tests

**Controls**:

1. **Scope Selector** (radio buttons):
   - All Tests
   - Selected File
   - Selected Test Only
   - (Disabled if nothing selected)

2. **Filter** (optional):
   - Match pattern (e.g., `test_*.py`)

3. **Action Button**: "Run Tests"
   - Shows spinner during execution
   - Disabled if nothing selected

**Results Area**:
- Test execution summary
  - Total: X
  - Passed: X ✅
  - Failed: X ❌
  - Skipped: X ⊘
- Detailed results (if any failures)
  - Test name
  - Duration
  - Error message (expandable)
- Export results button

##### Form 2: Stats

**Content**:
- Total tests found
- Tests passed / failed / skipped (with counts)
- Average test duration
- Coverage percentage (if available)
- Last run timestamp

---

### Page 4: CI Inspections

**Purpose**: Explore CI execution data from GitHub Actions
**Navigation**: Fourth tab
**Layout**: Two columns
**Prerequisite**: Active project with repo configured

#### Left Column: Executions Tree

**Initial State** (empty database):
- Message: "No executions fetched yet"
- Action Button: "Fetch Executions from GitHub"
  - Calls Scout to fetch workflow runs
  - Shows progress spinner
  - Updates tree when complete

**After Data Loaded**:

```
Workflow Executions
├── test.yml
│   ├── Run #123 (2025-02-01 14:32) ✅
│   │   ├── Job 1: test-python
│   │   ├── Job 2: test-cpp
│   │   └── Job 3: lint
│   ├── Run #122 (2025-01-31 09:15) ❌
│   │   ├── Job 1: test-python
│   │   ├── Job 2: test-cpp
│   │   └── Job 3: lint
│   └── ...
└── ci-integration.yml
    ├── Run #50 ✅
    └── ...
```

**Visual Indicators**:
- ✅ Passed (green)
- ❌ Failed (red)
- ⏳ In Progress (orange)
- ⊘ Skipped (gray)

**Features**:
- Click run to select
- Expand run to see jobs
- Click job to view logs/data

#### Right Column: Execution Details

Two expandable forms (shown only when run/job selected):

##### Form 1: Log Viewer

**Content**:
- **Status**:
  - ✅ "Log available in database"
  - ⚠️ "Log not yet fetched. Click 'Fetch Log' to retrieve."

- **Fetch Button** (if log not available):
  - Downloads log from GitHub
  - Caches in `~/.scout/<owner>/<repo>/logs/`
  - Shows spinner during download

- **Log Display** (if available):
  - Text area with log content (read-only)
  - Scrollable
  - Line numbers
  - Copy button
  - Download button

- **Empty State** (if no data):
  - "Select a run or job to view logs"

##### Form 2: Parsed Data

**Content**:
- **Status**:
  - ✅ "Parsed data available in database"
  - ⚠️ "Data not yet parsed. Click 'Parse Logs' to extract test results."
  - ⚠️ "No logs available. Fetch logs first."

- **Parse Button** (if log available but not parsed):
  - Calls Scout to parse logs
  - Extracts test results
  - Shows spinner during parsing
  - Stores results in database

- **Data Display** (if available):
  - Test summary table:
    - Test name
    - Status (✅ passed / ❌ failed / ⊘ skipped)
    - Duration
    - Error (expandable if failed)

- **Empty State** (if no data):
  - "Select a run or job to view parsed data"

---

## User Interface Guidelines

### Design Principles

1. **Minimal Aesthetics**
   - Clean whitespace
   - Subtle colors (grays, blues, minimal reds for errors)
   - Clear typography hierarchy
   - Consistent spacing (8px grid)

2. **Feedback & Responsiveness**
   - Spinners for async operations
   - Status messages (success/error/info)
   - Disabled state for unavailable actions
   - Visual selection (not just text)

3. **Accessibility**
   - Semantic HTML
   - ARIA labels where needed
   - Keyboard navigation support
   - Color not the only indicator (icons + text)

4. **Responsive Layout**
   - Splitter allows user adjustment
   - Collapses gracefully on small screens
   - Mobile-friendly stacking (future phase)

### Color Palette

| Role | Color | Usage |
|------|-------|-------|
| Primary | `#2563eb` | Buttons, links, active states |
| Success | `#16a34a` | Passing tests, successful operations |
| Error | `#dc2626` | Failures, errors, warnings |
| Warning | `#ea580c` | In progress, caution states |
| Background | `#f8fafc` | Page background |
| Surface | `#ffffff` | Cards, panels |
| Border | `#e2e8f0` | Dividers, borders |
| Text | `#1e293b` | Primary text |
| Text-light | `#64748b` | Secondary text |

### Component Styling

- **Buttons**:
  - Primary: Blue background, white text, rounded corners (4px)
  - Secondary: Gray background, dark text
  - Hover: Slightly darker shade
  - Disabled: Grayed out, cursor not-allowed

- **Forms**:
  - Input fields: Light gray border, rounded (4px), padding 8px
  - Labels: Dark text, 12px font, margin-bottom 4px
  - Required indicator: Red asterisk

- **Cards/Panels**:
  - Light background, subtle border
  - Shadow: `0 1px 2px rgba(0,0,0,0.05)`
  - Padding: 16px
  - Rounded corners: 6px

---

## Logging Architecture

### Overview

Integrated logging ensures all activities (backend + frontend) are captured for debugging without manual copy-paste.

### Log Files

**Location**: `~/.lens/logs/`

```
~/.lens/logs/
├── backend.log          (All backend API calls, errors, database operations)
├── frontend.log         (Frontend console logs, errors, user actions)
└── combined.log         (Merged logs for debugging - optional)
```

### Backend Logging

**Framework**: Python logging (scout uses this)
**Location**: `lens/backend/logging_config.py`

**Logged Events**:
- API request received (method, path, params)
- Scout command execution (command, arguments)
- Database queries (if debug mode)
- Errors and exceptions (with traceback)
- Performance metrics (request duration)

**Format**:
```
[2026-02-06 14:32:45.123] [INFO] GET /api/scout/list - lmvcruz/argos
[2026-02-06 14:32:46.456] [INFO] Executed Scout command: fetch --repo lmvcruz/argos
[2026-02-06 14:32:47.789] [ERROR] Failed to parse logs - ValueError: Invalid format
```

### Frontend Logging

**Framework**: Custom logging service (JavaScript)
**Location**: `lens/frontend/src/services/LoggingService.ts`

**Logged Events**:
- User navigation (page change)
- Form submissions (no sensitive data)
- API calls (request/response)
- Errors and exceptions
- User interactions (button clicks - optional for verbosity control)

**Format**:
```
[14:32:45.123] [INFO] Page changed: Config
[14:32:46.456] [INFO] API call: GET /api/scout/list
[14:32:47.789] [ERROR] Form submission failed: Network error
```

### Log Rotation

- **Max file size**: 10MB per file
- **Retention**: Keep last 7 days of logs
- **Compression**: Compress rotated logs to .gz

### Accessing Logs

**UI**:
- Logs indicator in footer (⚙️ icon)
- Click to open logs directory
- On macOS: Opens Finder
- On Linux: Opens file manager
- On Windows: Opens Explorer

**CLI**:
```bash
# View recent logs
tail -f ~/.lens/logs/backend.log
tail -f ~/.lens/logs/frontend.log

# Search logs
grep "ERROR" ~/.lens/logs/combined.log
```

---

## Technical Considerations

### State Management

**Frontend State** (localStorage):
- Active project ID
- Page tabs state (which page is active)
- Expanded/collapsed sections
- Filter settings
- Column widths (for splitters)

**Backend State** (database):
- Project configuration (saved in `~/.lens/projects.json` or SQLite)
- Cached data from Scout
- Analysis results

### API Endpoints

**Backend** provides REST APIs for:
- Project management (CRUD)
- Local inspection (trigger Anvil, get results)
- Local tests (run tests, get results)
- CI inspections (list runs, get logs, trigger parsing)

### Performance Considerations

- **Lazy loading**: Don't fetch all runs at once, load on demand
- **Caching**: Cache tree data with expiration
- **Debouncing**: Debounce filter input to avoid excessive updates
- **Progressive disclosure**: Show spinners for long operations

### Error Handling

- **API errors**: Show user-friendly message + option to retry
- **Validation errors**: Show inline error messages on forms
- **Network errors**: Retry with exponential backoff
- **All errors logged**: To `~/.lens/logs/` for debugging

---

## Future Enhancements

### Phase 2

- Export results (JSON, CSV, PDF)
- Custom report generation
- Comparison between runs
- Historical trends

### Phase 3

- Multi-language support
- Dark mode
- Real-time test execution with live updates
- Integration with issue tracking (GitHub Issues)
- Slack notifications

---

## Success Criteria

✅ Config page allows creating/managing projects
✅ Local Inspection displays source tree with filtering
✅ Local Tests shows test hierarchy and execution
✅ CI Inspections displays execution tree with log/data viewers
✅ All logs captured to `~/.lens/logs/`
✅ Two-column layout consistent across all pages
✅ Basic CSS improves aesthetics without being "fancy"
✅ No manual log copy-paste needed for debugging

