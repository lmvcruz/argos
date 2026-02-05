#!/usr/bin/env python
"""Complete Scout workflow demo: fetch, parse, and show executions."""

from scout.storage import DatabaseManager
from scout.storage.schema import WorkflowRun, WorkflowJob, WorkflowTestResult
from collections import defaultdict
from datetime import datetime

print("\n" + "="*70)
print("SCOUT WORKFLOW DEMO: FETCH, PARSE & SHOW")
print("="*70)

# Initialize database
db = DatabaseManager('scout.db')
db.initialize()
session = db.get_session()

print(f"\n✓ Database initialized: scout.db")

# ============================================================================
# STEP 1: FETCH (Show what was fetched)
# ============================================================================
print("\n" + "-"*70)
print("STEP 1: FETCH - CI Workflow Data")
print("-"*70)

runs = session.query(WorkflowRun).order_by(WorkflowRun.started_at.desc()).all()
print(f"\n✓ Fetched {len(runs)} workflow runs from GitHub Actions")
print(f"  Workflow: Anvil Tests")
print(f"  Repository: lmvcruz/argos")
print(f"  Date range: {runs[-1].started_at} to {runs[0].started_at}")

# Show workflow breakdown
conclusions = defaultdict(int)
for run in runs:
    conclusions[run.conclusion] += 1

for conclusion, count in sorted(conclusions.items()):
    icon = "✓" if conclusion == "success" else "✗" if conclusion == "failure" else "⊘"
    pct = 100 * count / len(runs)
    print(f"    {icon} {conclusion}: {count} ({pct:.1f}%)")

# ============================================================================
# STEP 2: PARSE (Show what was parsed)
# ============================================================================
print("\n" + "-"*70)
print("STEP 2: PARSE - Extract Test Results & Job Details")
print("-"*70)

jobs = session.query(WorkflowJob).all()
tests = session.query(WorkflowTestResult).all()

print(f"\n✓ Parsed {len(jobs)} jobs from workflow runs")
print(f"  Job details extracted: status, duration, runner, Python version")

# Show job matrix
python_versions = set()
runners = set()
for job in jobs:
    if job.python_version:
        python_versions.add(job.python_version)
    if job.runner_os:
        runners.add(job.runner_os)

print(f"\n✓ Parsed {len(tests)} test results")
print(f"  Test details extracted: outcome, duration, error messages")
print(f"\n  Test matrix:")
print(f"    Platforms: {', '.join(sorted(runners))}")
print(f"    Python versions: {', '.join(sorted(python_versions))}")

# ============================================================================
# STEP 3: SHOW - Display Last 5 Executions
# ============================================================================
print("\n" + "-"*70)
print("STEP 3: SHOW - Last 5 Executions")
print("-"*70 + "\n")

last_runs = session.query(WorkflowRun).order_by(
    WorkflowRun.started_at.desc()).limit(5).all()

for i, run in enumerate(last_runs, 1):
    status_icon = "✓" if run.conclusion == "success" else "✗"
    minutes = (run.duration_seconds // 60) if run.duration_seconds else 0
    seconds = (run.duration_seconds % 60) if run.duration_seconds else 0
    duration_str = f"{minutes}m {seconds}s" if run.duration_seconds else "unknown"

    print(f"{i}. {status_icon} Run {run.run_id}")
    print(f"   Branch: {run.branch} | Commit: {run.commit_sha[:8]}")
    print(f"   Status: {run.conclusion} | Duration: {duration_str}")
    print(f"   Started: {run.started_at}")

    # Job summary
    run_jobs = session.query(WorkflowJob).filter_by(run_id=run.run_id).all()
    if run_jobs:
        failed_count = sum(1 for j in run_jobs if j.conclusion == "failure")
        print(f"   Jobs: {len(run_jobs)} total ({failed_count} failed)")
    print()

# Show test results summary
print("-"*70)
print("Test Results Summary")
print("-"*70)

if tests:
    print(f"\nSample test results from parsing:")
    for test in tests[:3]:
        outcome_icon = "✓" if test.outcome == "passed" else "✗" if test.outcome == "failed" else "⊘"
        duration_str = f"({test.duration:.2f}s)" if test.duration else ""
        print(f"  {outcome_icon} {test.test_nodeid} {duration_str}")
        if test.outcome == "failed" and test.error_message:
            error_line = test.error_message.split("\n")[0][:60]
            print(f"     Error: {error_line}...")
else:
    print("\nNo test results parsed yet.")

print("\n" + "="*70)
print("✓ Scout workflow demo completed successfully!")
print("="*70 + "\n")

session.close()
