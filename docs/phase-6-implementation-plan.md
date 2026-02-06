# Phase 6: CI Inspection Enhancement - Implementation Plan

**Date**: February 5, 2026
**Priority**: High (moved to Phase 1)
**Timeline**: Weeks 1-2

---

## Overview

Phase 6 focuses on enriching the CI Inspection page with advanced workflow analysis capabilities. This includes Scout integration with UI enhancements, workflow comparison, failure analysis, and performance trending.

---

## Tasks & Implementation

### Task 1: Enhance Scout Sync Status UI
**Effort**: 2 days | **Priority**: High

**Current State**:
- ✅ Scout client has `getSyncStatus()` method
- ✅ CIInspection page renders workflow list
- ❌ Sync status UI not implemented
- ❌ Manual sync trigger not available

**Implementation**:
1. Add sync status display in CIInspection header
   - Last sync timestamp
   - Current sync progress
   - Next scheduled sync time
   - Manual sync button
2. Update `useWorkflowHistory` hook to fetch sync status
3. Add loading state during sync
4. Show sync errors/warnings

**UI Components Needed**:
- SyncStatusBar (header with refresh button)
- SyncProgressIndicator (in-progress animation)

**Files to Create/Modify**:
- `lens/frontend/src/components/SyncStatusBar.tsx` (new)
- `lens/frontend/src/pages/CIInspection.tsx` (modify)
- `lens/frontend/src/hooks/useWorkflowHistory.ts` (enhance)

---

### Task 2: Build Workflow History Visualization
**Effort**: 3 days | **Priority**: High

**Current State**:
- ✅ Workflows list displays in table format
- ❌ No timeline/history view
- ❌ No status progression visualization
- ❌ No run trends

**Implementation**:
1. Create timeline view of workflow runs
   - Vertical timeline with workflow runs
   - Color-coded by status (success/failure/pending)
   - Clickable to view details
2. Add run status progression
   - Show job statuses within each run
   - Display job duration
3. Add filter/search by:
   - Branch
   - Status (passed, failed, pending)
   - Date range
   - Workflow name

**UI Components Needed**:
- WorkflowTimeline (main component)
- TimelineEntry (individual run)
- JobStatusBar (jobs within run)

**Files to Create/Modify**:
- `lens/frontend/src/components/WorkflowTimeline.tsx` (new)
- `lens/frontend/src/components/TimelineEntry.tsx` (new)
- `lens/frontend/src/pages/CIInspection.tsx` (modify)

---

### Task 3: Create Run Comparison Views
**Effort**: 3 days | **Priority**: Medium

**Current State**:
- ❌ No comparison capability
- ❌ No side-by-side run view
- ❌ No diff visualization

**Implementation**:
1. Add "Compare Runs" feature
   - Select 2 runs to compare
   - Side-by-side view of:
     - Job results
     - Test results
     - Duration differences
     - Status changes
2. Show differences highlighted
   - Green for improvements
   - Red for regressions
3. Comparison metrics
   - Faster/slower jobs
   - New failures
   - Fixed issues

**UI Components Needed**:
- RunComparison (main view)
- ComparisonSelector (pick 2 runs)
- DiffHighlight (show changes)

**API Endpoints Needed**:
- `GET /api/scout/workflows/{workflowId}/compare/{otherId}`

**Files to Create/Modify**:
- `lens/frontend/src/pages/RunComparison.tsx` (new)
- `lens/frontend/src/components/RunComparison.tsx` (new)
- `lens/frontend/src/api/tools/scoutClient.ts` (enhance)
- Backend: Scout client compare endpoint

---

### Task 4: Implement Failure Pattern Analysis
**Effort**: 4 days | **Priority**: Medium

**Current State**:
- ❌ No failure aggregation
- ❌ No pattern detection
- ❌ No failure grouping

**Implementation**:
1. Failure dashboard showing:
   - Most common failures (aggregated)
   - Failure frequency over time (histogram)
   - Failing jobs (by count)
   - Test failure rates
2. Failure pattern detection
   - Group similar failures
   - Show failure cascade (A fails → B fails)
   - Identify flaky tests
3. Actionable insights
   - "This job fails 80% of the time"
   - "Test X is flaky (passes 50% of runs)"
   - "Failure started after commit XYZ"

**UI Components Needed**:
- FailureAnalysisDashboard
- FailureFrequencyChart
- FailureGrouping
- FlakynessIndicator

**API Endpoints Needed**:
- `GET /api/scout/analytics/failures` - Get failure patterns
- `GET /api/scout/analytics/flaky-tests` - Detect flaky tests

