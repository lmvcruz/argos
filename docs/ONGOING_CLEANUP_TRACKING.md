# Ongoing Cleanup Tracking

**Last Updated:** Phase 4 In Progress
**Status:** 50 files cleaned (28 Phase 3 + 22 Phase 4), tracking remaining candidates for future removal

---

## Overview

This document tracks low-value documentation, demo scripts, and utilities identified for future removal. These files are NOT deleted immediately but documented here for systematic cleanup decisions in future phases.

### Why Track Rather Than Delete?

1. **Safety**: Some items may be referenced in workflows or CI
2. **Awareness**: Team should understand what's low-value
3. **Timing**: Better to remove after features are fully stable
4. **Batching**: More efficient to delete in scheduled cleanup phases

---

## Category 1: Demo & POC Scripts

**Priority:** Low | **Estimated Value:** Minimal | **Action Timing:** After all POCs validated

### Scout Demo Scripts

| File | Purpose | Status | Risk | Notes |
|------|---------|--------|------|-------|
| `scout/workflow_demo.py` | Demonstrates Scout fetch→parse→show workflow | **Demo** | Low | Example/tutorial script; could be moved to docs/ |
| `scout/demo_simplified_workflow.py` | Shows simplified 3-step workflow | **Demo** | Low | Duplicate concept with workflow_demo.py |
| `scout/show_last_runs.py` | Display last 5 workflow runs | **Demo** | Low | Utility; useful for manual inspection but can use CLI |
| `scout/show_run_details.py` | Display detailed run information | **Demo** | Low | Similar to show_last_runs.py |
| `scout/show_test_results.py` | Display test results from database | **Demo** | Low | Overlaps with CLI reporting features |
| `scout/summary.py` | Create summary of runs | **Demo** | Low | Could be replaced by CLI summary command |

**Recommendation:** Move all `show_*` and `*_demo.py` scripts to a `docs/examples/` directory or delete after CLI commands fully replace them.

---

## Category 2: Old Implementation Plans & Iterations

**Priority:** Medium | **Estimated Value:** Historical reference only | **Action Timing:** Keep through stable v1.0

### Implementation Plans

| File | Current Status | Replaced By | Keep Until |
|------|---|---|---|
| `docs/forge-implementation-plan.md` | **ITER 1** (outdated) | `forge-implementation-plan-iter2.md` | v1.0 stable |
| `docs/scout-implementation-plan-iter1.md` | **ITER 1** (superseded) | Not directly replaced; see scout/scout/cli/ | v1.0 stable |
| `docs/anvil-implementation-plan.md` | **ITER 1** (outdated) | anvil-specification.md | v1.0 stable |
| `docs/anvil-project-integration-plan.md` | **ITER 1** (outdated) | anvil-lens-integration-demo.md | v1.0 stable |

**Recommendation:** Archive to `docs/archive/` directory for historical reference, or keep until v1.0 release is stable. These document the design decisions from earlier phases.

---

## Category 3: POC & Demo Documentation

**Priority:** Low | **Estimated Value:** Historical | **Action Timing:** Delete after project launch

### POC Documentation

| File | Purpose | Status | Notes |
|------|---------|--------|-------|
| `docs/anvil-lens-integration-demo.md` | Demo of Anvil-Lens integration | **POC Doc** | Good for onboarding; archive after project stable |
| `docs/scout-anvil-lens-poc.md` | POC document for Scout-Anvil-Lens integration | **POC Doc** | Already implemented in production code |
| `docs/anvil-lens-integration-plan.md` | Integration plan (experimental) | **Planning** | Superseded by implementation; archive after v1.0 |
| `docs/anvil-project-integration-plan.md` | Project integration planning | **Planning** | Historical; archive after v1.0 |

**Recommendation:** Archive to `docs/archive/` as they document early design exploration. Keep until project reaches v1.0 stability.

---

## Category 4: Specification Variants & Deprecated

**Priority:** Medium | **Estimated Value:** Low | **Action Timing:** Consolidate before v1.0

### Overlapping Specifications

