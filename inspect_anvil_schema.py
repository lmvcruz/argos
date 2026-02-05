#!/usr/bin/env python3
"""Inspect the Anvil database schema to understand available tables and columns."""

import sqlite3

conn = sqlite3.connect(".anvil/execution.db")
cursor = conn.cursor()

# Get all tables
cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("\n" + "=" * 80)
print("ANVIL DATABASE SCHEMA")
print("=" * 80)

for table_name in tables:
    table = table_name[0]

    # Get table schema
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()

    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]

    print(f"\n[{table}] - {count} rows")
    print(f"  {'Column':<40} {'Type':<15}")
    print(f"  {'-' * 40} {'-' * 15}")
    for col in columns:
        col_name = col[1]
        col_type = col[2]
        print(f"  {col_name:<40} {col_type:<15}")

conn.close()
