#!/usr/bin/env python
"""Check what projects are in the database."""
import sqlite3
from pathlib import Path

db_path = str(Path.home() / '.lens' / 'projects.db')
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute('SELECT * FROM projects')
rows = cursor.fetchall()

print(f"Total projects: {len(rows)}")
for row in rows:
    print(f"\nProject Details:")
    for key in row.keys():
        print(f"  {key}: {row[key]}")

conn.close()
