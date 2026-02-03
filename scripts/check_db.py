"""Check database contents."""
from anvil.storage.execution_schema import ExecutionDatabase

db = ExecutionDatabase('.anvil/history.db')

cursor = db.connection.execute('SELECT COUNT(*) FROM execution_history')
print(f'Total executions: {cursor.fetchone()[0]}')

cursor = db.connection.execute('SELECT COUNT(*) FROM entity_statistics')
print(f'Entity statistics: {cursor.fetchone()[0]}')

cursor = db.connection.execute('SELECT entity_id, total_runs, passed, failed, failure_rate FROM entity_statistics LIMIT 5')
print('\nSample statistics:')
for row in cursor:
    entity_short = row[0][:60]
    print(f'  {entity_short}')
    print(f'    Runs: {row[1]}, Passed: {row[2]}, Failed: {row[3]}, Failure Rate: {row[4]*100:.1f}%')

db.close()
