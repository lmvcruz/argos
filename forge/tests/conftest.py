"""
Pytest configuration and shared fixtures.
"""

import pytest
import tempfile
from pathlib import Path


@pytest.fixture
def temp_dir():
    """Provide a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_source_dir(temp_dir):
    """Create a sample source directory with CMakeLists.txt."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()
    cmakelists = source_dir / "CMakeLists.txt"
    cmakelists.write_text("project(TestProject)\n")
    return source_dir


@pytest.fixture
def sample_build_dir(temp_dir):
    """Create a sample build directory."""
    build_dir = temp_dir / "build"
    build_dir.mkdir()
    return build_dir
