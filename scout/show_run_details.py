#!/usr/bin/env python
"""Display details of the most recent workflow execution with test results."""

from scout.storage import DatabaseManager
from scout.storage.schema import WorkflowRun, WorkflowJob, WorkflowTestResult
from collections import defaultdict

# Connect to database
db = DatabaseManager('scout.db')
db.initialize()
session = db.get_session()

# Get the most recent run
run = session.query(WorkflowRun).order_by(
    WorkflowRun.started_at.desc()).first()

if not run:
    print("No workflow runs found")
    session.close()
    exit(1)

status_icon = "✓" if run.conclusion == "success" else "✗" if run.conclusion == "failure" else "⊘"

print("\n" + "="*70)
print(f"WORKFLOW RUN DETAILS - Run ID {run.run_id}")
print("="*70)

print(f"\nWorkflow: {run.workflow_name}")
print(f"Status: {status_icon} {run.conclusion}")
print(f"Branch: {run.branch}")
print(f"Commit: {run.commit_sha}")
print(f"URL: {run.url}")
if run.started_at:
    print(f"Started: {run.started_at}")
if run.completed_at:
    print(f"Completed: {run.completed_at}")
if run.duration_seconds:
    minutes = run.duration_seconds // 60
    seconds = run.duration_seconds % 60
    print(f"Duration: {run.duration_seconds}s ({minutes}m {seconds}s)")

# Get jobs for this run
jobs = session.query(WorkflowJob).filter_by(run_id=run.run_id).all()

if jobs:
    print(f"\n{'JOBS':-^70}")
    print(f"Total: {len(jobs)} job(s)")

    # Group by status
    by_status = defaultdict(list)
    for job in jobs:
        by_status[job.conclusion or job.status].append(job)

    for status in ["failure", "success", "skipped", "cancelled"]:
        if status in by_status:
            job_list = by_status[status]
            status_icon = "✗" if status == "failure" else "✓" if status == "success" else "⊘"
            print(f"\n{status_icon} {status.upper()} ({len(job_list)}):")
            for job in job_list:
                print(f"  - {job.job_name}")
                if job.runner_os:
                    print(f"    Runner: {job.runner_os}")
                if job.python_version:
                    print(f"    Python: {job.python_version}")

# Get test results - filter by job IDs from this run
job_ids = [job.id for job in jobs]
test_results = (
    session.query(WorkflowTestResult)
    .filter(WorkflowTestResult.job_id.in_(job_ids))
    .all()
) if job_ids else []

# Also get all test results to see what's in the database
all_test_results = session.query(WorkflowTestResult).all()
print(f"\nNote: {len(all_test_results)} test result(s) total in database, {len(test_results)} from this run")

if test_results:
    print(f"\n{'TEST RESULTS':-^70}")
    print(f"Total: {len(test_results)} test(s)")

    # Group by outcome
    by_outcome = defaultdict(list)
    for result in test_results:
        by_outcome[result.outcome].append(result)

    for outcome in ["failed", "passed", "skipped"]:
        if outcome in by_outcome:
            results = by_outcome[outcome]
            outcome_icon = "✗" if outcome == "failed" else "✓" if outcome == "passed" else "⊘"
            print(f"\n{outcome_icon} {outcome.upper()} ({len(results)}):")
            for result in results[:10]:  # Show first 10
                duration_str = f" ({result.duration:.2f}s)" if result.duration else ""
                print(f"  - {result.test_nodeid}{duration_str}")
                if outcome == "failed" and result.error_message:
                    first_line = result.error_message.split("\n")[0][:60]
                    print(f"    Error: {first_line}...")
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more")

session.close()
print("\n" + "="*70 + "\n")
