"""
Database manager for Scout CI data storage.

This module provides a database manager for creating, connecting to,
and managing the Scout CI data database.
"""

from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from scout.storage.schema import Base


class DatabaseManager:
    """
    Database manager for Scout CI data storage.

    Handles database creation, connection management, and session
    lifecycle for storing and querying CI data.

    Args:
        db_path: Path to SQLite database file (default: ~/.scout/scout.db)
        echo: Whether to echo SQL statements (default: False)

    Examples:
        >>> db = DatabaseManager(db_path=":memory:")
        >>> db.initialize()
        >>> session = db.get_session()
        >>> session.close()
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        echo: bool = False,
    ):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file (default: ~/.scout/scout.db)
            echo: Whether to echo SQL statements (default: False)
        """
        if db_path is None:
            # Default to ~/.scout/scout.db
            scout_dir = Path.home() / ".scout"
            scout_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(scout_dir / "scout.db")

        self.db_path = db_path
        self.echo = echo
        self._engine: Optional[Engine] = None
        self._session_factory: Optional[sessionmaker] = None

    @property
    def engine(self) -> Engine:
        """
        Get SQLAlchemy engine.

        Returns:
            SQLAlchemy Engine instance

        Raises:
            RuntimeError: If database has not been initialized
        """
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._engine

    def initialize(self) -> None:
        """
        Initialize database and create tables.

        Creates the database file (if it doesn't exist) and all tables
        defined in the schema.
        """
        # Create engine
        db_url = f"sqlite:///{self.db_path}"
        self._engine = create_engine(db_url, echo=self.echo)

        # Create all tables
        Base.metadata.create_all(self._engine)

        # Create session factory
        self._session_factory = sessionmaker(bind=self._engine)

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy Session instance

        Raises:
            RuntimeError: If database has not been initialized

        Examples:
            >>> db = DatabaseManager(db_path=":memory:")
            >>> db.initialize()
            >>> session = db.get_session()
            >>> # Use session...
            >>> session.close()
        """
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")
        return self._session_factory()

    def reset(self) -> None:
        """
        Reset database by dropping all tables and recreating them.

        Warning:
            This will delete all data in the database!
        """
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call initialize() first.")

        # Drop all tables
        Base.metadata.drop_all(self._engine)

        # Recreate all tables
        Base.metadata.create_all(self._engine)

    def close(self) -> None:
        """Close database connection."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
