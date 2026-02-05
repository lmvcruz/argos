#!/usr/bin/env python
"""Check Anvil database schema."""

import sqlite3

conn = sqlite3.connect('.anvil/execution.db')
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Tables in Anvil database:")
for table in tables:
    table_name = table[0]
    print(f"\n  {table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    for col in columns:
        print(f"    - {col[1]} ({col[2]})")

# Try to get some data from the main tables
print("\n\nData samples:")

for table_name in ['workflow_run', 'execution', 'execution_history']:
    try:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [col[1] for col in cursor.fetchall()]
            print(f"\n{table_name} ({len(rows)} rows):")
            for row in rows:
                print(f"  {dict(zip(columns, row))}")
    except Exception as e:
        print(f"\n{table_name}: {e}")

conn.close()
