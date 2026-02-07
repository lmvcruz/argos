"""
Database layer for Lens projects.

Manages SQLite database for project storage and retrieval.
Handles database initialization, migrations, and CRUD operations.
"""

from pathlib import Path
from typing import Optional, List
import sqlite3
from datetime import datetime
import json

from lens.backend.models.project import Project
from lens.backend.logging_config import get_logger

logger = get_logger(__name__)


class ProjectDatabase:
    """
    Manages SQLite database for Lens projects.

    Database location: ~/.lens/projects.db
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize database connection.

        Args:
            db_path: Optional custom database path (default: ~/.lens/projects.db)
        """
        if db_path is None:
            db_path = Path.home() / '.lens' / 'projects.db'

        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        logger.info(f"ProjectDatabase initialized at {self.db_path}")

    def _init_schema(self) -> None:
        """Initialize database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Create projects table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    local_folder TEXT NOT NULL,
                    repo TEXT NOT NULL,
                    token TEXT,
                    storage_location TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Create active_project table (stores single active project ID)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS active_project (
                    project_id INTEGER PRIMARY KEY,
                    FOREIGN KEY (project_id) REFERENCES projects(id)
                        ON DELETE SET NULL
                )
            ''')

            conn.commit()
            logger.debug("Database schema initialized")
        except sqlite3.Error as e:
            logger.error(f"Error initializing schema: {e}")
            raise
        finally:
            conn.close()

    def create_project(self, project: Project) -> Project:
        """
        Create a new project in the database.

        Args:
            project: Project instance to create

        Returns:
            Project with ID set

        Raises:
            ValueError: If project data is invalid
            sqlite3.IntegrityError: If project name already exists
        """
        project.validate()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO projects
                (name, local_folder, repo, token, storage_location)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                project.name,
                project.local_folder,
                project.repo,
                project.token,
                project.storage_location
            ))

            project.id = cursor.lastrowid
            project.created_at = datetime.now()
            project.updated_at = datetime.now()

            conn.commit()
            logger.info(f"Created project: {project.name} (ID: {project.id})")
            return project

        except sqlite3.IntegrityError as e:
            logger.error(f"Integrity error creating project: {e}")
            raise ValueError(
                f"Project name '{project.name}' already exists") from e
        except sqlite3.Error as e:
            logger.error(f"Error creating project: {e}")
            raise
        finally:
            conn.close()

    def get_project(self, project_id: int) -> Optional[Project]:
        """
        Get project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project instance or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                'SELECT * FROM projects WHERE id = ?',
                (project_id,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_project(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Error getting project: {e}")
            raise
        finally:
            conn.close()

    def get_project_by_name(self, name: str) -> Optional[Project]:
        """
        Get project by name.

        Args:
            name: Project name

        Returns:
            Project instance or None if not found
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute(
                'SELECT * FROM projects WHERE name = ?',
                (name,)
            )
            row = cursor.fetchone()

            if row:
                return self._row_to_project(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Error getting project by name: {e}")
            raise
        finally:
            conn.close()

    def list_projects(self) -> List[Project]:
        """
        List all projects.

        Returns:
            List of Project instances
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT * FROM projects ORDER BY created_at DESC')
            rows = cursor.fetchall()
            return [self._row_to_project(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error listing projects: {e}")
            raise
        finally:
            conn.close()

    def update_project(self, project: Project) -> Project:
        """
        Update an existing project.

        Args:
            project: Project instance with updates

        Returns:
            Updated project

        Raises:
            ValueError: If project ID not set or project not found
        """
        if project.id is None:
            raise ValueError("Project ID must be set for update")

        project.validate()
        project.updated_at = datetime.now()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                UPDATE projects
                SET name = ?, local_folder = ?, repo = ?,
                    token = ?, storage_location = ?, updated_at = ?
                WHERE id = ?
            ''', (
                project.name,
                project.local_folder,
                project.repo,
                project.token,
                project.storage_location,
                project.updated_at,
                project.id
            ))

            if cursor.rowcount == 0:
                raise ValueError(f"Project with ID {project.id} not found")

            conn.commit()
            logger.info(f"Updated project: {project.name} (ID: {project.id})")
            return project

        except sqlite3.Error as e:
            logger.error(f"Error updating project: {e}")
            raise
        finally:
            conn.close()

    def delete_project(self, project_id: int) -> bool:
        """
        Delete a project.

        Args:
            project_id: Project ID to delete

        Returns:
            True if deleted, False if not found
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Clear active project if it's the one being deleted
            cursor.execute(
                'DELETE FROM active_project WHERE project_id = ?', (project_id,))

            # Delete the project
            cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))

            deleted = cursor.rowcount > 0
            conn.commit()

            if deleted:
                logger.info(f"Deleted project ID: {project_id}")
            else:
                logger.warning(
                    f"Project ID {project_id} not found for deletion")

            return deleted

        except sqlite3.Error as e:
            logger.error(f"Error deleting project: {e}")
            raise
        finally:
            conn.close()

    def set_active_project(self, project_id: int) -> None:
        """
        Set the active project.

        Args:
            project_id: Project ID to set as active

        Raises:
            ValueError: If project doesn't exist
        """
        # Verify project exists
        if self.get_project(project_id) is None:
            raise ValueError(f"Project with ID {project_id} not found")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Clear existing active project
            cursor.execute('DELETE FROM active_project')

            # Set new active project
            cursor.execute(
                'INSERT INTO active_project (project_id) VALUES (?)',
                (project_id,)
            )

            conn.commit()
            logger.info(f"Set active project to ID: {project_id}")

        except sqlite3.Error as e:
            logger.error(f"Error setting active project: {e}")
            raise
        finally:
            conn.close()

    def get_active_project(self) -> Optional[Project]:
        """
        Get the currently active project.

        Returns:
            Active project or None if none set
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute('''
                SELECT p.* FROM projects p
                JOIN active_project ap ON p.id = ap.project_id
            ''')
            row = cursor.fetchone()

            if row:
                return self._row_to_project(row)
            return None

        except sqlite3.Error as e:
            logger.error(f"Error getting active project: {e}")
            raise
        finally:
            conn.close()

    @staticmethod
    def _row_to_project(row: sqlite3.Row) -> Project:
        """
        Convert database row to Project instance.

        Args:
            row: SQLite Row object

        Returns:
            Project instance
        """
        return Project(
            id=row['id'],
            name=row['name'],
            local_folder=row['local_folder'],
            repo=row['repo'],
            token=row['token'],
            storage_location=row['storage_location'],
            created_at=datetime.fromisoformat(
                row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(
                row['updated_at']) if row['updated_at'] else None
        )