| File | Issue | Recommendation |
|------|-------|---|
| `docs/gaze-specification.md` | Unimplemented feature spec | Archive to `docs/archive/` - feature not in scope |
| `docs/Argus-Project-Description.md` | Project was renamed to Argos | Delete - outdated project name |

**Recommendation:**
- Delete `Argus-Project-Description.md` (project renamed, no longer relevant)
- Archive `gaze-specification.md` (feature out of scope; can be referenced if feature returns)

---

## Category 5: Root-Level & Scripts Folder Items

**Priority:** Medium | **Estimated Value:** Utility/Debug | **Action Timing:** Consolidate before v1.0

### Root-Level Utility Scripts (in `scripts/`)

| File | Purpose | Usage | Keep Until |
|------|---------|-------|---|
| `scripts/analyze_db.py` | Debug script to inspect database schema | **Internal tool** | Development only |
| `scripts/check_db.py` | Quick database check | **Debug tool** | Development only |
| `scripts/check_ci_stats.py` | CI statistics checking | **Debug tool** | Development only |
| `scripts/check_lint_db.py` | Lint database inspection | **Debug tool** | Development only |
| `scripts/quick_db_check.py` | Quick database status | **Debug tool** | Development only |

**Recommendation:** Keep in development, but move to `scripts/debug/` subdirectory to organize them separately from essential scripts.

### Scripts for Removed Features (in `scripts/`)

| File | Purpose | Status | Action |
|------|---------|--------|--------|
| `scripts/download_ci_lint.py` | Download CI lint data | **Deprecated** | Delete |
| `scripts/fetch-job-logs.py` | Fetch GitHub Actions logs | **Replaced** | Delete; use Scout CLI instead |
| `scripts/get-gh-action-logs.py` | Get GH Actions logs | **Replaced** | Delete; use Scout CLI instead |
| `scripts/init_coverage_schema.py` | Initialize coverage schema | **One-time setup** | Delete after initial setup |
| `scripts/populate_demo_data.py` | Populate demo data | **Demo/Testing** | Keep for testing, document as test utility |
| `scripts/run_baseline_execution.py` | Baseline execution | **Completed** | Archive; use for reference only |

### Test/Validation Scripts (in `scripts/`)

| File | Purpose | Status | Keep Until |
|------|---------|--------|---|
| `scripts/test_coverage_parser.py` | Test coverage parser | **Test utility** | Until coverage integration stable |
| `scripts/test_lint_parser.py` | Test lint parser | **Test utility** | Until lint integration stable |
| `scripts/test_lint_schema.py` | Test lint schema | **Test utility** | Until lint integration stable |
| `scripts/test_overlap.py` | Test data overlap | **Test utility** | Until quality integration stable |
| `scripts/test_quality_comparison.py` | Test quality reports | **Test utility** | Until quality reports stable |

**Recommendation:** Reorganize `scripts/` folder structure:
```
scripts/
├── debug/              # Internal debugging utilities
│   ├── analyze_db.py
│   ├── check_db.py
│   ├── check_ci_stats.py
│   └── ...
├── deprecated/         # Remove in next phase
│   ├── download_ci_lint.py
│   ├── fetch-job-logs.py
│   ├── get-gh-action-logs.py
│   └── ...
├── essential/          # Keep - required for CI/CD
│   ├── generate_coverage_report.py
│   ├── generate_quality_report.py
│   ├── sync_ci_to_anvil.py
│   └── ...
└── README.md
```

---

## Category 6: Quick-Reference Documents

**Priority:** Low | **Estimated Value:** Moderate (for active development) | **Action Timing:** Consolidate before v1.0

### Quick-Reference Candidates for Consolidation

| File | Content | Frequency Used | Recommendation |
|------|---------|---|---|
| `docs/ci-sync-quick-reference.md` | CI sync workflow quick guide | Medium | Keep for now; consolidate into unified guide v1.0 |
| `docs/coverage-quick-reference.md` | Coverage reporting quick guide | Low | Consolidate into combined quick-ref v1.0 |
| `docs/quality-quick-reference.md` | Quality checks quick guide | Low | Consolidate into combined quick-ref v1.0 |
| `docs/CI-TROUBLESHOOTING.md` | CI troubleshooting guide | Medium | Keep; merge with ci-sync-quick-reference |
| `docs/ci-quality-integration.md` | Quality integration documentation | Low | Consolidate into architecture docs |

