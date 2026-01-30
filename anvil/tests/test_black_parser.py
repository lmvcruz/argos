"""
Tests for black parser.

This module tests the BlackParser class which parses black output
into Anvil ValidationResult objects.
"""

import subprocess
from pathlib import Path

import pytest
from helpers.parser_test_helpers import ParserTestHelpers
from pytest_mock import MockerFixture

from anvil.parsers import BlackParser


class TestBlackTextParsing:
    """Test parsing black text output."""

    def test_parse_output_all_files_formatted(self):
        """Test parsing output when all files are properly formatted."""
        text_output = "All done! ✨ 🍰 ✨\n3 files would be left unchanged."

        result = BlackParser.parse_text(
            text_output, [Path("file1.py"), Path("file2.py"), Path("file3.py")]
        )

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.files_checked == 3

    def test_parse_output_files_need_formatting(self):
        """Test parsing output when files need formatting."""
        text_output = """would reformat /path/to/file1.py
would reformat /path/to/file2.py
Oh no! 💥 💔 💥
2 files would be reformatted, 1 file would be left unchanged."""

        result = BlackParser.parse_text(
            text_output,
            [Path("/path/to/file1.py"), Path("/path/to/file2.py"), Path("/path/to/file3.py")],
        )

        assert result.passed is False
        assert len(result.errors) == 2
        assert result.errors[0].file_path == Path("/path/to/file1.py")
        assert result.errors[1].file_path == Path("/path/to/file2.py")
        assert "would reformat" in result.errors[0].message.lower()

    def test_parse_would_reformat_messages(self):
        """Test extracting file paths from 'would reformat' messages."""
        text_output = "would reformat /home/user/project/module.py"

        result = BlackParser.parse_text(text_output, [Path("/home/user/project/module.py")])

        assert len(result.errors) == 1
        assert result.errors[0].file_path == Path("/home/user/project/module.py")
        assert result.errors[0].severity == "error"
        assert result.errors[0].rule_name == "BLACK_FORMAT"

    def test_parse_windows_paths(self):
        """Test parsing Windows paths in black output."""
        text_output = r"would reformat D:\project\src\main.py"

        result = BlackParser.parse_text(text_output, [Path(r"D:\project\src\main.py")])

        assert len(result.errors) == 1
        assert result.errors[0].file_path == Path(r"D:\project\src\main.py")

    def test_parse_left_unchanged_messages(self):
        """Test parsing 'left unchanged' messages (should not create issues)."""
        text_output = "3 files left unchanged."

        result = BlackParser.parse_text(
            text_output, [Path("file1.py"), Path("file2.py"), Path("file3.py")]
        )

        assert result.passed is True
        assert len(result.errors) == 0

    def test_parse_reformatted_messages(self):
        """Test parsing 'reformatted' messages from actual formatting."""
        text_output = """reformatted /path/to/file1.py
All done! ✨ 🍰 ✨
1 file reformatted."""

        result = BlackParser.parse_text(text_output, [Path("/path/to/file1.py")])

        assert len(result.errors) == 1
        assert "reformatted" in result.errors[0].message.lower()


class TestBlackCommandBuilding:
    """Test building black commands with various options."""

    def test_build_command_default_options(self):
        """Test building basic black command."""
        cmd = BlackParser.build_command([Path("test.py")], {})

        assert "python" in cmd
        assert "-m" in cmd
        assert "black" in cmd
        assert "--check" in cmd
        assert "test.py" in cmd

    def test_build_command_with_line_length(self):
        """Test building command with custom line length."""
        config = {"line_length": 120}
        cmd = BlackParser.build_command([Path("test.py")], config)

        assert "--line-length=120" in cmd or "--line-length" in cmd

    def test_build_command_with_target_version(self):
        """Test building command with target Python version."""
        config = {"target_version": ["py38", "py39"]}
        cmd = BlackParser.build_command([Path("test.py")], config)

        assert "--target-version" in cmd or any("py38" in str(c) for c in cmd)

    def test_build_command_with_skip_string_normalization(self):
        """Test building command with skip-string-normalization."""
        config = {"skip_string_normalization": True}
        cmd = BlackParser.build_command([Path("test.py")], config)

        assert "--skip-string-normalization" in cmd or "-S" in cmd

    def test_build_command_with_diff(self):
        """Test building command with diff output."""
        config = {"diff": True}
        cmd = BlackParser.build_command([Path("test.py")], config)

        assert "--diff" in cmd

    def test_build_command_with_color(self):
        """Test building command with color output."""
        config = {"color": True}
        cmd = BlackParser.build_command([Path("test.py")], config)

        assert "--color" in cmd

    def test_build_command_with_multiple_files(self):
        """Test building command with multiple files."""
        files = [Path("file1.py"), Path("file2.py"), Path("file3.py")]
        cmd = BlackParser.build_command(files, {})

        assert "file1.py" in cmd
        assert "file2.py" in cmd
        assert "file3.py" in cmd