**Files to Create/Modify**:
- `lens/frontend/src/pages/FailureAnalysis.tsx` (new)
- `lens/frontend/src/components/FailureAnalysisDashboard.tsx` (new)
- Backend: Failure analysis endpoints

---

### Task 5: Add Performance Trending
**Effort**: 3 days | **Priority**: Medium

**Current State**:
- ❌ No performance history
- ❌ No trend visualization
- ❌ No regression detection

**Implementation**:
1. Performance metrics dashboard
   - Overall workflow duration trend
   - Individual job duration trends
   - Test execution time trends
2. Visualizations
   - Line chart: Duration over time
   - Bar chart: Duration by job
   - Heatmap: Job duration × run count
3. Performance insights
   - "Workflow 10% slower than 7 days ago"
   - "Job X is getting slower (trend)"
   - "Performance regression detected"
4. Baseline comparison
   - Set baseline (main branch)
   - Compare feature branches to baseline
   - Show performance delta

**UI Components Needed**:
- PerformanceTrendChart
- BaselineComparison
- TrendIndicator (↑↓ with percentage)

**API Endpoints Needed**:
- `GET /api/scout/analytics/performance` - Get performance trends
- `GET /api/scout/analytics/baseline` - Compare to baseline

**Files to Create/Modify**:
- `lens/frontend/src/pages/PerformanceTrending.tsx` (new)
- `lens/frontend/src/components/PerformanceTrendChart.tsx` (new)
- Backend: Performance trending endpoints

---

## Implementation Sequence

### Week 1:
- **Day 1-2**: Task 1 (Sync Status UI)
- **Day 3-4**: Task 2 Part 1 (Workflow Timeline)
- **Day 5**: Integration & testing

### Week 2:
- **Day 6-7**: Task 3 (Run Comparison)
- **Day 8-9**: Task 4 (Failure Analysis)
- **Day 10**: Task 5 (Performance Trending)

---

## Backend Requirements

### New Scout API Endpoints Needed:
```
GET /api/scout/sync-status
  ✅ Already exists (getSyncStatus)

POST /api/scout/sync
  Trigger manual sync

GET /api/scout/workflows
  ✅ Already exists

GET /api/scout/workflows/{id}/jobs
  Get jobs in a workflow

GET /api/scout/workflows/{id}/tests
  Get test results

GET /api/scout/workflows/{id1}/compare/{id2}
  Compare two runs

GET /api/scout/analytics/failures
  Failure patterns & aggregation

GET /api/scout/analytics/flaky-tests
  Detect flaky tests

GET /api/scout/analytics/performance
  Performance trends

GET /api/scout/analytics/baseline
  Baseline comparison
```

### Database Queries Needed:
- Failure aggregation & grouping
- Performance metrics calculation
- Flaky test detection (run history analysis)
- Baseline establishment & comparison

---

## UI Layout Structure

```
CIInspection (main page)
├── Header
│   ├── SyncStatusBar (sync status + refresh button)
│   └── Filters (branch, status, date range)
├── Main Content (tab-based)
│   ├── Tab 1: Workflow Timeline
│   │   └── WorkflowTimeline component
│   ├── Tab 2: Failure Analysis
│   │   └── FailureAnalysisDashboard component
│   ├── Tab 3: Performance Trending
│   │   └── PerformanceTrendChart component
│   └── Tab 4: Run Comparison
│       └── RunComparison component
└── Details Panel (collapsible)
    └── Workflow details on click
```

---

## Success Criteria

- ✅ Sync status visible & refreshable
- ✅ Timeline shows run history with status
- ✅ Can compare 2 runs side-by-side
- ✅ Failure patterns identified & displayed
- ✅ Performance trends visible with baseline
- ✅ All components render without errors
- ✅ API calls working correctly
- ✅ Filtering/search functional
- ✅ Responsive design on different screen sizes

---

## Dependencies

### External Libraries (if needed):
- Chart library: `recharts` (already in lens package.json?)
- Timeline: Custom or use `react-timeline`?

### Internal Dependencies:
- ScoutClient API client (already exists)
- Components: ResultsTable, SeverityBadge, CollapsibleSection
- Hooks: useWorkflowHistory (exists, needs enhancement)

---

## Risk Assessment

**Low Risk**:
- Sync status UI (straightforward)
- Workflow timeline (UI only, data exists)

**Medium Risk**:
- Run comparison (new API endpoint needed)
- Failure analysis (requires data aggregation logic)

**Higher Effort**:
- Performance trending (historical data tracking)
- Flaky test detection (requires statistical analysis)

---

## Next Steps

1. ✅ Review this plan
2. Gather Scout API capabilities & data structure
3. Implement Task 1 first (quick win)
4. Build out components incrementally
5. Test with real CI data
6. Polish UI/UX based on feedback
