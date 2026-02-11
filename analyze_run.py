"""Analyze a specific Scout run to understand failures."""

import sqlite3
from pathlib import Path

run_id = 21786230446
db_path = Path.home() / '.scout' / 'lmvcruz' / 'argos' / 'scout.db'

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print(f"\n=== Analysis for Run ID: {run_id} ===\n")

# First check what columns exist
cursor.execute("PRAGMA table_info(workflow_runs)")
print("Available columns in workflow_runs:")
for col in cursor.fetchall():
    print(f"  - {col[1]} ({col[2]})")
print()

# Get run information
cursor.execute("""
    SELECT run_number, workflow_name, event, status, conclusion, started_at
    FROM workflow_runs
    WHERE run_id = ?
""", (run_id,))

run_info = cursor.fetchone()
if run_info:
    print(f"Run Number: {run_info[0]}")
    print(f"Workflow: {run_info[1]}")
    print(f"Event: {run_info[2]}")
    print(f"Status: {run_info[3]}")
    print(f"Conclusion: {run_info[4]}")
    print(f"Started: {run_info[5]}")
else:
    print("Run not found!")
    exit(1)

# Get all jobs for this run
cursor.execute("""
    SELECT job_id, job_name, status, conclusion, started_at, completed_at
    FROM workflow_jobs
    WHERE run_id = ?
    ORDER BY job_id
""", (run_id,))

jobs = cursor.fetchall()
print(f"\n=== Jobs ({len(jobs)} total) ===\n")

failed_jobs = []
for job in jobs:
    job_id, job_name, status, conclusion, started, completed = job
    status_icon = "[OK]" if conclusion == "success" else "[FAIL]"
    print(f"{status_icon} Job {job_id}: {job_name}")
    print(f"   Status: {status}, Conclusion: {conclusion}")

    if conclusion == "failure":
        failed_jobs.append((job_id, job_name))

        # Get log size
        cursor.execute("""
            SELECT LENGTH(raw_content) as log_size
            FROM execution_logs
            WHERE job_id = ?
        """, (job_id,))

        log_info = cursor.fetchone()
        if log_info and log_info[0]:
            print(f"   Log size: {log_info[0]:,} bytes")

            # Get a snippet of the log to show errors
            cursor.execute("""
                SELECT raw_content
                FROM execution_logs
                WHERE job_id = ?
            """, (job_id,))

            log_content = cursor.fetchone()
            if log_content and log_content[0]:
                lines = log_content[0].split('\n')
                # Look for error patterns
                error_lines = [l for l in lines if 'error' in l.lower() or 'failed' in l.lower() or 'traceback' in l.lower()]

                if error_lines:
                    print(f"   Found {len(error_lines)} lines with error indicators")
                    print(f"   Sample errors:")
                    for err_line in error_lines[:3]:
                        print(f"      {err_line[:100]}")
    print()

if failed_jobs:
    print(f"\n=== Summary: {len(failed_jobs)} job(s) failed ===")
    for job_id, job_name in failed_jobs:
        print(f"  - {job_name} (ID: {job_id})")
else:
    print("\n=== All jobs passed! ===")

conn.close()
