import sqlite3

conn = sqlite3.connect('.anvil/history.db')
c = conn.cursor()

print("DATABASE ANALYSIS")
print("=" * 80)

# Check all space values
print("\n1. Executions by space (including NULL):")
c.execute("SELECT space, COUNT(*) FROM execution_history GROUP BY space")
for row in c.fetchall():
    space = row[0] if row[0] else "NULL/empty"
    print(f"   {space}: {row[1]:,}")

# Check entity_statistics - THE PROBLEM!
print("\n2. Entity statistics (aggregated WITHOUT space differentiation):")
c.execute("SELECT entity_id, total_runs, passed, failed, failure_rate FROM entity_statistics ORDER BY total_runs DESC LIMIT 5")
for row in c.fetchall():
    print(f"   {row[0][:60]}: runs={row[1]}, passed={row[2]}, failed={row[3]}, failure_rate={row[4]:.1%}")

# Check flaky tests from entity_statistics
print("\n3. FLAKY TESTS FROM ENTITY_STATISTICS (this is what Lens uses):")
c.execute("SELECT entity_id, total_runs, passed, failed, failure_rate FROM entity_statistics WHERE failure_rate >= 0.05 ORDER BY failure_rate DESC LIMIT 5")
for row in c.fetchall():
    print(f"   {row[0]}")
    print(f"      Runs: {row[1]}, Passed: {row[2]}, Failed: {row[3]}, Rate: {row[4]:.1%}")

# Check dates
print("\n4. Date distribution:")
c.execute("SELECT DATE(timestamp) as date, COUNT(*) FROM execution_history GROUP BY DATE(timestamp) ORDER BY date LIMIT 10")
for row in c.fetchall():
    print(f"   {row[0]}: {row[1]:,} executions")

# NOW THE KEY CHECK - compare entity_statistics vs actual execution_history
print("\n5. PROBLEM DETECTION - Do statistics match reality?")
print("\n   Checking test: anvil/tests/test_execution_schema.py::TestExecutionDatabase::test_insert_history")

# From entity_statistics
c.execute("SELECT total_runs, passed, failed, failure_rate FROM entity_statistics WHERE entity_id LIKE '%test_insert_history%' LIMIT 1")
row = c.fetchone()
if row:
    print(f"   entity_statistics says: runs={row[0]}, passed={row[1]}, failed={row[2]}, rate={row[3]:.1%}")

# From actual execution_history
c.execute("SELECT COUNT(*), SUM(CASE WHEN status='PASSED' THEN 1 ELSE 0 END), SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) FROM execution_history WHERE entity_id LIKE '%test_insert_history%'")
row = c.fetchone()
if row:
    failure_rate = row[2] / row[0] if row[0] > 0 else 0
    print(f"   execution_history says: runs={row[0]}, passed={row[1]}, failed={row[2]}, rate={failure_rate:.1%}")

# Check if statistics are space-specific
print("\n6. SPACE-SPECIFIC ANALYSIS for test_insert_history:")
c.execute("SELECT space, COUNT(*), SUM(CASE WHEN status='PASSED' THEN 1 ELSE 0 END), SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) FROM execution_history WHERE entity_id LIKE '%test_insert_history%' GROUP BY space")
for row in c.fetchall():
    space = row[0] if row[0] else "NULL"
    failure_rate = row[3] / row[1] if row[1] > 0 else 0
    print(f"   {space}: runs={row[1]}, passed={row[2]}, failed={row[3]}, rate={failure_rate:.1%}")

conn.close()
