#!/usr/bin/env python3
"""Fix duplicate path in project database."""

import sqlite3
from pathlib import Path

db_path = Path.home() / '.lens' / 'projects.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Get all projects
cursor.execute('SELECT id, name, local_folder FROM projects')
projects = cursor.fetchall()

print('Current projects:')
for id, name, local_folder in projects:
    print(f'  ID {id}: {name} -> {local_folder}')

# Fix the Argos project if it has duplicated path
cursor.execute(
    'SELECT id, local_folder FROM projects WHERE name=?', ('Argos',))
result = cursor.fetchone()
if result:
    project_id, local_folder = result
    print(f'\nFound Argos project (ID {project_id}): {local_folder}')
    if 'argos\\argos' in local_folder.lower() or 'argos/argos' in local_folder.lower():
        fixed_path = local_folder.replace('argos\\argos', 'argos').replace(
            'argos\\\\argos', 'argos').replace('argos/argos', 'argos')
        print(f'Fixing duplicate path...')
        print(f'  Old: {local_folder}')
        print(f'  New: {fixed_path}')
        cursor.execute(
            'UPDATE projects SET local_folder=? WHERE id=?', (fixed_path, project_id))
        conn.commit()
        print('✓ Fixed!')
    else:
        print(f'Path looks OK: {local_folder}')
else:
    print('No Argos project found')

conn.close()
