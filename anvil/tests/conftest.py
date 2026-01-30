"""
Pytest configuration and fixtures for Anvil tests.
"""

import sys
from pathlib import Path

import pytest

# Add tests directory to Python path for helper imports
tests_dir = Path(__file__).parent
if str(tests_dir) not in sys.path:
    sys.path.insert(0, str(tests_dir))


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
