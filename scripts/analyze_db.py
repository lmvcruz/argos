"""Analyze the database to understand what's stored."""

import sqlite3
from datetime import datetime

db_path = ".anvil/history.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("DATABASE ANALYSIS")
print("=" * 80)

# Total counts by space
print("\n1. EXECUTIONS BY SPACE:")
cursor.execute("""
    SELECT space, COUNT(*) as count
    FROM execution_history
    GROUP BY space
    ORDER BY count DESC
""")
for row in cursor.fetchall():
    space = row[0] if row[0] else 'NULL'
    print(f"   {space}: {row[1]:,}")

# Date range by space
print("\n2. DATE RANGE BY SPACE:")
cursor.execute("""
    SELECT
        space,
        MIN(timestamp) as earliest,
        MAX(timestamp) as latest,
        COUNT(*) as count
    FROM execution_history
    GROUP BY space
""")
for row in cursor.fetchall():
    space = row[0] if row[0] else 'NULL'
    print(f"\n   {space}:")
    print(f"      Earliest: {row[1]}")
    print(f"      Latest: {row[2]}")
    print(f"      Count: {row[3]:,}")

# Sample CI executions
print("\n3. SAMPLE CI EXECUTIONS:")
cursor.execute("""
    SELECT
        execution_id,
        entity_id,
        timestamp,
        status,
        metadata
    FROM execution_history
    WHERE space = 'ci'
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"\n   Execution: {row[0]}")
    print(f"   Test: {row[1]}")
    print(f"   Timestamp: {row[2]}")
    print(f"   Status: {row[3]}")
    print(f"   Metadata: {row[4][:100]}...")

# Sample local executions
print("\n4. SAMPLE LOCAL EXECUTIONS:")
cursor.execute("""
    SELECT
        execution_id,
        entity_id,
        timestamp,
        status
    FROM execution_history
    WHERE space = 'local'
    LIMIT 5
""")
for row in cursor.fetchall():
    print(f"\n   Execution: {row[0]}")
    print(f"   Test: {row[1]}")
    print(f"   Timestamp: {row[2]}")
    print(f"   Status: {row[3]}")

# Check entity_statistics
print("\n5. ENTITY STATISTICS:")
cursor.execute("""
    SELECT
        entity_id,
        total_executions,
        passed,
        failed,
        avg_duration
    FROM entity_statistics
    ORDER BY total_executions DESC
    LIMIT 10
""")
print("\n   Top 10 entities by execution count:")
for row in cursor.fetchall():
    print(f"   {row[0][:60]:60s} | Runs: {row[1]:4d} | Pass: {row[2]:4d} | Fail: {row[3]:4d} | Avg: {row[4]:.2f}s")

# Check for CI-specific statistics
print("\n6. CI VS LOCAL STATISTICS:")
cursor.execute("""
    SELECT
        space,
        COUNT(DISTINCT entity_id) as unique_tests,
        COUNT(*) as total_executions,
        SUM(CASE WHEN status = 'PASSED' THEN 1 ELSE 0 END) as passed,
        SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) as failed
    FROM execution_history
    GROUP BY space
""")
for row in cursor.fetchall():
    space = row[0] if row[0] else 'NULL'
    print(f"\n   {space}:")
    print(f"      Unique tests: {row[1]:,}")
    print(f"      Total executions: {row[2]:,}")
    print(f"      Passed: {row[3]:,}")
    print(f"      Failed: {row[4]:,}")
    success_rate = (row[3] / row[2] * 100) if row[2] > 0 else 0
    print(f"      Success rate: {success_rate:.1f}%")

# Check if entity_statistics is aggregating across spaces
print("\n7. CHECKING IF STATISTICS ARE SPACE-AWARE:")
cursor.execute("""
    SELECT COUNT(*) FROM pragma_table_info('entity_statistics') WHERE name='space'
""")
has_space_column = cursor.fetchone()[0] > 0
print(f"   entity_statistics has 'space' column: {has_space_column}")

conn.close()

print("\n" + "=" * 80)
