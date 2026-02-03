import sqlite3
conn = sqlite3.connect('.anvil/history.db')

# Sample CI tests
print("Sample CI tests:")
rows = conn.execute('SELECT DISTINCT entity_id FROM execution_history WHERE space="ci" ORDER BY entity_id LIMIT 10').fetchall()
for r in rows:
    print(f'  {r[0][:70]}')

#Count total CI tests
total = conn.execute('SELECT COUNT(DISTINCT entity_id) FROM execution_history WHERE space="ci"').fetchone()[0]
print(f'\nTotal unique CI tests: {total}')

# Count total local tests
total_local = conn.execute('SELECT COUNT(DISTINCT entity_id) FROM execution_history WHERE space="local"').fetchone()[0]
print(f'Total unique local tests: {total_local}')

# Do they overlap?
overlap = conn.execute('SELECT COUNT(DISTINCT e1.entity_id) FROM execution_history e1 JOIN execution_history e2 ON e1.entity_id = e2.entity_id WHERE e1.space="local" AND e2.space="ci"').fetchone()[0]
print(f'Tests in BOTH local and CI: {overlap}')

conn.close()
