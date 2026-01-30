"""
Tests for parser test framework infrastructure.

This module tests the fixture-based testing framework that all parser tests
will use. It validates helper functions, fixture loading, and directory structure.
"""

from pathlib import Path

import pytest

from anvil.models.validator import Issue, ValidationResult


class TestFixtureDirectoryStructure:
    """Test fixture directory structure and organization."""

    def test_fixtures_directory_exists(self):
        """Test that fixtures directory exists in tests folder."""
        fixtures_dir = Path(__file__).parent / "fixtures"
        assert fixtures_dir.exists(), "fixtures/ directory must exist"
        assert fixtures_dir.is_dir(), "fixtures/ must be a directory"

    def test_python_fixtures_directory_exists(self):
        """Test that python fixtures subdirectory exists."""
        python_dir = Path(__file__).parent / "fixtures" / "python"
        assert python_dir.exists(), "fixtures/python/ directory must exist"
        assert python_dir.is_dir(), "fixtures/python/ must be a directory"

    def test_cpp_fixtures_directory_exists(self):
        """Test that cpp fixtures subdirectory exists."""
        cpp_dir = Path(__file__).parent / "fixtures" / "cpp"
        assert cpp_dir.exists(), "fixtures/cpp/ directory must exist"
        assert cpp_dir.is_dir(), "fixtures/cpp/ must be a directory"

    def test_sample_code_fixtures_directory_exists(self):
        """Test that sample_code fixtures subdirectory exists."""
        sample_dir = Path(__file__).parent / "fixtures" / "sample_code"
        assert sample_dir.exists(), "fixtures/sample_code/ directory must exist"
        assert sample_dir.is_dir(), "fixtures/sample_code/ must be a directory"