**Recommendation:** Keep all for now as they're useful during active development. Before v1.0 release, consolidate into a single "Quick Start & Troubleshooting" guide covering:
- Setting up CI data sync
- Generating coverage reports
- Running quality checks
- Common troubleshooting

---

## Category 7: Architecture & Data Flow Docs

**Priority:** Medium | **Estimated Value:** High (for maintainability) | **Action Timing:** Review & consolidate

| File | Status | Recommendation |
|------|--------|---|
| `docs/forge-architecture.md` | Current, detailed | Keep as reference |
| `docs/ANVIL_ARCHITECTURE_VISUAL.md` | Current | Keep; good visual reference |
| `docs/ANVIL_DATA_FLOW_GUIDE.md` | Current | Keep; important for understanding data pipeline |

**Recommendation:** Keep all; these are valuable for maintainability and onboarding.

---

## Category 8: Integration & Usage Guides

**Priority:** Medium | **Estimated Value:** High (for onboarding) | **Action Timing:** Review & update before v1.0

| File | Status | Recommendation |
|------|--------|---|
| `docs/scout-anvil-lens-integration-plan.md` | Current, detailed | Keep; important integration documentation |
| `docs/lens-usage-guide.md` | Current | Keep; required for users |
| `docs/lens-implementation-plan.md` | Current | Keep; implementation reference |
| `docs/ANVIL_DOCUMENTATION_INDEX.md` | Current | Keep; navigation aid |

**Recommendation:** Keep all; these are actively used and valuable for project users and developers.

---

## Phase-Based Removal Timeline

### ✅ Phase 3 (COMPLETED)
- 28 files deleted
- All temporary phase documentation removed
- All baseline/coverage reports removed
- Temporary analysis scripts removed

### ✅ Phase 4 (IN PROGRESS - PARTIAL)
**Target:** Before v1.0 Beta release

**Deletions Completed (22 files):**
1. ✅ Scout demo scripts (workflow_demo.py, demo_simplified_workflow.py, summary.py)
2. ✅ Scout show utilities (show_last_runs.py, show_run_details.py, show_test_results.py)
3. ✅ Debug utilities (analyze_db.py, check_db.py, check_ci_stats.py, check_lint_db.py, quick_db_check.py)
4. ✅ Deprecated scripts (download_ci_lint.py, fetch-job-logs.py, get-gh-action-logs.py)
5. ✅ Demo/baseline scripts (populate_demo_data.py, run_baseline_execution.py, init_coverage_schema.py)
6. ✅ Quick-reference docs (ci-sync-quick-reference.md, coverage-quick-reference.md, quality-quick-reference.md)
7. ✅ Troubleshooting & integration docs (CI-TROUBLESHOOTING.md, ci-quality-integration.md)

**Remaining Phase 4 Tasks:**
1. Keep: scripts/test_*.py files (still useful for integration validation)
2. Archive old implementation plans to `docs/archive/`
3. Delete docs/Argus-Project-Description.md (outdated project name)
4. Archive docs/gaze-specification.md (out of scope feature)

### 📅 Phase 5 (PROPOSED)
**Target:** Before v1.0 Stable release

**Consolidation Tasks:**
1. Consolidate remaining quick-reference content into architecture docs
2. Review and archive all POC documentation
3. Create `docs/examples/` for any remaining demo content
4. Final documentation audit

**Final Cleanup:**
1. Archive POC documentation if features stabilized
2. Consolidate documentation tree

---

## Scripts to Keep (Actively Used)

### Essential CI/Reporting Scripts
- ✅ `scripts/generate_coverage_report.py` - Essential for coverage reporting
- ✅ `scripts/generate_quality_report.py` - Essential for quality metrics
- ✅ `scripts/sync_ci_to_anvil.py` - Critical for CI data integration
- ✅ `scripts/run_local_tests.py` - Essential for local testing

