"""
Initialize coverage tables in the Anvil database.

This script creates the coverage_history and coverage_summary tables
by instantiating the ExecutionDatabase, which runs _create_schema().
"""

import sys
from pathlib import Path

# Add anvil to path
anvil_path = Path(__file__).parent.parent / "anvil"
sys.path.insert(0, str(anvil_path))

from anvil.storage.execution_schema import ExecutionDatabase

def main():
    """Initialize coverage tables in database."""
    db_path = ".anvil/history.db"

    print(f"Initializing coverage schema in {db_path}...")

    # Create database connection (this will run _create_schema)
    db = ExecutionDatabase(db_path)

    # Verify tables exist
    cursor = db.connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    print(f"\n✅ Schema initialized. Tables in database:")
    for table in tables:
        print(f"  - {table}")

    # Check for coverage tables specifically
    coverage_tables = ["coverage_history", "coverage_summary"]
    missing = [t for t in coverage_tables if t not in tables]

    if missing:
        print(f"\n❌ Missing coverage tables: {missing}")
        return 1
    else:
        print(f"\n✅ All coverage tables created successfully!")
        return 0

    db.close()

if __name__ == "__main__":
    sys.exit(main())
