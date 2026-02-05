#!/usr/bin/env python
"""Show comprehensive summary of Scout database."""

from scout.storage import DatabaseManager
from scout.storage.schema import WorkflowRun, WorkflowJob, WorkflowTestResult

print("\n" + "="*70)
print("SCOUT WORKFLOW SUMMARY")
print("="*70)

db = DatabaseManager('scout.db')
db.initialize()
session = db.get_session()

# Get statistics
runs = session.query(WorkflowRun).all()
jobs = session.query(WorkflowJob).all()
tests = session.query(WorkflowTestResult).all()

print(f"\n📊 DATABASE STATISTICS:")
print(f"   Workflow Runs: {len(runs)}")
print(f"   Jobs: {len(jobs)}")
print(f"   Test Results: {len(tests)}")

# Get status breakdown
passed_runs = sum(1 for r in runs if r.conclusion == "success")
failed_runs = sum(1 for r in runs if r.conclusion == "failure")
print(f"\n📈 RUN STATUS:")
print(f"   ✓ Passed: {passed_runs} ({100*passed_runs/len(runs):.1f}%)")
print(f"   ✗ Failed: {failed_runs} ({100*failed_runs/len(runs):.1f}%)")

# Get test breakdown
passed_tests = sum(1 for t in tests if t.outcome == "passed")
failed_tests = sum(1 for t in tests if t.outcome == "failed")
skipped_tests = sum(1 for t in tests if t.outcome == "skipped")
print(f"\n🧪 TEST RESULTS:")
print(f"   ✓ Passed: {passed_tests}")
print(f"   ✗ Failed: {failed_tests}")
print(f"   ⊘ Skipped: {skipped_tests}")

# Get platforms
platforms = set()
for job in jobs:
    if job.runner_os:
        platforms.add(job.runner_os)

print(f"\n🖥️  PLATFORMS TESTED:")
for platform in sorted(platforms):
    platform_jobs = sum(1 for j in jobs if j.runner_os == platform)
    platform_failed = sum(1 for j in jobs if j.runner_os ==
                          platform and j.conclusion == "failure")
    print(f"   {platform}: {platform_jobs} jobs ({platform_failed} failed)")

session.close()
print("\n" + "="*70 + "\n")
