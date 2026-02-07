# Phase 3: Quick Reference - File Locations & Structure

## Frontend Files Created/Modified

### Components

#### FileTree Component
- **File:** `frontend/src/components/FileTree.tsx`
- **Lines:** 123
- **Status:** ✅ Existing (enhanced with styling)
- **Props:**
  - `nodes: FileTreeNode[]` - Tree structure
  - `onSelectNode?: (nodeId: string) => void` - Selection callback
  - `selectedNodeId?: string` - Currently selected node
  - `onSetAnalysisTarget?: (nodeId: string) => void` - Analysis target callback
  - `analysisTargetId?: string` - Analysis target
- **Features:**
  - Recursive rendering
  - Expand/collapse folders
  - File type icons
  - Double-click for analysis target

#### ValidationForm Component
- **File:** `frontend/src/components/ValidationForm.tsx`
- **Lines:** 302
- **Status:** ✅ NEW
- **Props:**
  - `selectedPath?: string` - Currently selected path
  - `selectedPathType?: 'file' | 'folder'` - Path type
  - `validators: Validator[]` - Available validators
  - `languages: string[]` - Available languages
  - `onValidate: (language, validator, path) => Promise<ValidationResult[]>` - Validation callback
  - `loading?: boolean` - Loading state
  - `results?: ValidationResult[]` - Validation results
- **Exports:**
  - `ValidationForm` component
  - `ValidationResult` interface
  - `Validator` interface
- **Features:**
  - Language dropdown
  - Validator dropdown (filtered by language)
  - Path display
  - Form validation
  - Results display with severity badges
  - Export to JSON
  - Error handling

#### StatsCard Component
- **File:** `frontend/src/components/StatsCard.tsx`
- **Lines:** 216
- **Status:** ✅ NEW
- **Props:**
  - `filesAnalyzed?: number` - File count
  - `errorCount?: number` - Error count
  - `warningCount?: number` - Warning count
  - `infoCount?: number` - Info count
  - `lastUpdated?: Date` - Last validation time
  - `isLoading?: boolean` - Loading state
  - `onRefresh?: () => void` - Refresh callback
  - `language?: string` - Selected language
  - `validator?: string` - Selected validator
- **Features:**
  - Statistics display in grid
  - Percentage calculations
  - Distribution bar chart
  - Relative time formatting
  - Refresh button with animation

### Pages

#### LocalInspection Page
- **File:** `frontend/src/pages/LocalInspection.tsx`
- **Lines:** 227
- **Status:** ✅ NEW (replaces old implementation)
- **Exports:**
  - `LocalInspection` (named export)
  - default export
- **State Management:**
  - `selectedNodeId: string` - Currently selected file/folder
  - `selectedPath: string` - Full path of selected item
  - `selectedPathType: 'file' | 'folder'` - Type of selected item
  - `fileNodes: FileTreeNode[]` - Project file tree
  - `validationResults: ValidationResult[]` - Validation results
  - `validators: Validator[]` - Available validators
  - `languages: string[]` - Available languages
  - `lastValidationTime: Date?` - When validation was last run
  - `isValidating: boolean` - Validation in progress
- **Event Handlers:**
  - `handleSelectNode(nodeId)` - File/folder selection
  - `handleValidate(language, validator, path)` - Run validation
- **API Calls:**
  - `GET /api/inspection/files` - Load file tree
  - `GET /api/inspection/languages` - Load languages
  - `GET /api/inspection/validators` - Load validators
  - `POST /api/inspection/validate` - Execute validation
- **Layout:**
  - Left panel (35%): FileTree
  - Right panel (65%): ValidationForm + StatsCard

### CSS Files

#### FileTree Styling
- **File:** `frontend/src/components/FileTree.css`
- **Lines:** 100+
- **Status:** ✅ NEW
- **Classes:**
  - `.file-tree` - Main container
  - `.tree-node` - Individual node
  - `.node-header` - Node content
  - `.expand-button` - Expand/collapse button
  - `.node-icon` - File/folder icon
  - `.node-name` - File/folder name
  - `.filter-bar` - Filter controls
  - `.tree-content` - Scrollable area

#### ValidationForm Styling
- **File:** `frontend/src/components/ValidationForm.css`
- **Lines:** 300+
- **Status:** ✅ NEW
- **Sections:**
  - Form section (language/validator selectors)
  - Target path display
  - Results section with list
  - Severity badges (error, warning, info)
  - Export buttons
  - Error message display
  - Loading state
  - Empty state

