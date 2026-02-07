"""
Project data models for Lens.

Defines the Project dataclass and provides database operations
for project storage and retrieval.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List
import sqlite3
import json


@dataclass
class Project:
    """
    Represents a project in Lens.

    Attributes:
        name: Unique project name
        local_folder: Path to local project folder
        repo: GitHub repository in format 'owner/repo'
        token: Optional GitHub token for API access
        storage_location: Optional custom storage location
        id: Database ID (set by storage layer)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    name: str
    local_folder: str
    repo: str
    token: Optional[str] = None
    storage_location: Optional[str] = None
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """
        Convert project to dictionary.

        Returns:
            Dictionary representation of project
        """
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """
        Create project from dictionary.

        Args:
            data: Dictionary with project data

        Returns:
            Project instance

        Raises:
            ValueError: If required fields are missing
        """
        required_fields = {'name', 'local_folder', 'repo'}
        if not required_fields.issubset(data.keys()):
            raise ValueError(
                f"Missing required fields: {required_fields - set(data.keys())}")

        # Parse datetime strings if present
        created_at = None
        updated_at = None
        if 'created_at' in data and isinstance(data['created_at'], str):
            created_at = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            updated_at = datetime.fromisoformat(data['updated_at'])

        return cls(
            name=data['name'],
            local_folder=data['local_folder'],
            repo=data['repo'],
            token=data.get('token'),
            storage_location=data.get('storage_location'),
            id=data.get('id'),
            created_at=created_at,
            updated_at=updated_at
        )

    def validate(self) -> None:
        """
        Validate project data.

        Raises:
            ValueError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise ValueError("Project name cannot be empty")

        if not self.local_folder or not self.local_folder.strip():
            raise ValueError("Local folder cannot be empty")

        if not self.repo or not self.repo.strip():
            raise ValueError("Repository cannot be empty")

        # Validate repo format (owner/repo)
        if '/' not in self.repo:
            raise ValueError("Repository must be in format 'owner/repo'")

        # Validate local folder exists (as string, not requiring actual path)
        # Note: Actual validation could happen during project creation in the API

    def __repr__(self) -> str:
        """Return string representation of project."""
        return f"Project(id={self.id}, name='{self.name}', repo='{self.repo}')"