class TestFixtureLoading:
    """Test fixture file loading helper functions."""

    def test_load_fixture_file_returns_content(self, helpers):
        """Test that load_fixture loads file content correctly."""
        # We'll use a known fixture file (to be created)
        content = helpers.load_fixture("python/good_code.py")
        assert isinstance(content, str), "Loaded content must be string"
        assert len(content) > 0, "Loaded content must not be empty"

    def test_load_fixture_file_with_subdirectory(self, helpers):
        """Test loading fixture from subdirectory path."""
        content = helpers.load_fixture("python/bad_code/missing_imports.py")
        assert isinstance(content, str)
        assert len(content) > 0

    def test_load_fixture_file_preserves_encoding(self, helpers):
        """Test that fixture loading preserves UTF-8 encoding."""
        content = helpers.load_fixture("python/unicode_content.py")
        assert isinstance(content, str)
        # Should be able to contain Unicode characters
        assert "©" in content or "utf" in content.lower()

    def test_load_fixture_nonexistent_file_raises_error(self, helpers):
        """Test that loading nonexistent fixture raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            helpers.load_fixture("python/does_not_exist.py")

    def test_get_fixture_path_returns_absolute_path(self, helpers):
        """Test that get_fixture_path returns absolute Path object."""
        path = helpers.get_fixture_path("python/good_code.py")
        assert isinstance(path, Path), "Must return Path object"
        assert path.is_absolute(), "Must return absolute path"
        assert path.exists(), "Returned path must exist"

    def test_list_fixtures_in_directory(self, helpers):
        """Test listing all fixtures in a directory."""
        fixtures = helpers.list_fixtures("python")
        assert isinstance(fixtures, list), "Must return list"
        assert len(fixtures) > 0, "Must find at least one Python fixture"
        assert all(isinstance(f, Path) for f in fixtures)


class TestParserHelpers:
    """Test parser helper functions for running validators."""

    def test_create_validation_result_helper(self, helpers):
        """Test helper for creating ValidationResult objects."""
        result = helpers.create_validation_result(
            validator_name="test_validator",
            passed=True,
            errors=[],
            warnings=[],
            files_checked=1,
        )
        assert isinstance(result, ValidationResult)
        assert result.validator_name == "test_validator"
        assert result.passed is True
        assert result.files_checked == 1

    def test_create_issue_helper(self, helpers):
        """Test helper for creating Issue objects."""
        issue = helpers.create_issue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            message="Test error",
            severity="error",
            rule_name="TEST001",
        )
        assert isinstance(issue, Issue)
        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column_number == 5
        assert issue.message == "Test error"
        assert issue.severity == "error"
        assert issue.rule_name == "TEST001"

    def test_assert_validation_result_structure(self, helpers):
        """Test assertion helper for ValidationResult structure."""
        result = ValidationResult(
            validator_name="test",
            passed=True,
            errors=[],
            warnings=[],
            execution_time=1.0,
            files_checked=1,
        )
        # Should not raise assertion error
        helpers.assert_validation_result_structure(result)

    def test_assert_validation_result_invalid_structure_raises(self, helpers):
        """Test that invalid ValidationResult structure raises AssertionError."""
        # Create object with wrong type
        with pytest.raises((AssertionError, AttributeError)):
            helpers.assert_validation_result_structure("not a result")

    def test_assert_issue_structure(self, helpers):
        """Test assertion helper for Issue structure."""
        issue = Issue(
            file_path="test.py",
            line_number=1,
            message="Test",
            severity="error",
        )
        # Should not raise assertion error
        helpers.assert_issue_structure(issue)

    def test_count_issues_by_severity(self, helpers):
        """Test helper for counting issues by severity."""
        issues = [
            Issue(file_path="test.py", line_number=1, message="E1", severity="error"),
            Issue(file_path="test.py", line_number=2, message="E2", severity="error"),
            Issue(file_path="test.py", line_number=3, message="W1", severity="warning"),
        ]
        counts = helpers.count_issues_by_severity(issues)
        assert counts["error"] == 2
        assert counts["warning"] == 1
        assert counts.get("info", 0) == 0

    def test_filter_issues_by_file(self, helpers):
        """Test helper for filtering issues by file path."""
        issues = [
            Issue(file_path="test1.py", line_number=1, message="E1", severity="error"),
            Issue(file_path="test2.py", line_number=1, message="E2", severity="error"),
            Issue(file_path="test1.py", line_number=2, message="E3", severity="error"),
        ]
        filtered = helpers.filter_issues_by_file(issues, "test1.py")
        assert len(filtered) == 2
        assert all(i.file_path == "test1.py" for i in filtered)

    def test_filter_issues_by_severity(self, helpers):
        """Test helper for filtering issues by severity."""
        issues = [
            Issue(file_path="test.py", line_number=1, message="E1", severity="error"),
            Issue(file_path="test.py", line_number=2, message="W1", severity="warning"),
            Issue(file_path="test.py", line_number=3, message="E2", severity="error"),
        ]
        errors = helpers.filter_issues_by_severity(issues, "error")
        assert len(errors) == 2
        assert all(i.severity == "error" for i in errors)


class TestPythonFixtures:
    """Test Python code fixtures."""

    def test_good_python_code_fixture_exists(self, helpers):
        """Test that good Python code fixture exists."""
        content = helpers.load_fixture("python/good_code.py")
        assert "def" in content or "class" in content
        # Good code should be syntactically valid Python
        compile(content, "good_code.py", "exec")

    def test_bad_python_syntax_error_fixture_exists(self, helpers):
        """Test that Python syntax error fixture exists."""
        content = helpers.load_fixture("python/bad_code/syntax_error.py")
        assert len(content) > 0
        # Should contain syntax error
        with pytest.raises(SyntaxError):
            compile(content, "syntax_error.py", "exec")

    def test_bad_python_missing_imports_fixture_exists(self, helpers):
        """Test that Python missing imports fixture exists."""
        content = helpers.load_fixture("python/bad_code/missing_imports.py")
        assert len(content) > 0
        # Should be valid syntax but have logical issues
        compile(content, "missing_imports.py", "exec")

    def test_bad_python_unused_code_fixture_exists(self, helpers):
        """Test that Python unused code fixture exists."""
        content = helpers.load_fixture("python/bad_code/unused_code.py")
        assert len(content) > 0
        # Should compile but have unused imports/variables
        compile(content, "unused_code.py", "exec")

    def test_bad_python_style_violations_fixture_exists(self, helpers):
        """Test that Python style violations fixture exists."""
        content = helpers.load_fixture("python/bad_code/style_violations.py")
        assert len(content) > 0
        # Should compile but violate PEP 8
        compile(content, "style_violations.py", "exec")

    def test_bad_python_unformatted_code_fixture_exists(self, helpers):
        """Test that Python unformatted code fixture exists."""
        content = helpers.load_fixture("python/bad_code/unformatted.py")
        assert len(content) > 0
        # Should compile but need formatting
        compile(content, "unformatted.py", "exec")


class TestCppFixtures:
    """Test C++ code fixtures."""

    def test_good_cpp_code_fixture_exists(self, helpers):
        """Test that good C++ code fixture exists."""
        content = helpers.load_fixture("cpp/good_code.cpp")
        assert "#include" in content or "int main" in content
        assert len(content) > 0

    def test_good_cpp_header_fixture_exists(self, helpers):
        """Test that good C++ header fixture exists."""
        content = helpers.load_fixture("cpp/good_code.hpp")
        assert "#pragma once" in content or "#ifndef" in content
        assert len(content) > 0

    def test_bad_cpp_syntax_error_fixture_exists(self, helpers):
        """Test that C++ syntax error fixture exists."""
        content = helpers.load_fixture("cpp/bad_code/syntax_error.cpp")
        assert len(content) > 0
        # Should contain obvious syntax errors

    def test_bad_cpp_style_violations_fixture_exists(self, helpers):
        """Test that C++ style violations fixture exists."""
        content = helpers.load_fixture("cpp/bad_code/style_violations.cpp")
        assert len(content) > 0
        # Should have style issues

    def test_bad_cpp_static_analysis_issues_fixture_exists(self, helpers):
        """Test that C++ static analysis issues fixture exists."""
        content = helpers.load_fixture("cpp/bad_code/static_analysis_issues.cpp")
        assert len(content) > 0
        # Should have potential bugs


class TestFixtureNamingConventions:
    """Test fixture naming conventions documentation."""

    def test_readme_exists_in_fixtures_directory(self):
        """Test that README.md exists in fixtures directory."""
        readme = Path(__file__).parent / "fixtures" / "README.md"
        assert readme.exists(), "fixtures/README.md must exist to document conventions"

    def test_readme_documents_naming_conventions(self):
        """Test that README documents fixture naming conventions."""
        readme = Path(__file__).parent / "fixtures" / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "naming" in content.lower() or "convention" in content.lower()
        assert "good_code" in content or "bad_code" in content

    def test_readme_documents_directory_structure(self):
        """Test that README documents directory structure."""
        readme = Path(__file__).parent / "fixtures" / "README.md"
        content = readme.read_text(encoding="utf-8")
        assert "python" in content.lower() or "cpp" in content.lower()
        assert "structure" in content.lower() or "organization" in content.lower()


# Pytest fixtures for test helpers
@pytest.fixture
def helpers():
    """Provide parser test helpers."""
    from helpers.parser_test_helpers import ParserTestHelpers

    return ParserTestHelpers()
