"""
Pytest configuration and fixtures for Anvil tests.
"""

import pytest


@pytest.fixture
def temp_project(tmp_path):
    """
    Create a temporary project directory structure for testing.

    Returns:
        Path to the temporary project directory
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    return project_dir
