# Phase 2: Integration Roadmap

## Overview

Phase 2 (Weeks 3-4) connects Phase 1 foundation components to actual tool backends and implements core scenario features.

## Phase 2 Goals

1. **Backend Integration**: Connect to Anvil, Forge, Scout, Verdict, Gaze tools
2. **Real Data Flow**: Replace mock data with actual backend responses
3. **Advanced Features**: Filtering, search, export, real-time updates
4. **Error Handling**: Graceful failures and retry logic
5. **Performance**: Optimize for large datasets

## Week 3: Local Inspection & Local Tests

### Week 3 Tasks

#### Task 1: Anvil Integration for Local Inspection
**Goal**: Connect FileTree and ResultsTable to real code analysis

**Files to Create**:
- `lens/frontend/src/api/tools/anvilClient.ts` - Anvil API client
- `lens/frontend/src/hooks/useAnvilAnalysis.ts` - Custom hook for analysis
- Update `lens/frontend/src/pages/LocalInspection.tsx` - Use real data

**Implementation Steps**:
1. Create AnvilClient class to wrap HTTP calls to `/api/anvil/analyze`
2. Implement `useAnvilAnalysis()` hook to manage analysis state
3. Add file selection handler to trigger analysis
4. Replace mock data with real analysis results
5. Add loading spinner during analysis
6. Add error state for failed analyses
7. Add real file tree from analysis results
8. Implement ResultsTable with real issue data

**Expected Backend API** (to be implemented in lens backend):
```
POST /api/anvil/analyze
{
  "projectPath": string,
  "toolOptions": {
    "ignorePatterns": string[],
    "checkTypes": string[]
  }
}

Response:
{
  "issues": [
    {
      "id": string,
      "file": string,
      "line": number,
      "column": number,
      "severity": "error" | "warning" | "info",
      "rule": string,
      "message": string,
      "code": string
    }
  ],
  "summary": {
    "total": number,
    "errors": number,
    "warnings": number,
    "info": number
  },
  "duration": number
}
```

#### Task 2: Verdict Integration for Local Tests
**Goal**: Connect ResultsTable to real test execution results

**Files to Create**:
- `lens/frontend/src/api/tools/verdictClient.ts` - Verdict API client
- `lens/frontend/src/hooks/useTestExecution.ts` - Custom hook for tests
- Update `lens/frontend/src/pages/LocalTests.tsx` - Use real data

**Implementation Steps**:
1. Create VerdictClient to wrap HTTP calls to `/api/verdict/execute`
2. Implement `useTestExecution()` hook for test state management
3. Add test runner selector (jest, pytest, etc.)
4. Replace mock data with real test results
5. Implement test filtering by status (pass, fail, flaky)
6. Add test duration sorting
7. Add test file path navigation
8. Implement test re-run for failed tests
9. Add coverage summary if available

**Expected Backend API**:
```
POST /api/verdict/execute
{
  "projectPath": string,
  "testPattern": string,
  "framework": "jest" | "pytest" | "mocha" | "go test"
}

Response:
{
  "tests": [
    {
      "id": string,
      "name": string,
      "status": "passed" | "failed" | "flaky" | "skipped",
      "file": string,
      "duration": number,
      "error": string,
      "stackTrace": string
    }
  ],
  "summary": {
    "total": number,
    "passed": number,
    "failed": number,
    "flaky": number,
    "skipped": number,
    "duration": number,
    "coverage": number (0-100)
  }
}
```

### Week 3 Deliverables

✅ Anvil integration working with real file analysis
✅ Verdict integration working with real test execution
✅ Local Inspection showing real analysis results
✅ Local Tests showing real test results
✅ Error handling for both integrations
✅ Loading states for all operations
✅ Basic filtering and sorting

## Week 4: CI Integration & Polish

### Week 4 Tasks

#### Task 3: Scout Integration for CI Inspection
**Goal**: Connect workflow history table to real CI data

**Files to Create**:
- `lens/frontend/src/api/tools/scoutClient.ts` - Scout API client
- `lens/frontend/src/hooks/useWorkflowHistory.ts` - Custom hook for CI data
- Update `lens/frontend/src/pages/CIInspection.tsx` - Use real data

**Implementation Steps**:
1. Create ScoutClient to wrap HTTP calls to `/api/scout/workflows`
2. Implement `useWorkflowHistory()` hook for workflow state
3. Add workflow filtering by status and branch
4. Add date range filter for workflow history
5. Replace mock data with real workflow data
6. Implement workflow detail view on row click
7. Add workflow re-trigger functionality
8. Implement GitHub webhook for real-time updates
9. Add workflow duration trends

**Expected Backend API**:
```
GET /api/scout/workflows?limit=50&branch=main&status=all

Response:
{
  "workflows": [
    {
      "id": string,
      "name": string,
      "run_number": number,
      "branch": string,
      "status": "completed" | "in_progress" | "queued",
      "result": "passed" | "failed" | "pending",
      "duration": number,
      "started_at": ISO8601,
      "completed_at": ISO8601,
      "url": string,
      "jobs": [
        {
          "id": string,
          "name": string,
          "status": string,
          "duration": number
        }
      ]
    }
  ],
  "sync_status": {
    "last_sync": ISO8601,
    "is_syncing": boolean,
    "next_sync": ISO8601
  }
}
```

