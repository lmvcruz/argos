"""
Tests for project name detection from CMakeLists.txt files.

This module tests the BuildInspector's ability to extract project names
from CMakeLists.txt files in various formats and edge cases.
"""

from pathlib import Path

from inspector.build_inspector import BuildInspector

# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "cmakelists"


class TestSimpleProjectDetection:
    """Test basic project name extraction."""

    def test_simple_project_call(self):
        """Test extraction from simple project(MyProject) call."""
        fixture = FIXTURES_DIR / "simple_project.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "MyProject"

    def test_project_with_language(self):
        """Test extraction from project(Name LANGUAGE) format."""
        fixture = FIXTURES_DIR / "project_with_language.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "WebServer"

    def test_project_with_version(self):
        """Test extraction from project(Name VERSION x.y.z) format."""
        fixture = FIXTURES_DIR / "project_with_version.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "DataProcessor"

    def test_project_with_languages_keyword(self):
        """Test extraction with LANGUAGES keyword."""
        fixture = FIXTURES_DIR / "project_with_languages.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "MixedApp"

    def test_project_with_all_options(self):
        """Test extraction from project with VERSION, DESCRIPTION, LANGUAGES."""
        fixture = FIXTURES_DIR / "project_with_all_options.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "CompleteProject"


class TestMultilineProjectDetection:
    """Test project name extraction from multiline project() calls."""

    def test_multiline_project_call(self):
        """Test extraction from multiline project() declaration."""
        fixture = FIXTURES_DIR / "multiline_project.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "MultilineProject"


class TestProjectWithComments:
    """Test project name extraction when comments are present."""

    def test_project_with_comments(self):
        """Test extraction when comments are in the file."""
        fixture = FIXTURES_DIR / "project_with_comments.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "CommentedProject"


class TestNestedProjects:
    """Test handling of nested project calls."""

    def test_nested_project_calls_use_outermost(self):
        """Test that outermost project name is extracted (first one found)."""
        fixture = FIXTURES_DIR / "nested_projects.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "OuterProject"


class TestProjectWithSpecialCharacters:
    """Test project name extraction with special characters."""

    def test_project_with_spaces_in_quotes(self):
        """Test extraction of project name with spaces (quoted)."""
        fixture = FIXTURES_DIR / "project_with_spaces.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "Project With Spaces"


class TestCaseInsensitivity:
    """Test case-insensitive project() command detection."""

    def test_lowercase_project_command(self):
        """Test that PROJECT, project, and PrOjEcT all work (CMake is case-insensitive)."""
        fixture = FIXTURES_DIR / "lowercase_project.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "LowercaseTest"


class TestErrorCases:
    """Test error handling for invalid or missing files."""

    def test_file_not_found(self):
        """Test handling when CMakeLists.txt doesn't exist."""
        nonexistent = FIXTURES_DIR / "nonexistent.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(nonexistent)

        assert name is None

    def test_no_project_call(self):
        """Test handling when CMakeLists.txt has no project() call."""
        fixture = FIXTURES_DIR / "no_project.txt"
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name is None

    def test_with_actual_cmakelists_filename(self):
        """Test detection using actual CMakeLists.txt filename (not .txt extension)."""
        # Create a temporary CMakeLists.txt for this test
        temp_dir = Path(__file__).parent / "fixtures" / "temp"
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / "CMakeLists.txt"

        try:
            temp_file.write_text("cmake_minimum_required(VERSION 3.10)\n" "project(TempProject)\n")

            inspector = BuildInspector()
            name = inspector.detect_project_name(temp_file)

            assert name == "TempProject"
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()
            if temp_dir.exists():
                temp_dir.rmdir()


class TestPathHandling:
    """Test various path input formats."""

    def test_with_string_path(self):
        """Test detection works with string path (not Path object)."""
        fixture = str(FIXTURES_DIR / "simple_project.txt")
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "MyProject"

    def test_with_path_object(self):
        """Test detection works with Path object."""
        fixture = Path(FIXTURES_DIR / "simple_project.txt")
        inspector = BuildInspector()

        name = inspector.detect_project_name(fixture)

        assert name == "MyProject"


class TestFileEncodingHandling:
    """Test handling of various file encodings and corrupted files."""

    def test_with_invalid_encoding(self):
        """Test handling of files with invalid UTF-8 encoding."""
        # Create a file with invalid UTF-8 bytes
        temp_dir = Path(__file__).parent / "fixtures" / "temp"
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / "invalid_encoding.txt"

        try:
            # Write some invalid UTF-8 bytes
            temp_file.write_bytes(b"\xff\xfe" + b"invalid utf-8 \x80\x81\x82")

            inspector = BuildInspector()
            name = inspector.detect_project_name(temp_file)

            # Should return None when file can't be read
            assert name is None
        finally:
            # Cleanup
            if temp_file.exists():
                temp_file.unlink()
            if temp_dir.exists():
                temp_dir.rmdir()
