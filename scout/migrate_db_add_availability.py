"""
Database migration script to add data availability columns.

Adds has_logs, has_parsed_data, logs_downloaded_at, and data_parsed_at
columns to workflow_runs and workflow_jobs tables.
"""

import sqlite3
import sys
from pathlib import Path


def migrate_database(db_path: str) -> None:
    """
    Add data availability columns to existing database.

    Args:
        db_path: Path to SQLite database file
    """
    print(f"Migrating database: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Add columns to workflow_runs table
        print("Adding columns to workflow_runs table...")
        cursor.execute(
            "ALTER TABLE workflow_runs ADD COLUMN has_logs INTEGER DEFAULT 0 NOT NULL"
        )
        cursor.execute(
            "ALTER TABLE workflow_runs ADD COLUMN has_parsed_data INTEGER DEFAULT 0 NOT NULL"
        )
        cursor.execute("ALTER TABLE workflow_runs ADD COLUMN logs_downloaded_at DATETIME")
        cursor.execute("ALTER TABLE workflow_runs ADD COLUMN data_parsed_at DATETIME")

        # Add columns to workflow_jobs table
        print("Adding columns to workflow_jobs table...")
        cursor.execute(
            "ALTER TABLE workflow_jobs ADD COLUMN has_logs INTEGER DEFAULT 0 NOT NULL"
        )
        cursor.execute(
            "ALTER TABLE workflow_jobs ADD COLUMN has_parsed_data INTEGER DEFAULT 0 NOT NULL"
        )
        cursor.execute("ALTER TABLE workflow_jobs ADD COLUMN logs_downloaded_at DATETIME")
        cursor.execute("ALTER TABLE workflow_jobs ADD COLUMN data_parsed_at DATETIME")

        conn.commit()
        print("✓ Migration completed successfully")

    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✓ Columns already exist, no migration needed")
        else:
            raise

    finally:
        conn.close()


if __name__ == "__main__":
    # Default to lmvcruz/argos repo database
    db_path = Path.home() / ".scout" / "lmvcruz" / "argos" / "scout.db"

    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    migrate_database(str(db_path))
