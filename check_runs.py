"""Check recent workflow runs in Scout database."""
import sqlite3
from pathlib import Path

db_path = Path.home() / ".scout" / "lmvcruz" / "argos" / "scout.db"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get recent runs
cursor.execute(
    "SELECT run_id, workflow_name, status, conclusion FROM workflow_runs ORDER BY run_id DESC LIMIT 5"
)
print("Recent runs:")
for row in cursor.fetchall():
    print(f"  run_id={row[0]}, workflow={row[1]}, status={row[2]}, conclusion={row[3]}")

conn.close()
