# Phase 1: Quick Start Guide

## What's New in Phase 1

Three new scenario pages have been added to Lens with a complete foundation for expansion:

1. **Local Inspection** (`/local-inspection`) - Code quality analysis
2. **Local Tests** (`/local-tests`) - Test execution results
3. **CI Inspection** (`/ci-inspection`) - CI workflow monitoring

All backed by a new configuration system and 6 reusable components.

## Quick Start

### 1. Start the backend
```bash
cd lens
python -m lens.backend.server
```

### 2. Start the frontend
```bash
cd lens/frontend
npm install  # if not done already
npm run dev
```

### 3. Navigate to scenarios
- Local Inspection: http://localhost:3000/local-inspection
- Local Tests: http://localhost:3000/local-tests
- CI Inspection: http://localhost:3000/ci-inspection

## Configuration

Modify `lens/frontend/public/config/settings.json` to toggle features:

```json
{
  "features": {
    "localInspection": { "enabled": true },
    "localTests": { "enabled": true },
    "ciInspection": { "enabled": true },
    "localBuild": { "enabled": false },
    "localExecution": { "enabled": false }
  }
}
```

Or use environment variables:
```bash
VITE_LENS_FEATURE_LOCALBUILD=true npm run dev
```

## Component Usage Examples

### FileTree - Hierarchical File Browser
```tsx
import { FileTree, type FileTreeNode } from '../components';

const files: FileTreeNode[] = [
  {
    id: 'root',
    name: 'project',
    type: 'folder',
    children: [
      { id: 'file1', name: 'main.ts', type: 'file' },
    ],
  },
];

<FileTree nodes={files} onSelectNode={(id) => {...}} />
```

### ResultsTable - Sortable Results Table
```tsx
import { ResultsTable, type TableColumn, type TableRow } from '../components';

const columns: TableColumn[] = [
  { key: 'name', label: 'Name', sortable: true },
  {
    key: 'severity',
    label: 'Severity',
    render: (value) => <SeverityBadge severity={value} />
  },
];

const rows: TableRow[] = [
  { id: '1', name: 'Issue 1', severity: 'error' },
];

<ResultsTable columns={columns} rows={rows} pageSize={20} />
```

### OutputPanel - Real-time Logs
```tsx
import { OutputPanel, type LogEntry } from '../components';

const logs: LogEntry[] = [
  { timestamp: '14:23:45', level: 'info', message: 'Starting analysis...' },
  { timestamp: '14:23:46', level: 'error', message: 'Failed to parse file' },
];

<OutputPanel logs={logs} isLive={true} filterLevel="all" />
```

### SeverityBadge - Color-coded Badges
```tsx
import { SeverityBadge } from '../components';

<SeverityBadge severity="error" label="Critical" count={3} size="md" />
<SeverityBadge severity="warning" count={5} />
<SeverityBadge severity="info" label="Information" />
<SeverityBadge severity="success" label="All Tests Pass" />
```

### CodeSnippet - Syntax Highlighting
```tsx
import { CodeSnippet } from '../components';

<CodeSnippet
  code={`function test() { return 42; }`}
  language="typescript"
  lineNumbers
  maxHeight="400px"
/>
```

### CollapsibleSection - Expandable Details
```tsx
import { CollapsibleSection } from '../components';
import { Settings } from 'lucide-react';

<CollapsibleSection
  title="Advanced Options"
  icon={<Settings />}
  defaultExpanded={false}
>
  {/* detailed content here */}
</CollapsibleSection>
```

## Using Configuration Context

```tsx
import { useConfig } from '../config/ConfigContext';

export function MyComponent() {
  const { config, isFeatureEnabled, isToolEnabled, isLoading, error } = useConfig();

  if (isLoading) return <div>Loading configuration...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      {isFeatureEnabled('localInspection') && (
        <LocalInspectionSection />
      )}

      {isToolEnabled('anvil') && (
        <AnvilToolSection path={config.tools.anvil.path} />
      )}
    </div>
  );
}
```

## File Structure for Phase 2

When implementing Phase 2 features, follow this structure:

```
lens/
├── frontend/
│   └── src/
│       ├── components/       # Reusable UI components
│       ├── config/          # Configuration & context
│       ├── pages/           # Scenario pages
│       ├── api/             # API client & hooks
│       ├── types/           # Shared TypeScript types
│       └── services/        # Business logic services
├── backend/                 # Python FastAPI server
└── tools/                   # Tool integrations
    ├── anvil/              # Code analysis
    ├── forge/              # Build management
    ├── scout/              # CI data sync
    ├── verdict/            # Test analysis
    └── gaze/               # Performance monitoring
```

## Common Tasks

### Add a new scenario page

1. Create `lens/frontend/src/pages/MyScenario.tsx`
2. Import base components you need
3. Use `useConfig()` to check if feature is enabled
4. Export as default
5. Add route in `App.tsx`
6. Add navigation link in sidebar

### Add a feature toggle

1. Add feature to `settings.json` in `features` object
2. Set `"enabled": true/false`
3. In page, check: `if (!isFeatureEnabled('myFeature')) return <Disabled />`
4. Optionally add environment variable override support

### Use a tool

1. Get config: `const { config } = useConfig()`
2. Check if enabled: `if (isToolEnabled('anvil')) { ... }`
3. Get tool path: `const path = config.tools.anvil.path`
4. Get timeout: `const timeout = config.tools.anvil.timeout`

## Testing Features Locally

### Test Local Inspection
- Click "Local Inspection" in sidebar
- View mock file tree
- View mock analysis results
- Click "Run Analysis" to trigger mock execution
- Watch output panel update with logs

### Test Local Tests
- Click "Local Tests" in sidebar
- View mock test results with pass/fail/flaky status
- Click "Run Tests" to trigger mock execution
- See summary stats update

### Test CI Inspection
- Click "CI Inspection" in sidebar
- View workflow history
- See success rate statistics
- View workflow execution logs

### Disable Features
Edit `public/config/settings.json`:
```json
{
  "features": {
    "localInspection": { "enabled": false },
    "localTests": { "enabled": false },
    "ciInspection": { "enabled": false }
  }
}
```

Reload page - features won't appear in sidebar.

## Troubleshooting

### Components not appearing
- Ensure `ConfigProvider` wraps your app (it's in `App.tsx`)
- Check `settings.json` has `"enabled": true`
- Look at browser console for errors

### Config not loading
- Verify `public/config/settings.json` exists
- Ensure path is `/config/settings.json` (served from public root)
- Check browser Network tab - should see 200 response

### Styling issues
- Confirm Tailwind CSS is configured
- Check class names are valid Tailwind classes
- Rebuild if needed: `npm run dev`

### TypeScript errors
- Ensure all imports are correct
- Check component prop types match usage
- Run `npm run build` to check for build errors

## Next Phase (Phase 2)

Phase 2 will connect these components to actual tool backends:
- Anvil integration for code analysis
- Forge integration for build data
- Scout integration for CI data
- Verdict integration for test results
- Real-time data streaming
- Advanced filtering and search
- Performance optimizations

For now, all data is mocked - ready to be replaced with real backend calls!
