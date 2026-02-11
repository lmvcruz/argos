import sqlite3
from pathlib import Path

# Connect to Scout database
db_path = Path.home() / '.scout' / 'lmvcruz' / 'argos' / 'scout.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get logs for run 21786230446
cursor.execute('''
    SELECT job_id, job_name, LENGTH(raw_content) as log_size
    FROM execution_logs
    WHERE run_id = 21786230446
    LIMIT 5
''')

results = cursor.fetchall()

print('Logs available for run 21786230446 (Anvil Tests):\n')
for job_id, job_name, size in results:
    print(f'  Job {job_id}: {job_name} - {size:,} bytes')

print(f'\nTotal jobs with logs: {len(results)}')

# Show a snippet of the first log
cursor.execute('''
    SELECT raw_content
    FROM execution_logs
    WHERE run_id = 21786230446
    LIMIT 1
''')

log_content = cursor.fetchone()[0]
print(f'\n=== First 500 characters of log ===')
print(log_content[:500])

conn.close()
