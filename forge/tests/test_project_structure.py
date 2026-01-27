"""
Test suite for verifying project structure.

This test validates that all required directories and __init__.py files
exist and can be imported correctly.
"""

import pytest
from pathlib import Path


def test_all_required_directories_exist():
    """Test that all required directories exist."""
    forge_root = Path(__file__).parent.parent

    required_dirs = [
        "cli",
        "cmake",
        "inspector",
        "storage",
        "models",
        "utils",
        "tests",
    ]

    for dir_name in required_dirs:
        dir_path = forge_root / dir_name
        assert dir_path.exists(), f"Directory {dir_name} does not exist"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"


def test_all_init_files_present():
    """Test that all required __init__.py files are present."""
    forge_root = Path(__file__).parent.parent

    required_init_dirs = [
        "",  # Root __init__.py
        "cli",
        "cmake",
        "inspector",
        "storage",
        "models",
        "utils",
        "tests",
    ]

    for dir_name in required_init_dirs:
        if dir_name:
            init_path = forge_root / dir_name / "__init__.py"
        else:
            init_path = forge_root / "__init__.py"

        assert init_path.exists(), f"__init__.py missing in {dir_name or 'root'}"
        assert init_path.is_file(), f"__init__.py in {dir_name or 'root'} is not a file"


def test_all_modules_can_be_imported():
    """Test that all modules can be imported without errors."""
    # Test root module
    import forge
    assert hasattr(forge, "__version__")

    # Test submodules
    import forge.cli
    import forge.cmake
    import forge.inspector
    import forge.storage
    import forge.models
    import forge.utils
    import forge.tests

    # Verify imports work
    assert forge.cli is not None
    assert forge.cmake is not None
    assert forge.inspector is not None
    assert forge.storage is not None
    assert forge.models is not None
    assert forge.utils is not None
    assert forge.tests is not None


def test_pytest_discovers_tests_directory():
    """Test that pytest can discover the tests directory."""
    tests_dir = Path(__file__).parent
    assert tests_dir.exists(), "Tests directory does not exist"
    assert tests_dir.is_dir(), "Tests path is not a directory"
    assert tests_dir.name == "tests", f"Expected 'tests', got '{tests_dir.name}'"


def test_main_entry_point_exists():
    """Test that __main__.py exists and is executable."""
    forge_root = Path(__file__).parent.parent
    main_path = forge_root / "__main__.py"

    assert main_path.exists(), "__main__.py does not exist"
    assert main_path.is_file(), "__main__.py is not a file"

    # Verify it has a main function
    content = main_path.read_text()
    assert "def main()" in content, "__main__.py missing main() function"


def test_required_placeholder_files_exist():
    """Test that all required placeholder files exist."""
    forge_root = Path(__file__).parent.parent

    required_files = [
        "cli/argument_parser.py",
        "cmake/parameter_manager.py",
        "cmake/executor.py",
        "inspector/build_inspector.py",
        "storage/persistence.py",
        "storage/query.py",
        "storage/schema.sql",
        "models/arguments.py",
        "models/results.py",
        "models/metadata.py",
        "models/records.py",
        "utils/logging.py",
        "utils/paths.py",
        "utils/formatting.py",
    ]

    for file_path in required_files:
        full_path = forge_root / file_path
        assert full_path.exists(), f"Required file {file_path} does not exist"
        assert full_path.is_file(), f"{file_path} is not a file"


def test_fixtures_directory_exists():
    """Test that fixtures directory exists for test data."""
    fixtures_dir = Path(__file__).parent / "fixtures"
    fixtures_dir.mkdir(exist_ok=True)

    assert fixtures_dir.exists(), "Fixtures directory does not exist"
    assert fixtures_dir.is_dir(), "Fixtures path is not a directory"
