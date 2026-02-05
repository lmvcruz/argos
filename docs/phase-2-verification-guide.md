# Phase 2 Implementation - Verification Guide

## Quick Verification Checklist

This guide helps verify that Phase 2 implementation is complete and correct.

---

## 1. File Structure Verification

### Expected Directories
```
src/
├── api/
│   ├── types.ts ✓
│   └── tools/
│       ├── anvilClient.ts ✓
│       ├── verdictClient.ts ✓
│       ├── scoutClient.ts ✓
│       └── index.ts ✓
├── hooks/
│   ├── useAnvilAnalysis.ts ✓
│   ├── useTestExecution.ts ✓
│   ├── useWorkflowHistory.ts ✓
│   └── index.ts ✓
└── pages/
    ├── LocalInspection.tsx ✓
    ├── LocalTests.tsx ✓
    └── CIInspection.tsx ✓
```

**Verify with:**
```bash
# From frontend directory
ls -la src/api/tools/
ls -la src/hooks/
```

---

## 2. TypeScript Compilation Check

### Verify no TypeScript errors
```bash
cd lens/frontend
npm run type-check
```

**Expected output**: No errors

### Verify imports are correct
```bash
# Check that all imports resolve
grep -r "import.*from.*api/tools" src/
grep -r "import.*from.*hooks" src/
```

**Expected**:
- Pages should import from hooks
- Hooks should import from api/tools
- No circular dependencies

---

## 3. Build Verification

### Run Vite dev server
```bash
cd lens/frontend
npm run dev
```

**Expected output**:
```
  VITE v5.4.21  ready in XXX ms

  ➜  Local:   http://localhost:3000/
  ➜  press h + enter to show help
```

**Check browser console** (F12):
- No red errors
- No import errors
- No TypeScript compilation errors

---

## 4. Runtime Verification

### Verify pages load without errors

1. **LocalInspection**
   - Navigate to http://localhost:3000/
   - Should show code analysis interface
   - "Run Analysis" button should be clickable
   - No console errors
   - Project path input should be visible

2. **LocalTests**
   - Navigate to http://localhost:3000/tests
   - Should show test results interface
   - "Run Tests" button should be clickable
   - No console errors
   - Summary stats should show 0/0/0 initially

3. **CIInspection**
   - Navigate to http://localhost:3000/ci
   - Should show workflow history interface
   - Should auto-load workflows on mount (even if backend not ready)
   - "Refresh" button should be visible
   - No console errors

---

## 5. API Client Verification

### Test Anvil client initialization
```bash
# Open browser console and run:
```
```typescript
import { anvilClient } from './api/tools'
console.log(anvilClient) // Should show AnvilClient instance
```

### Test Verdict client initialization
```typescript
import { verdictClient } from './api/tools'
console.log(verdictClient) // Should show VerdictClient instance
```

### Test Scout client initialization
```typescript
import { scoutClient } from './api/tools'
console.log(scoutClient) // Should show ScoutClient instance
```

---

## 6. Hook Verification

### Test useAnvilAnalysis hook
```typescript
import { useAnvilAnalysis } from './hooks'

// Should be callable in a component
const { data, loading, error, analyze } = useAnvilAnalysis()
// Should return proper types
```

### Test useTestExecution hook
```typescript
import { useTestExecution } from './hooks'

// Should be callable in a component
const { data, loading, error, execute } = useTestExecution()
// Should return proper types
```

### Test useWorkflowHistory hook
```typescript
import { useWorkflowHistory } from './hooks'

// Should be callable in a component
const { data, loading, error, fetch } = useWorkflowHistory()
// Should return proper types
```

---

## 7. Component Integration Verification

### LocalInspection
Check that component:
- [ ] Imports `useAnvilAnalysis` hook
- [ ] Calls hook in component body
- [ ] Passes loading state to button
- [ ] Shows error message when error exists
- [ ] Converts API response to table rows
- [ ] Displays dynamic statistics
- [ ] Has project path input field

**Code locations:**
- Lines 1-20: Imports
- Lines 25-30: Hook initialization
- Lines 35-60: Conversion logic
- Lines 80-100: Button with loading state
- Lines 130-160: Error display

### LocalTests
Check that component:
- [ ] Imports `useTestExecution` hook
- [ ] Calls hook in component body
- [ ] Passes loading state to button
- [ ] Shows error message when error exists
- [ ] Converts API response to table rows
- [ ] Displays dynamic statistics
- [ ] Has project path input field