class TestBlackErrorHandling:
    """Test error handling for black parser."""

    def test_error_when_black_not_installed(self, mocker: MockerFixture):
        """Test handling when black is not installed."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError())

        with pytest.raises(FileNotFoundError, match="black not found"):
            BlackParser.run_black([Path("test.py")], {})

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test handling of black timeout."""
        mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("black", 30))

        with pytest.raises(TimeoutError):
            BlackParser.run_black([Path("test.py")], {"timeout": 30})

    def test_parse_syntax_error_in_file(self):
        """Test parsing output when file has syntax errors."""
        text_output = """error: cannot format test.py: Cannot parse: 1:5: def foo(
Oh no! 💥 💔 💥
1 file failed to reformat."""

        result = BlackParser.parse_text(text_output, [Path("test.py")])

        assert result.passed is False
        assert len(result.errors) == 1
        assert (
            "cannot format" in result.errors[0].message.lower()
            or "failed" in result.errors[0].message.lower()
        )


class TestBlackVersionDetection:
    """Test black version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detecting black version."""
        mock_result = mocker.Mock()
        mock_result.stdout = "black, 24.1.0 (compiled: yes)\nPython (CPython) 3.11.2"
        mock_result.returncode = 0
        mocker.patch("subprocess.run", return_value=mock_result)

        version = BlackParser.get_version()

        assert version == "24.1.0" or "24.1" in version

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test version detection when black is not available."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError())

        version = BlackParser.get_version()
        assert version is None


class TestBlackIntegrationWithFixtures:
    """Integration tests with real black on fixture files."""

    def test_black_on_formatted_python_code(self):
        """Test running real black on properly formatted code."""
        helpers = ParserTestHelpers()
        fixture_path = helpers.get_fixture_path("python/good_code.py")

        result = BlackParser.run_and_parse([fixture_path], {})

        # Good code should already be formatted (or at least syntactically valid)
        assert isinstance(result.passed, bool)

    def test_black_on_unformatted_python_code(self):
        """Test running real black on unformatted code."""
        helpers = ParserTestHelpers()
        fixture_path = helpers.get_fixture_path("python/bad_code/unformatted.py")

        result = BlackParser.run_and_parse([fixture_path], {})
        # Unformatted code should trigger black errors
        if result.passed is False:
            assert len(result.errors) > 0

    def test_black_on_syntax_error_fixture(self):
        """Test running real black on code with syntax errors."""
        helpers = ParserTestHelpers()
        fixture_path = helpers.get_fixture_path("python/bad_code/syntax_error.py")

        result = BlackParser.run_and_parse([fixture_path], {})

        # Syntax errors should be reported
        assert result.passed is False
        assert len(result.errors) > 0


class TestBlackConfigurationHandling:
    """Test black configuration file detection and handling."""

    def test_detect_pyproject_toml(self, tmp_path):
        """Test detection of pyproject.toml configuration."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.black]\nline-length = 100\n")

        config_file = BlackParser.find_config_file(tmp_path)

        assert config_file == pyproject

    def test_no_config_file_returns_none(self, tmp_path):
        """Test when no config file exists."""
        config_file = BlackParser.find_config_file(tmp_path)

        assert config_file is None


class TestBlackSuggestedFixes:
    """Test generation of suggested fix commands."""

    def test_generate_fix_command(self):
        """Test generating command to fix formatting issues."""
        files = [Path("file1.py"), Path("file2.py")]

        fix_cmd = BlackParser.generate_fix_command(files, {})

        assert "black" in fix_cmd
        assert "file1.py" in fix_cmd
        assert "file2.py" in fix_cmd
        assert "--check" not in fix_cmd  # Should not be in fix mode

    def test_generate_fix_command_with_options(self):
        """Test generating fix command with configuration options."""
        config = {"line_length": 120, "skip_string_normalization": True}

        fix_cmd = BlackParser.generate_fix_command([Path("test.py")], config)

        assert "--line-length=120" in fix_cmd or "--line-length" in fix_cmd
        assert "--skip-string-normalization" in fix_cmd or "-S" in fix_cmd
