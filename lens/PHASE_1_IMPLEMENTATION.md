# Phase 1: Foundation - Implementation Complete

## Overview

Phase 1 establishes the foundation for Lens expansion by implementing:
- **Configuration System**: JSON-based settings with environment variable overrides
- **React Context**: App-wide configuration and state management
- **Base Components**: 6 reusable UI components for output visualization
- **Scenario Routes**: Navigation and routing for 3 enabled scenarios
- **Placeholder Pages**: Ready for Phase 2-3 feature implementation

## Architecture

### Directory Structure

```
lens/frontend/src/
├── config/
│   ├── settings.json          # Configuration schema
│   ├── configManager.ts       # Config loading and management
│   └── ConfigContext.tsx      # React Context for config
├── components/
│   ├── FileTree.tsx           # Hierarchical file browser
│   ├── ResultsTable.tsx       # Sortable, paginated results table
│   ├── CodeSnippet.tsx        # Syntax-highlighted code display
│   ├── CollapsibleSection.tsx # Expandable detail panels
│   ├── SeverityBadge.tsx      # Color-coded severity indicators
│   ├── OutputPanel.tsx        # Real-time output/log display
│   └── index.ts               # Component exports
├── pages/
│   ├── LocalInspection.tsx    # Local code analysis scenario
│   ├── LocalTests.tsx         # Local test execution scenario
│   ├── CIInspection.tsx       # CI workflow monitoring scenario
│   └── [existing pages]       # Analytics dashboard pages
├── App.tsx                    # Updated with new routes & config
└── [existing structure]
```

### Configuration System

**File**: `lens/frontend/src/config/settings.json`

Features configurable through JSON:
- Feature toggles (localInspection, localTests, localBuild, localExecution, ciInspection)
- Tool enablement (anvil, forge, scout, verdict, gaze)
- UI preferences (theme, sidebar state, results per page)
- Output settings (color support, verbosity level)

**Environment Variable Overrides**:
```bash
# Override feature toggles
VITE_LENS_FEATURE_LOCALINSPECTION=true

# Override tool settings
VITE_LENS_TOOL_ANVIL_ENABLED=false
VITE_LENS_TOOL_ANVIL_PATH=/custom/path/to/anvil
```

### React Components

#### 1. **FileTree**
- Hierarchical folder/file browser
- Collapsible folders
- Click selection
- Custom icons support

**Usage**:
```tsx
<FileTree
  nodes={fileStructure}
  onSelectNode={(id) => {...}}
  selectedNodeId={selectedId}
/>
```

#### 2. **ResultsTable**
- Sortable columns
- Pagination
- Row selection
- Custom cell rendering
- Responsive design

**Usage**:
```tsx
<ResultsTable
  columns={columns}
  rows={data}
  pageSize={20}
  onRowClick={(id) => {...}}
  selectedRowId={selectedId}
/>
```

#### 3. **CodeSnippet**
- Syntax-highlighted code blocks (dark theme)
- Line numbers option
- Copy-to-clipboard button
- Scrollable with max-height

**Usage**:
```tsx
<CodeSnippet
  code={sourceCode}
  language="typescript"
  lineNumbers
  maxHeight="500px"
/>
```

#### 4. **CollapsibleSection**
- Expandable/collapsible container
- Custom title and icon
- Default expanded state option

**Usage**:
```tsx
<CollapsibleSection
  title="Configuration"
  icon={<Settings />}
  defaultExpanded={false}
>
  {/* content */}
</CollapsibleSection>
```

#### 5. **SeverityBadge**
- Color-coded severity levels (error, warning, info, success)
- Multiple sizes (sm, md, lg)
- Optional count display
- Icons and labels

**Usage**:
```tsx
<SeverityBadge
  severity="error"
  label="Critical Issue"
  count={5}
  size="md"
/>
```

#### 6. **OutputPanel**
- Real-time log/output display
- Log level filtering (debug, info, warn, error)
- Auto-scroll in live mode
- Copy and download functionality
- Timestamp display

**Usage**:
```tsx
<OutputPanel
  logs={logEntries}
  isLive={true}
  filterLevel="all"
  showTimestamp
  onClear={() => {...}}
/>
```

### Configuration Context

**File**: `lens/frontend/src/config/ConfigContext.tsx`

Provides:
- Configuration loading on app startup
- Feature toggle queries
- Tool enablement queries
- Configuration refresh capability

**Hook Usage**:
```tsx
const {
  config,
  isLoading,
  error,
  isFeatureEnabled,
  isToolEnabled,
  refreshConfig
} = useConfig();

// Check if feature is enabled
if (isFeatureEnabled('localInspection')) {
  // Show feature
}
```

## Scenario Pages

### 1. Local Inspection (`/local-inspection`)
**Purpose**: Analyze code quality, style, and coverage issues

**Components**:
- File tree explorer on left
- Analysis results table
- Severity summary statistics
- Execution output panel
- Configuration details