### CIInspection
Check that component:
- [ ] Imports `useWorkflowHistory` hook
- [ ] Uses useEffect to auto-load on mount
- [ ] Calls hook in component body
- [ ] Passes loading state to button
- [ ] Shows error message when error exists
- [ ] Converts API response to table rows
- [ ] Displays dynamic statistics
- [ ] Shows sync status

---

## 8. Backend Connectivity Test (Optional)

### Create mock backend responses

Create `test-backend.js` in lens/backend:
```javascript
const http = require('http');

const server = http.createServer((req, res) => {
  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');

  if (req.url === '/api/anvil/analyze' && req.method === 'POST') {
    res.writeHead(200);
    res.end(JSON.stringify({
      issues: [
        {
          id: '1',
          file: 'src/main.ts',
          line: 42,
          column: 5,
          severity: 'error',
          rule: 'no-unused-variable',
          message: 'Variable "x" is defined but never used'
        }
      ],
      summary: { total: 1, errors: 1, warnings: 0, info: 0 },
      duration: 1000,
      timestamp: new Date().toISOString()
    }));
  }

  if (req.url === '/api/verdict/execute' && req.method === 'POST') {
    res.writeHead(200);
    res.end(JSON.stringify({
      tests: [
        {
          id: '1',
          name: 'test should pass',
          status: 'passed',
          file: 'tests/main.test.ts',
          duration: 100
        }
      ],
      summary: { total: 1, passed: 1, failed: 0, flaky: 0, skipped: 0, duration: 100 },
      timestamp: new Date().toISOString()
    }));
  }

  if (req.url === '/api/scout/workflows') {
    res.writeHead(200);
    res.end(JSON.stringify({
      workflows: [
        {
          id: '1',
          name: 'Test Suite',
          run_number: 100,
          branch: 'main',
          status: 'completed',
          result: 'passed',
          duration: 60000,
          started_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
          url: 'https://github.com/owner/repo/actions/runs/1',
          jobs: []
        }
      ],
      sync_status: {
        last_sync: new Date().toISOString(),
        is_syncing: false,
        next_sync: new Date(Date.now() + 300000).toISOString()
      },
      total: 1,
      timestamp: new Date().toISOString()
    }));
  }
});

server.listen(8000, () => {
  console.log('Mock backend running on http://localhost:8000');
});
```

Run with: `node test-backend.js`

Then test in browser console:
```bash
# LocalInspection
curl -X POST http://localhost:8000/api/anvil/analyze -H "Content-Type: application/json" -d '{"projectPath":"."}'

# LocalTests
curl -X POST http://localhost:8000/api/verdict/execute -H "Content-Type: application/json" -d '{"projectPath":"."}'

# CIInspection
curl http://localhost:8000/api/scout/workflows
```

---

## 9. Error State Testing

### Test error handling

In LocalInspection:
1. Make sure backend is NOT running
2. Click "Run Analysis"
3. Should see error message: "Failed to fetch... backend unavailable"
4. Button should return to clickable state

In LocalTests:
1. Same as above for tests
2. Should see error message

In CIInspection:
1. Same as above for workflows
2. Should see error message instead of results

---

## 10. Loading State Testing

### Test loading animations

In LocalInspection:
1. Slow down network (DevTools → Network → Fast 3G)
2. Click "Run Analysis"
3. Should see spinner on button
4. Button should be disabled
5. Should not be able to click again while loading

In LocalTests:
1. Same process
2. Verify spinner animates

In CIInspection:
1. Click "Refresh"
2. Should see spinner on refresh icon
3. Should rotate while loading

---

## Troubleshooting

### TypeScript Errors
```bash
# If you see TypeScript errors:
npm run type-check  # Show all errors
npm install        # Ensure packages installed
```

### Import Errors
```
Cannot find module '@hooks' or similar
→ Check that barrel exports (index.ts) exist and are correct
```

### Network Errors
```
Failed to fetch http://localhost:8000
→ Check backend is running on correct port
→ Check CORS is enabled if needed
```

### State Not Updating
```
Data doesn't show after API call
→ Check hook is called in component
→ Check API response matches interface
→ Check console for errors
```

---

## Success Criteria

- ✅ All files created in correct locations
- ✅ Frontend builds without TypeScript errors
- ✅ All three pages load in browser
- ✅ No console errors in browser
- ✅ Buttons show loading/disabled states
- ✅ Error messages display properly
- ✅ Hook state is properly typed
- ✅ API clients are instantiated correctly

**If all checks pass**: Phase 2 implementation is complete and ready for testing!
