"""
Tests for Lens project database.

Tests the ProjectDatabase class and Project model.
"""

import tempfile
from pathlib import Path
from datetime import datetime
import pytest

from lens.backend.models.project import Project
from lens.backend.database import ProjectDatabase


class TestProject:
    """Tests for Project dataclass."""

    def test_create_project(self):
        """Test creating a project instance."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )

        assert project.name == "test-project"
        assert project.local_folder == "/path/to/project"
        assert project.repo == "owner/repo"
        assert project.token is None
        assert project.id is None

    def test_project_with_all_fields(self):
        """Test project with all fields set."""
        created_at = datetime.now()
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo",
            token="github_token",
            storage_location="/custom/storage",
            id=1,
            created_at=created_at,
            updated_at=created_at
        )

        assert project.id == 1
        assert project.token == "github_token"
        assert project.storage_location == "/custom/storage"
        assert project.created_at == created_at

    def test_project_to_dict(self):
        """Test converting project to dictionary."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo",
            id=1
        )

        project_dict = project.to_dict()

        assert project_dict['name'] == "test-project"
        assert project_dict['local_folder'] == "/path/to/project"
        assert project_dict['repo'] == "owner/repo"
        assert project_dict['id'] == 1

    def test_project_from_dict(self):
        """Test creating project from dictionary."""
        data = {
            "name": "test-project",
            "local_folder": "/path/to/project",
            "repo": "owner/repo",
            "id": 1,
            "token": "github_token"
        }

        project = Project.from_dict(data)

        assert project.name == "test-project"
        assert project.local_folder == "/path/to/project"
        assert project.repo == "owner/repo"
        assert project.id == 1
        assert project.token == "github_token"

    def test_project_from_dict_missing_required_field(self):
        """Test that from_dict raises error for missing required fields."""
        data = {
            "name": "test-project",
            "local_folder": "/path/to/project"
            # Missing 'repo'
        }

        with pytest.raises(ValueError, match="Missing required fields"):
            Project.from_dict(data)

    def test_project_validate_empty_name(self):
        """Test validation rejects empty name."""
        project = Project(
            name="",
            local_folder="/path/to/project",
            repo="owner/repo"
        )

        with pytest.raises(ValueError, match="Project name cannot be empty"):
            project.validate()

    def test_project_validate_empty_repo(self):
        """Test validation rejects empty repo."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo=""
        )

        with pytest.raises(ValueError, match="Repository cannot be empty"):
            project.validate()

    def test_project_validate_invalid_repo_format(self):
        """Test validation rejects invalid repo format."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="invalid-repo-format"  # Missing /
        )

        with pytest.raises(ValueError, match="Repository must be in format"):
            project.validate()

    def test_project_validate_valid(self):
        """Test validation passes for valid project."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )

        # Should not raise any exception
        project.validate()

    def test_project_repr(self):
        """Test project string representation."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo",
            id=1
        )

        repr_str = repr(project)

        assert "test-project" in repr_str
        assert "owner/repo" in repr_str
        assert "id=1" in repr_str


class TestProjectDatabase:
    """Tests for ProjectDatabase class."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = ProjectDatabase(db_path)
            yield db

    def test_database_initialization(self, temp_db):
        """Test database initializes schema."""
        assert temp_db.db_path.exists()

    def test_create_project(self, temp_db):
        """Test creating a project."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )

        created = temp_db.create_project(project)

        assert created.id is not None
        assert created.name == "test-project"
        assert created.created_at is not None
        assert created.updated_at is not None

    def test_create_duplicate_project_name(self, temp_db):
        """Test that duplicate project names are rejected."""
        project1 = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )
        temp_db.create_project(project1)

        project2 = Project(
            name="test-project",  # Same name
            local_folder="/path/to/other",
            repo="other/repo"
        )

        with pytest.raises(ValueError, match="already exists"):
            temp_db.create_project(project2)

    def test_get_project(self, temp_db):
        """Test retrieving a project by ID."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )
        created = temp_db.create_project(project)

        retrieved = temp_db.get_project(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "test-project"

    def test_get_project_not_found(self, temp_db):
        """Test retrieving non-existent project returns None."""
        retrieved = temp_db.get_project(9999)
        assert retrieved is None

    def test_get_project_by_name(self, temp_db):
        """Test retrieving project by name."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )
        temp_db.create_project(project)

        retrieved = temp_db.get_project_by_name("test-project")

        assert retrieved is not None
        assert retrieved.name == "test-project"

    def test_list_projects(self, temp_db):
        """Test listing all projects."""
        for i in range(3):
            project = Project(
                name=f"project-{i}",
                local_folder=f"/path/{i}",
                repo=f"owner/repo{i}"
            )
            temp_db.create_project(project)

        projects = temp_db.list_projects()

        assert len(projects) == 3
        assert all(isinstance(p, Project) for p in projects)

    def test_update_project(self, temp_db):
        """Test updating a project."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )
        created = temp_db.create_project(project)

        # Update
        created.name = "updated-project"
        created.token = "new_token"
        updated = temp_db.update_project(created)

        # Retrieve and verify
        retrieved = temp_db.get_project(updated.id)
        assert retrieved.name == "updated-project"
        assert retrieved.token == "new_token"

    def test_update_project_without_id(self, temp_db):
        """Test that update fails without project ID."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )

        with pytest.raises(ValueError, match="ID must be set"):
            temp_db.update_project(project)

    def test_delete_project(self, temp_db):
        """Test deleting a project."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )
        created = temp_db.create_project(project)

        deleted = temp_db.delete_project(created.id)
        assert deleted is True

        retrieved = temp_db.get_project(created.id)
        assert retrieved is None

    def test_delete_project_not_found(self, temp_db):
        """Test deleting non-existent project returns False."""
        deleted = temp_db.delete_project(9999)
        assert deleted is False

    def test_set_active_project(self, temp_db):
        """Test setting active project."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )
        created = temp_db.create_project(project)

        temp_db.set_active_project(created.id)

        active = temp_db.get_active_project()
        assert active is not None
        assert active.id == created.id

    def test_set_active_project_not_found(self, temp_db):
        """Test setting non-existent project as active fails."""
        with pytest.raises(ValueError, match="not found"):
            temp_db.set_active_project(9999)

    def test_get_active_project_none(self, temp_db):
        """Test getting active project when none set."""
        active = temp_db.get_active_project()
        assert active is None

    def test_set_active_project_replaces_previous(self, temp_db):
        """Test that setting active project replaces previous."""
        project1 = Project(
            name="project-1",
            local_folder="/path/1",
            repo="owner/repo1"
        )
        project2 = Project(
            name="project-2",
            local_folder="/path/2",
            repo="owner/repo2"
        )

        created1 = temp_db.create_project(project1)
        created2 = temp_db.create_project(project2)

        # Set first as active
        temp_db.set_active_project(created1.id)
        assert temp_db.get_active_project().id == created1.id

        # Set second as active
        temp_db.set_active_project(created2.id)
        assert temp_db.get_active_project().id == created2.id

    def test_delete_project_clears_active(self, temp_db):
        """Test that deleting active project clears active status."""
        project = Project(
            name="test-project",
            local_folder="/path/to/project",
            repo="owner/repo"
        )
        created = temp_db.create_project(project)
        temp_db.set_active_project(created.id)

        temp_db.delete_project(created.id)

        active = temp_db.get_active_project()
        assert active is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
