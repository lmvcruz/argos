#!/usr/bin/env python
"""Display the last 5 workflow executions from Scout database."""

from scout.storage import DatabaseManager
from scout.storage.schema import WorkflowRun

# Connect to database
db = DatabaseManager('scout.db')
db.initialize()
session = db.get_session()

# Get the last 5 runs
runs = session.query(WorkflowRun).order_by(
    WorkflowRun.started_at.desc()).limit(5).all()

print("\n" + "="*70)
print("LAST 5 WORKFLOW EXECUTIONS")
print("="*70)

for i, run in enumerate(runs, 1):
    status_icon = "✓" if run.conclusion == "success" else "✗" if run.conclusion == "failure" else "⊘"

    print(f"\n{i}. Run #{run.run_number} - {run.workflow_name}")
    print(f"   Run ID: {run.run_id}")
    print(f"   Status: {status_icon} {run.conclusion}")
    print(f"   Branch: {run.branch}")
    print(f"   Commit: {run.commit_sha[:8]}")
    if run.started_at:
        print(f"   Started: {run.started_at}")
    if run.completed_at:
        print(f"   Completed: {run.completed_at}")

    # Count jobs if available
    job_count = len(run.jobs) if hasattr(run, 'jobs') else 0
    if job_count > 0:
        failed_jobs = sum(1 for j in run.jobs if j.conclusion == "failure")
        print(f"   Jobs: {job_count} total ({failed_jobs} failed)")

session.close()
print("\n" + "="*70 + "\n")
