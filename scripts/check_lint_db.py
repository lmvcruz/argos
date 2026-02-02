import sqlite3

conn = sqlite3.connect('.anvil/history.db')
cursor = conn.cursor()

# Get lint summaries
cursor.execute('SELECT space, execution_id, validator, errors, warnings, total_violations FROM lint_summary ORDER BY space, execution_id, validator')
summaries = cursor.fetchall()

print('\nLint Data in Database:')
print('=' * 95)
print(f"{'Space':<10} | {'Execution ID':<35} | {'Tool':<10} | {'Errors':<6} | {'Warnings':<8} | {'Total':<6}")
print('=' * 95)
for space, exec_id, tool, errors, warnings, total in summaries:
    print(f"{space:<10} | {exec_id:<35} | {tool:<10} | {errors:<6} | {warnings:<8} | {total:<6}")

print(f"\nTotal records: {len(summaries)}")

conn.close()