### Utility Scripts (Useful for Maintenance)
- ✅ `anvil/scripts/pre-commit-check.py` - Quality gate
- ✅ `anvil/scripts/setup-git-hooks.py` - Development setup
- ✅ `forge/scripts/pre-commit-check.py` - Quality gate
- ✅ `forge/scripts/setup-git-hooks.py` - Development setup
- ✅ `scout/scripts/pre-commit-check.py` - Quality gate
- ✅ `scout/scripts/setup-git-hooks.py` - Development setup
- ✅ `verdict/scripts/pre-commit-check.py` - Quality gate

---

## Documentation to Keep (High Value)

### Core Specifications
- ✅ `docs/anvil-specification.md` - Core component spec
- ✅ `docs/forge-specification.md` - Core component spec
- ✅ `docs/lens-specification.md` - Core component spec
- ✅ `docs/verdict-specification.md` - Core component spec

### Architecture & Design
- ✅ `docs/forge-architecture.md` - Critical for understanding CMake builds
- ✅ `docs/ANVIL_ARCHITECTURE_VISUAL.md` - Visual reference
- ✅ `docs/ANVIL_DATA_FLOW_GUIDE.md` - Data pipeline documentation
- ✅ `docs/project-organization.md` - Project structure reference

### Integration & Usage
- ✅ `docs/scout-anvil-lens-integration-plan.md` - Integration reference
- ✅ `docs/lens-usage-guide.md` - User documentation
- ✅ `docs/lens-implementation-plan.md` - Implementation details
- ✅ `docs/ANVIL_DOCUMENTATION_INDEX.md` - Navigation

### Quick References (Useful During Development)
- ✅ `docs/ci-sync-quick-reference.md` - Workflow reference
- ✅ `docs/coverage-quick-reference.md` - Coverage reference
- ✅ `docs/quality-quick-reference.md` - Quality reference
- ✅ `docs/CI-TROUBLESHOOTING.md` - Troubleshooting guide

---

## Summary Table

| Category | Count | Phase 3 Deleted | Phase 4 Deleted | Remaining |
|----------|-------|---|---|---|
| Demo/POC Scripts | 6 | - | 6 | - |
| Debug Utilities | 5 | - | 5 | - |
| Deprecated Scripts | 5 | - | 5 | - |
| Quick References | 5 | - | 5 | - |
| Troubleshooting/Integration | 2 | - | 2 | - |
| Old Implementation Plans | 4 | - | - | 4 (archive in Phase 4) |
| POC Documentation | 4 | - | - | 4 (archive in Phase 4) |
| Deprecated Specs | 2 | - | - | 2 (archive/delete in Phase 4) |
| Test/Validation Scripts | 5 | - | - | 5 (keep for now) |
| Active Documentation | 20+ | - | - | 20+ (keep) |
| **TOTAL** | 58+ | **28** | **22** | **8+** |

**Progress:** 50/58 files processed (86% complete)

---

## Action Items for Next Phase

### Immediate (Next Sprint)
- [ ] Document exact paths of deprecated scripts
- [ ] Identify any CI/workflow dependencies on deprecated items
- [ ] Plan archive directory structure

### Near-term (Before v1.0 Beta)
- [ ] Create `scripts/debug/` and `scripts/deprecated/` directories
- [ ] Move debug utilities and deprecated scripts accordingly
- [ ] Create `docs/archive/` directory
- [ ] Move old implementation plans to archive
- [ ] Delete `Argus-Project-Description.md`
- [ ] Delete `gaze-specification.md` or archive based on future plans

### Pre-v1.0 (Before Release)
- [ ] Consolidate quick-reference documents
- [ ] Review and archive all POC documentation
- [ ] Create `docs/examples/` for demo scripts
- [ ] Final documentation audit
- [ ] Delete deprecated items in `scripts/deprecated/`

---

## Notes

- All decisions are conservative to avoid breaking CI/workflows
- Demo scripts are kept for educational value and easy demo setup
- Old plans archived (not deleted) to preserve design decision history
- Focus on organization and consolidation rather than aggressive deletion
- Review for dependencies before any actual deletion
