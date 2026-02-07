"""
Tests for Lens project API routes.

Tests the FastAPI endpoints for project management.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile


@pytest.fixture
def client():
    """Create test client with custom temp database."""
    from lens.backend.server import create_app
    from lens.backend.database import ProjectDatabase

    app = create_app()

    # Use temporary database for tests
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        app.projects_db = ProjectDatabase(db_path)

        yield TestClient(app)


class TestProjectRoutes:
    """Tests for project management routes."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'

    def test_create_project(self, client):
        """Test creating a project via API."""
        payload = {
            "name": "test-project",
            "local_folder": "/path/to/project",
            "repo": "owner/repo"
        }
        response = client.post("/api/projects", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "test-project"
        assert data['id'] is not None
        assert data['created_at'] is not None

    def test_create_project_missing_field(self, client):
        """Test creating project without required field."""
        payload = {
            "name": "test-project",
            "local_folder": "/path/to/project"
            # Missing 'repo'
        }
        response = client.post("/api/projects", json=payload)

        assert response.status_code == 400

    def test_create_project_duplicate_name(self, client):
        """Test creating project with duplicate name."""
        payload = {
            "name": "test-project",
            "local_folder": "/path/to/project",
            "repo": "owner/repo"
        }
        client.post("/api/projects", json=payload)

        # Try to create with same name
        response = client.post("/api/projects", json=payload)
        assert response.status_code == 400

    def test_list_projects(self, client):
        """Test listing projects."""
        # Create a few projects
        for i in range(3):
            payload = {
                "name": f"project-{i}",
                "local_folder": f"/path/{i}",
                "repo": f"owner/repo{i}"
            }
            client.post("/api/projects", json=payload)

        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 3
        assert len(data['projects']) == 3

    def test_list_projects_empty(self, client):
        """Test listing projects when none exist."""
        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 0
        assert data['projects'] == []

    def test_get_project(self, client):
        """Test getting a specific project."""
        payload = {
            "name": "test-project",
            "local_folder": "/path/to/project",
            "repo": "owner/repo"
        }
        create_response = client.post("/api/projects", json=payload)
        project_id = create_response.json()['id']

        response = client.get(f"/api/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "test-project"
        assert data['id'] == project_id

    def test_get_project_not_found(self, client):
        """Test getting non-existent project."""
        response = client.get("/api/projects/9999")

        assert response.status_code == 404

    def test_update_project(self, client):
        """Test updating a project."""
        # Create project
        payload = {
            "name": "test-project",
            "local_folder": "/path/to/project",
            "repo": "owner/repo"
        }
        create_response = client.post("/api/projects", json=payload)
        project_id = create_response.json()['id']

        # Update
        update_payload = {
            "name": "updated-project",
            "token": "github_token"
        }
        response = client.put(
            f"/api/projects/{project_id}", json=update_payload)

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "updated-project"
        assert data['token'] == "github_token"

    def test_update_project_not_found(self, client):
        """Test updating non-existent project."""
        response = client.put("/api/projects/9999", json={"name": "new-name"})

        assert response.status_code == 404

    def test_delete_project(self, client):
        """Test deleting a project."""
        # Create project
        payload = {
            "name": "test-project",
            "local_folder": "/path/to/project",
            "repo": "owner/repo"
        }
        create_response = client.post("/api/projects", json=payload)
        project_id = create_response.json()['id']

        # Delete
        response = client.delete(f"/api/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'deleted'

        # Verify it's deleted
        get_response = client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == 404

    def test_delete_project_not_found(self, client):
        """Test deleting non-existent project."""
        response = client.delete("/api/projects/9999")

        assert response.status_code == 404

    def test_get_active_project_none(self, client):
        """Test getting active project when none set."""
        response = client.get("/api/projects/active")

        # Status should be 200 with null active_project
        assert response.status_code == 200
        data = response.json()
        assert data.get('active_project') is None

    def test_set_active_project(self, client):
        """Test setting active project."""
        # Create project
        payload = {
            "name": "test-project",
            "local_folder": "/path/to/project",
            "repo": "owner/repo"
        }
        create_response = client.post("/api/projects", json=payload)
        project_id = create_response.json()['id']

        # Set as active
        response = client.post(f"/api/projects/{project_id}/select")

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'active'
        assert data['project']['id'] == project_id

        # Verify it's active
        get_response = client.get("/api/projects/active")
        assert get_response.status_code == 200
        active = get_response.json()
        assert active.get('active_project') is not None
        assert active['active_project']['id'] == project_id

    def test_set_active_project_not_found(self, client):
        """Test setting non-existent project as active."""
        response = client.post("/api/projects/9999/select")

        assert response.status_code == 404

    def test_active_project_workflow(self, client):
        """Test complete workflow of creating and managing active project."""
        # Create two projects
        proj1_payload = {
            "name": "project-1",
            "local_folder": "/path/1",
            "repo": "owner/repo1"
        }
        proj2_payload = {
            "name": "project-2",
            "local_folder": "/path/2",
            "repo": "owner/repo2"
        }

        proj1_response = client.post("/api/projects", json=proj1_payload)
        proj2_response = client.post("/api/projects", json=proj2_payload)

        proj1_id = proj1_response.json()['id']
        proj2_id = proj2_response.json()['id']

        # Set project 1 as active
        client.post(f"/api/projects/{proj1_id}/select")
        active_response = client.get("/api/projects/active")
        assert active_response.status_code == 200
        active = active_response.json()
        assert active.get('active_project') is not None
        assert active['active_project']['id'] == proj1_id

        # Switch to project 2
        client.post(f"/api/projects/{proj2_id}/select")
        active_response = client.get("/api/projects/active")
        assert active_response.status_code == 200
        active = active_response.json()
        assert active.get('active_project') is not None
        assert active['active_project']['id'] == proj2_id

        # Delete active project
        client.delete(f"/api/projects/{proj2_id}")
        active_response = client.get("/api/projects/active")
        assert active_response.status_code == 200
        active = active_response.json()
        assert active.get('active_project') is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
