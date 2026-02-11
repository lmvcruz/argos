"""Check Scout database status."""
import sqlite3
from pathlib import Path

db_path = Path.home() / '.scout' / 'lmvcruz' / 'argos' / 'scout.db'
print(f"Database path: {db_path}")
print(f"Database exists: {db_path.exists()}")
print()

if db_path.exists():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # List tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"Tables: {tables}")
    print()

    # Check workflow_runs
    cursor.execute("SELECT run_id, has_logs, logs_downloaded_at FROM workflow_runs ORDER BY run_id DESC LIMIT 5")
    print("Recent workflow runs:")
    for row in cursor.fetchall():
        print(f"  Run {row[0]}: has_logs={row[1]}, downloaded={row[2]}")
    print()

    # Check execution_logs schema
    cursor.execute("PRAGMA table_info(execution_logs)")
    print("ExecutionLog table schema:")
    for row in cursor.fetchall():
        print(f"  {row[1]} ({row[2]})")
    print()

    # Check execution_logs content
    cursor.execute("SELECT COUNT(*), SUM(CASE WHEN raw_content IS NOT NULL AND LENGTH(raw_content) > 0 THEN 1 ELSE 0 END) FROM execution_logs")
    row = cursor.fetchone()
    print(f"ExecutionLog: Total rows: {row[0]}, With content: {row[1]}")
    print()

    # Sample some execution logs
    cursor.execute("SELECT job_id, LENGTH(raw_content), content_type, stored_at FROM execution_logs LIMIT 5")
    print("Sample execution logs:")
    for row in cursor.fetchall():
        print(f"  Job {row[0]}: content_length={row[1]}, type={row[2]}, stored={row[3]}")
    print()

    # Check workflow_jobs
    cursor.execute("SELECT job_id, job_name, run_id, has_logs FROM workflow_jobs WHERE run_id IN (21786230446, 21786230460) LIMIT 10")
    print("Workflow jobs for recent runs:")
    for row in cursor.fetchall():
        print(f"  Job {row[0]} ({row[1]}): run_id={row[2]}, has_logs={row[3]}")

    conn.close()