**State**:
- Selected file tracking
- Live output logs
- Running state

### 2. Local Tests (`/local-tests`)
**Purpose**: Execute and analyze test execution

**Components**:
- Test results table with pass/fail/flaky status
- Execution summary (passed, failed, flaky, total time)
- Execution output panel
- Test file navigator

**State**:
- Test execution logs
- Running state
- Results filtering

### 3. CI Inspection (`/ci-inspection`)
**Purpose**: Monitor CI/CD workflow execution

**Components**:
- Workflow status overview (passed, failed, running)
- Workflow history table
- Workflow details panel
- Last sync information

**State**:
- Workflow history
- Filter and sort state

## Navigation

Updated sidebar now shows:

**Analytics Section**:
- CI Health
- Local vs CI
- Flaky Tests
- Failure Patterns
- GitHub Sync

**Scenarios Section** (conditionally rendered based on config):
- Local Inspection (if enabled)
- Local Tests (if enabled)
- CI Inspection (if enabled)

Active route highlighted in blue.

## Configuration File

**Location**: `lens/frontend/public/config/settings.json`

Must be accessible at `/config/settings.json` via HTTP.

**Structure**:
```json
{
  "version": "1.0",
  "features": {
    "featureName": {
      "enabled": boolean,
      "name": string,
      "description": string,
      "icon": string
    }
  },
  "tools": {
    "toolName": {
      "enabled": boolean,
      "path": string,
      "timeout": number
    }
  },
  "ui": {
    "theme": "light|dark",
    "sidebarCollapsed": boolean,
    "defaultResultsPerPage": number
  },
  "output": {
    "colorEnabled": boolean,
    "verbosity": "debug|info|warn|error"
  }
}
```

## Running Phase 1

### Prerequisites
```bash
cd lens/frontend
npm install
```

### Start Frontend
```bash
npm run dev
# Opens http://localhost:3000
```

### Start Backend
In another terminal:
```bash
cd lens
python -m lens.backend.server
# Runs on http://localhost:8000
```

### Access Scenarios
- **Local Inspection**: http://localhost:3000/local-inspection
- **Local Tests**: http://localhost:3000/local-tests
- **CI Inspection**: http://localhost:3000/ci-inspection

## Feature Toggles

### Enabling/Disabling Features

**Via JSON** (`public/config/settings.json`):
```json
{
  "features": {
    "localInspection": { "enabled": true },
    "localBuild": { "enabled": false }
  }
}
```

**Via Environment Variables**:
```bash
VITE_LENS_FEATURE_LOCALBUILD=true npm run dev
```

## Type Definitions

All components are fully typed with TypeScript:

```typescript
interface FileTreeNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  children?: FileTreeNode[];
  icon?: React.ReactNode;
  onClick?: (id: string) => void;
}

interface TableColumn {
  key: string;
  label: string;
  width?: string;
  sortable?: boolean;
  render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode;
}

interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
}
```

## Next Steps: Phase 2

Phase 2 (Weeks 3-4) will implement:
- **Local Inspection**: Connect to Anvil and Forge tools
- **Local Tests**: Integrate with test runners and Verdict
- **Output Integration**: Real backend data in components
- **Advanced Filtering**: Complex result filtering and search
- **Progress Indicators**: Show execution progress
- **Error Handling**: Graceful error states

## Phase 1 Checklist

✅ Configuration system with JSON schema
✅ ConfigContext for app-wide state
✅ 6 base visualization components
✅ 3 scenario pages with mock data
✅ Navigation sidebar with feature toggles
✅ Environment variable override support
✅ Type-safe TypeScript implementation
✅ Dark/light theme support
✅ Responsive design
✅ Copy/download functionality in OutputPanel
✅ Pagination and sorting in ResultsTable
✅ Collapsible sections for details
✅ Severity color coding

## Build & Deploy

### Development Build
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run preview  # Test production build locally
```

### Docker (Future)
Phase 2 will add Docker support for containerized deployment.

## Troubleshooting

### Config file not loading
- Ensure `public/config/settings.json` exists
- Check browser console for CORS issues
- Verify file syntax with JSON validator

### Features not appearing
- Check `settings.json` for `"enabled": true`
- Verify environment variable override if using
- Check ConfigContext is properly wrapping app

### Components not styled
- Ensure Tailwind CSS is installed (`npm install -D tailwindcss`)
- Check `tailwind.config.js` includes `src/**/*.{js,jsx,ts,tsx}`
- Restart dev server after CSS changes

## Summary

Phase 1 provides a complete foundation for Lens expansion:
- ✅ Configuration infrastructure ready
- ✅ Reusable components for all scenarios
- ✅ Flexible routing system
- ✅ Type-safe implementation
- ✅ Ready for Phase 2 integration

The framework is extensible and ready for connecting actual tool backends in Phase 2.
