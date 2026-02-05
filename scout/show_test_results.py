#!/usr/bin/env python
"""Display all test results in the database."""

from scout.storage import DatabaseManager
from scout.storage.schema import WorkflowTestResult, WorkflowJob

# Connect to database
db = DatabaseManager('scout.db')
db.initialize()
session = db.get_session()

# Get all test results
test_results = session.query(WorkflowTestResult).all()

print("\n" + "="*70)
print("ALL TEST RESULTS IN DATABASE")
print("="*70)

if not test_results:
    print("\nNo test results found")
else:
    print(f"\nTotal: {len(test_results)} test result(s)\n")

    for i, result in enumerate(test_results, 1):
        # Get job info
        job = session.query(WorkflowJob).filter_by(id=result.job_id).first()
        job_name = job.job_name if job else "Unknown"

        outcome_icon = "✗" if result.outcome == "failed" else "✓" if result.outcome == "passed" else "⊘"

        print(f"{i}. {outcome_icon} {result.test_nodeid}")
        print(f"   Outcome: {result.outcome}")
        print(f"   Job: {job_name}")
        if result.python_version:
            print(f"   Python: {result.python_version}")
        if result.runner_os:
            print(f"   OS: {result.runner_os}")
        if result.duration:
            print(f"   Duration: {result.duration:.2f}s")
        if result.error_message:
            first_line = result.error_message.split("\n")[0][:80]
            print(f"   Error: {first_line}")
        print()

session.close()
print("="*70 + "\n")