#### StatsCard Styling
- **File:** `frontend/src/components/StatsCard.css`
- **Lines:** 250+
- **Status:** ✅ NEW
- **Components:**
  - `.stats-card` - Main card
  - `.stat-box` - Individual stat box
  - `.stat-box.error` - Error styling (red)
  - `.stat-box.warning` - Warning styling (yellow)
  - `.stat-box.info` - Info styling (blue)
  - `.distribution-bar` - Chart bar
  - `.metadata` - Timestamp section
  - `.refresh-btn` - Refresh button

#### LocalInspection Page Styling
- **File:** `frontend/src/pages/LocalInspection.css`
- **Lines:** 90+
- **Status:** ✅ NEW
- **Components:**
  - `.local-inspection-page` - Main container
  - `.inspection-panel` - Left/right panels
  - `.left-panel` - File tree panel
  - `.right-panel` - Validation panel
  - `.panel-splitter` - Divider
  - `.panel-header` - Section headers
  - `.validation-container` - Validation area
  - Responsive breakpoints

## Data Structures

### FileTreeNode
```typescript
interface FileTreeNode {
  id: string;                    // Unique identifier
  name: string;                  // File or folder name
  type: 'file' | 'folder';      // Type of node
  children?: FileTreeNode[];    // Child nodes (for folders)
  icon?: React.ReactNode;       // Icon component
  onClick?: (id: string) => void; // Click handler
}
```

### ValidationResult
```typescript
interface ValidationResult {
  file: string;                                    // File path
  line: number;                                    // Line number (1-indexed)
  column: number;                                  // Column number (1-indexed)
  severity: 'error' | 'warning' | 'info';        // Issue severity
  message: string;                                // Issue description
  rule?: string;                                  // Rule ID (e.g., "E305", "F821")
}
```

### Validator
```typescript
interface Validator {
  id: string;              // Validator ID (e.g., "flake8")
  name: string;            // Display name
  description: string;     // Description
  language: string;        // Language it supports
}
```

### ValidationFormProps
```typescript
interface ValidationFormProps {
  selectedPath?: string;
  selectedPathType?: 'file' | 'folder';
  validators: Validator[];
  languages: string[];
  onValidate: (language: string, validator: string, path: string) => Promise<ValidationResult[]>;
  loading?: boolean;
  results?: ValidationResult[];
}
```

## Navigation Flow

```
App.tsx
├── ProjectProvider
└── AppLayout
    ├── Navigation (tabs)
    │   ├── Config
    │   ├── Inspection ← LocalInspection page
    │   ├── Tests
    │   └── CI
    └── Page Content
        └── LocalInspection (when on "Inspection" tab)
            ├── useProjects() hook
            ├── State management (8 states)
            ├── API integration (4 endpoints)
            └── Render
                ├── Left Panel
                │   ├── Header "📁 Files"
                │   └── FileTree component
                ├── Splitter
                └── Right Panel
                    ├── Header "🔍 Validation"
                    ├── ValidationForm component
                    └── StatsCard component
```

## API Endpoint Mapping

| Component | Action | Endpoint | Method | Payload |
|-----------|--------|----------|--------|---------|
| LocalInspection | Mount | `/api/inspection/files` | GET | `?path={projectPath}` |
| LocalInspection | Mount | `/api/inspection/languages` | GET | None |
| LocalInspection | Mount | `/api/inspection/validators` | GET | None |
| ValidationForm | Submit | `/api/inspection/validate` | POST | `{path, language, validator, target}` |

## Styling Breakpoints

| Device | Width | Columns | Layout |
|--------|-------|---------|--------|
| Desktop | 1024px+ | 2 | 35% / 65% |
| Tablet | 768-1023px | 2 | 40% / 60% |
| Mobile | 480-767px | 1 | Stacked 35% / 65% |
| Small | <480px | 1 | Stacked responsive |

## Color Scheme

| Severity | Color | RGB | Usage |
|----------|-------|-----|-------|
| Error | Red | #ef5350 | Errors, critical issues |
| Warning | Yellow | #fbc02d | Warnings, style issues |
| Info | Blue | #29b6f6 | Info, suggestions |
| Default | Gray | #999 | Neutral text |

