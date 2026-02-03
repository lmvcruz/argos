import sqlite3

conn = sqlite3.connect('.anvil/history.db')

print("CHECKING CI DATA FOR COMMON TESTS")
print("=" * 80)

# Pick a test that should exist in both local and CI
test_pattern = "%test_models%"

print(f"\n1. Test pattern: {test_pattern}")

# Check local
c = conn.execute("SELECT COUNT(DISTINCT entity_id) FROM execution_history WHERE space='local' AND entity_id LIKE ?", (test_pattern,))
local_tests = c.fetchone()[0]
print(f"   Local unique tests matching: {local_tests}")

# Check CI
c = conn.execute("SELECT COUNT(DISTINCT entity_id) FROM execution_history WHERE space='ci' AND entity_id LIKE ?", (test_pattern,))
ci_tests = c.fetchone()[0]
print(f"   CI unique tests matching: {ci_tests}")

# Check a specific test
print("\n2. Specific test analysis:")
c = conn.execute("SELECT entity_id FROM execution_history WHERE entity_id LIKE ? LIMIT 1", (test_pattern,))
row = c.fetchone()
if row:
    test_id = row[0]
    print(f"   Test: {test_id}")

    # Count by space
    c = conn.execute("SELECT space, COUNT(*), SUM(CASE WHEN status='PASSED' THEN 1 ELSE 0 END), SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) FROM execution_history WHERE entity_id=? GROUP BY space", (test_id,))
    for row in c.fetchall():
        space = row[0]
        total = row[1]
        passed = row[2]
        failed = row[3]
        rate = (failed / total * 100) if total > 0 else 0
        print(f"   {space:6s}: {total:4d} runs, {passed:4d} passed, {failed:4d} failed, {rate:5.1f}% failure rate")

    # What does entity_statistics say?
    c = conn.execute("SELECT total_runs, passed, failed, failure_rate FROM entity_statistics WHERE entity_id=?", (test_id,))
    row = c.fetchone()
    if row:
        print(f"   STATS : {row[0]:4d} runs, {row[1]:4d} passed, {row[2]:4d} failed, {row[3]*100:5.1f}% failure rate")
        print("\n   ⚠️  PROBLEM: Statistics show different numbers than actual data!")

conn.close()
