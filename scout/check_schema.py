#!/usr/bin/env python
from scout.storage.database import DatabaseManager
import sqlalchemy as sa

db = DatabaseManager(db_path='scout.db')
db.initialize()
inspector = sa.inspect(db.engine)
for table_name in inspector.get_table_names():
    print(f'\n{table_name}:')
    for col in inspector.get_columns(table_name):
        print(f'  {col["name"]}: {col["type"]}')