#### Task 4: Advanced Features & Polish
**Goal**: Add enterprise features for all scenarios

**Implementation Steps**:
1. **Export Functionality**:
   - Add export to CSV for all result tables
   - Add export to PDF for reports
   - Add email report functionality

2. **Advanced Filtering**:
   - Add filter builder UI for complex queries
   - Add saved filter presets
   - Add search across all fields

3. **Real-time Updates**:
   - Implement WebSocket connections
   - Add live execution progress
   - Add execution notifications

4. **Performance Optimization**:
   - Implement virtual scrolling for large tables
   - Add result caching
   - Implement pagination optimization

5. **UI Polish**:
   - Add loading skeletons
   - Improve empty states
   - Add success/error toast notifications
   - Enhance keyboard navigation

6. **Mobile Responsiveness**:
   - Test on mobile devices
   - Optimize sidebar for mobile
   - Add touch-friendly interactions

### Week 4 Deliverables

✅ Scout integration with real workflow data
✅ CI Inspection showing real workflow history
✅ Export functionality (CSV, PDF)
✅ Advanced filtering across all scenarios
✅ Real-time updates via WebSocket
✅ Performance optimizations for large datasets
✅ Mobile responsive design
✅ Toast notifications for user feedback

## Phase 2 Architecture

### API Layer Structure
```
lens/frontend/src/api/
├── client.ts              # Base HTTP client
├── tools/
│   ├── anvilClient.ts     # Code analysis
│   ├── verdictClient.ts   # Test execution
│   ├── scoutClient.ts     # CI workflows
│   ├── forgeClient.ts     # Build (Phase 3)
│   └── gazeClient.ts      # Performance (Phase 3)
└── types.ts               # Shared API types
```

### Hook Layer Structure
```
lens/frontend/src/hooks/
├── useAnvilAnalysis.ts    # Code analysis hook
├── useTestExecution.ts    # Test execution hook
├── useWorkflowHistory.ts  # Workflow history hook
├── useProjectPath.ts      # Project path selection
└── useToolConfig.ts       # Tool configuration
```

### Service Layer Structure
```
lens/frontend/src/services/
├── exportService.ts       # CSV/PDF export
├── filterService.ts       # Advanced filtering
├── cacheService.ts        # Result caching
└── notificationService.ts # Toast notifications
```

## Backend Requirements

The Lens Python backend needs to expose these endpoints:

### For Anvil (Code Analysis)
```
POST /api/anvil/analyze
POST /api/anvil/cancel
GET /api/anvil/status
```

### For Verdict (Test Execution)
```
POST /api/verdict/execute
POST /api/verdict/cancel
GET /api/verdict/status
GET /api/verdict/coverage
```

### For Scout (CI Workflows)
```
GET /api/scout/workflows
POST /api/scout/workflows/{id}/trigger
GET /api/scout/workflows/{id}/jobs
GET /api/scout/workflows/{id}/logs
GET /api/scout/sync-status
```

## Rollout Schedule

**Week 3**:
- Mon-Tue: Anvil integration
- Wed-Thu: Verdict integration
- Fri: Testing and bug fixes

**Week 4**:
- Mon-Tue: Scout integration
- Wed: Advanced features (filtering, export)
- Thu: Real-time updates
- Fri: Polish and mobile optimization

## Testing Strategy

### Unit Tests
- Test all new API clients
- Test custom hooks with mocked backend
- Test filter/export logic

### Integration Tests
- Test full flow from UI to backend
- Test error scenarios
- Test concurrent operations

### E2E Tests
- Test complete scenarios end-to-end
- Test on multiple browsers
- Test on mobile devices

## Success Criteria

✅ All 3 scenario pages show real data from backends
✅ Error handling graceful with user feedback
✅ Loading states visible during operations
✅ Export functionality works for all data
✅ Filtering works across all scenarios
✅ Real-time updates show live progress
✅ Mobile responsive on all pages
✅ No TypeScript errors
✅ Performance acceptable for 10k+ results
✅ Full test coverage for API layer

## Phase 3 Preview

**Phase 3 (Weeks 5-6)** will add:
- Local Build scenario with Forge
- Local Execution scenario with Gaze
- Workflow trigger and re-run
- Advanced analytics and dashboards
- Performance profiling
- Dependency analysis

## Next Steps

1. **Immediate**: Backend team implements REST API endpoints above
2. **Week 1**: Frontend team creates API clients and hooks
3. **Week 2**: Connect UI to real data, test integration
4. **Week 3**: Add advanced features and polish
5. **Week 4**: Final testing and documentation

---

**Phase 2 Estimated Effort**: 80 hours (2 engineers × 2 weeks)
**Phase 2 Estimated Completion**: End of Week 4