## Import Paths

### From LocalInspection.tsx
```typescript
import { useProjects } from '../contexts/ProjectContext';
import { FileTree, FileTreeNode } from '../components/FileTree';
import { ValidationForm, ValidationResult, Validator } from '../components/ValidationForm';
import { StatsCard } from '../components/StatsCard';
import './LocalInspection.css';
```

### From Other Components
```typescript
// ValidationForm imports
import React, { useState, useEffect } from 'react';
import './ValidationForm.css';

// StatsCard imports
import React from 'react';
import './StatsCard.css';

// FileTree imports
import { ChevronDown, ChevronRight, Folder, File } from 'lucide-react';
import { useState } from 'react';
import './FileTree.css';
```

## Project Structure

```
lens/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── FileTree.tsx         ✅ PHASE 3
│   │   │   ├── FileTree.css         ✅ PHASE 3 (new)
│   │   │   ├── ValidationForm.tsx   ✅ PHASE 3 (new)
│   │   │   ├── ValidationForm.css   ✅ PHASE 3 (new)
│   │   │   ├── StatsCard.tsx        ✅ PHASE 3 (new)
│   │   │   ├── StatsCard.css        ✅ PHASE 3 (new)
│   │   │   ├── Navigation.tsx       ✅ PHASE 2
│   │   │   └── ... (other components)
│   │   ├── contexts/
│   │   │   └── ProjectContext.tsx   ✅ PHASE 2
│   │   ├── layouts/
│   │   │   └── AppLayout.tsx        ✅ PHASE 2
│   │   └── pages/
│   │       ├── LocalInspection.tsx  ✅ PHASE 3 (new)
│   │       ├── LocalInspection.css  ✅ PHASE 3 (new)
│   │       ├── ConfigPage.tsx       ✅ PHASE 2
│   │       └── ... (other pages)
│   └── vite.config.js
│
├── backend/
│   ├── services/
│   │   ├── anvil_service.py        ⏳ PHASE 3 TASK 5
│   │   └── ... (other services)
│   ├── routes/
│   │   ├── inspection.py            ⏳ PHASE 3 TASK 6
│   │   ├── projects.py              ✅ PHASE 1
│   │   └── ... (other routes)
│   ├── server.py                    ✅ PHASE 1
│   └── tests/
│       ├── test_inspection_routes.py ⏳ PHASE 3 TASK 7
│       └── ... (other tests)
│
└── docs/
    ├── PHASE_3_PROGRESS.md          ✅ NEW
    └── PHASE_3_FRONTEND_COMPLETE.md ✅ NEW
```

## Files to Create Next (Phase 3 Tasks 5-7)

### Backend Services
- [ ] `lens/backend/services/anvil_service.py` - Wraps Anvil validation

### Backend Routes
- [ ] `lens/backend/routes/inspection.py` - Inspection API endpoints

### Backend Tests
- [ ] `lens/backend/tests/test_anvil_service.py` - AnvilService tests
- [ ] `lens/backend/tests/test_inspection_routes.py` - Route tests

### Frontend Tests
- [ ] `lens/frontend/src/pages/LocalInspection.test.tsx` - Page tests
- [ ] `lens/frontend/src/components/ValidationForm.test.tsx` - Form tests
- [ ] `lens/frontend/src/components/StatsCard.test.tsx` - Stats tests

## Deployment Checklist

### Frontend (✅ Complete)
- [x] Components created
- [x] CSS styling complete
- [x] TypeScript compilation (0 errors)
- [x] Responsive design verified
- [x] Navigation integration
- [x] State management
- [x] API hooks ready

### Backend (⏳ Pending)
- [ ] AnvilService implemented
- [ ] Inspection routes created
- [ ] Routes registered in server.py
- [ ] CORS headers configured
- [ ] Error handling added
- [ ] Logging implemented
- [ ] Tests written

### Testing (⏳ Pending)
- [ ] Unit tests written
- [ ] Integration tests written
- [ ] Coverage 90%+
- [ ] All tests passing
- [ ] Manual testing completed

---

**Phase 3 Frontend: 100% COMPLETE ✅**
**Phase 3 Backend & Testing: 0% COMPLETE ⏳**

Next: Start Phase 3 Task 5 - AnvilService Backend Integration

