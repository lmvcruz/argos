"""Check ExecutionLog table in Scout database."""
import sqlite3
from pathlib import Path

db_path = Path.home() / ".scout" / "lmvcruz" / "argos" / "scout.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Check count
cursor.execute("SELECT COUNT(*) FROM execution_logs")
count = cursor.fetchone()[0]
print(f"ExecutionLog records: {count}")

if count > 0:
    # Get sample data
    cursor.execute(
        "SELECT job_id, LENGTH(raw_content), content_type, stored_at FROM execution_logs LIMIT 5"
    )
    print("\nSample logs:")
    for row in cursor.fetchall():
        print(f"  job_id={row[0]}, content_length={row[1]} bytes, type={row[2]}, stored={row[3]}")

    # Get a small sample of content
    cursor.execute("SELECT raw_content FROM execution_logs LIMIT 1")
    sample_content = cursor.fetchone()[0]
    print(f"\nFirst 500 chars of log content:\n{sample_content[:500]}")

conn.close()
