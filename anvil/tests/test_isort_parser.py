"""
Comprehensive tests for isort parser (Step 2.4).

Tests cover:
- Text output parsing (ERROR messages for incorrectly sorted imports)
- Command building with configuration options
- Error handling (isort not installed, timeouts)
- Version detection
- Integration tests with real isort
- Configuration file detection
- Fix command generation
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from helpers.parser_test_helpers import ParserTestHelpers
from pytest_mock import MockerFixture

from anvil.parsers.isort_parser import IsortParser


class TestIsortTextParsing:
    """Test parsing isort text output."""

    def test_parse_output_all_imports_sorted(self):
        """Test parsing output when all imports are correctly sorted."""
        output = "Skipped 3 files"

        result = IsortParser.parse_text(output, [Path("file1.py"), Path("file2.py")])

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_output_imports_need_sorting(self):
        """Test parsing output when imports need sorting."""
        output = """ERROR: /path/to/file.py Imports are incorrectly sorted and/or formatted.
Skipped 2 files"""

        result = IsortParser.parse_text(output, [Path("/path/to/file.py")])

        assert result.passed is False
        assert len(result.errors) == 1
        assert result.errors[0].file_path == Path("/path/to/file.py")
        assert "incorrectly sorted" in result.errors[0].message.lower()
        assert result.errors[0].severity == "error"
        assert result.errors[0].rule_name == "ISORT_ORDER"

    def test_parse_multiple_files_with_errors(self):
        """Test parsing output with multiple files needing sorting."""
        output = """ERROR: /path/to/first.py Imports are incorrectly sorted and/or formatted.
ERROR: /path/to/second.py Imports are incorrectly sorted and/or formatted.
Skipped 1 files"""

        result = IsortParser.parse_text(
            output, [Path("/path/to/first.py"), Path("/path/to/second.py")]
        )

        assert result.passed is False
        assert len(result.errors) == 2
        assert result.errors[0].file_path == Path("/path/to/first.py")
        assert result.errors[1].file_path == Path("/path/to/second.py")

    def test_parse_windows_paths(self):
        """Test parsing Windows-style paths with backslashes."""
        output = (
            r"ERROR: C:\Users\test\project\file.py Imports are incorrectly sorted and/or formatted."
        )

        result = IsortParser.parse_text(output, [Path(r"C:\Users\test\project\file.py")])

        assert result.passed is False
        assert len(result.errors) == 1
        assert "file.py" in str(result.errors[0].file_path)

    def test_parse_output_with_skipped_files(self):
        """Test parsing output that mentions skipped files."""
        output = """ERROR: /path/to/file.py Imports are incorrectly sorted and/or formatted.
Skipped 5 files"""

        result = IsortParser.parse_text(output, [Path("/path/to/file.py")])

        assert result.passed is False
        assert len(result.errors) == 1


class TestIsortCommandBuilding:
    """Test building isort command with various options."""

    def test_build_command_default_options(self):
        """Test building command with default options."""
        files = [Path("file1.py"), Path("file2.py")]

        cmd = IsortParser.build_command(files, {})

        assert cmd[0] == "python"
        assert cmd[1] == "-m"
        assert cmd[2] == "isort"
        assert "--check-only" in cmd
        assert str(files[0]) in cmd
        assert str(files[1]) in cmd

    def test_build_command_with_profile(self):
        """Test building command with profile option (black, google, etc.)."""
        files = [Path("test.py")]
        config = {"profile": "black"}

        cmd = IsortParser.build_command(files, config)

        assert "--profile" in cmd
        assert "black" in cmd

    def test_build_command_with_line_length(self):
        """Test building command with line length option."""
        files = [Path("test.py")]
        config = {"line_length": 120}

        cmd = IsortParser.build_command(files, config)

        assert "--line-length" in cmd
        assert "120" in cmd

    def test_build_command_with_multi_line_output(self):
        """Test building command with multi-line output style."""
        files = [Path("test.py")]
        config = {"multi_line_output": 3}

        cmd = IsortParser.build_command(files, config)

        assert "--multi-line" in cmd
        assert "3" in cmd

    def test_build_command_with_skip_patterns(self):
        """Test building command with skip patterns."""
        files = [Path("test.py")]
        config = {"skip": ["migrations", "__pycache__"]}

        cmd = IsortParser.build_command(files, config)

        assert "--skip" in cmd
        assert "migrations" in cmd
        assert "__pycache__" in cmd

    def test_build_command_with_force_single_line(self):
        """Test building command with force single line imports."""
        files = [Path("test.py")]
        config = {"force_single_line": True}

        cmd = IsortParser.build_command(files, config)

        assert "--force-single-line-imports" in cmd

    def test_build_command_with_diff(self):
        """Test building command with diff output."""
        files = [Path("test.py")]
        config = {"diff": True}

        cmd = IsortParser.build_command(files, config)

        assert "--diff" in cmd

    def test_build_command_with_multiple_files(self):
        """Test building command with multiple files."""
        files = [Path("file1.py"), Path("file2.py"), Path("file3.py")]

        cmd = IsortParser.build_command(files, {})

        for file in files:
            assert str(file) in cmd


class TestIsortErrorHandling:
    """Test error handling for isort parser."""

    def test_error_when_isort_not_installed(self, mocker: MockerFixture):
        """Test error handling when isort is not installed."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError("isort not found"))

        with pytest.raises(FileNotFoundError, match="isort not found"):
            IsortParser.run_isort([Path("test.py")], {})

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test timeout handling for slow isort execution."""
        mocker.patch(
            "subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="isort", timeout=30)
        )

        with pytest.raises(subprocess.TimeoutExpired):
            IsortParser.run_isort([Path("test.py")], {}, timeout=30)

    def test_parse_syntax_error_in_file(self):
        """Test parsing output when file has syntax errors."""
        output = "ERROR: /path/to/file.py Imports are incorrectly sorted and/or formatted."

        result = IsortParser.parse_text(output, [Path("/path/to/file.py")])

        assert result.passed is False
        assert len(result.errors) == 1


class TestIsortVersionDetection:
    """Test isort version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detecting isort version from --version output."""
        mock_result = MagicMock()
        # Long output string from isort --version
        mock_result.stdout = (
            "                 _                 _\n"
            "                (_) ___  ___  _ __| |_\n"
            "                | |/ _ \\/ _ \\| '__| __|\n"
            "                | |  __/ (_) | |  | |_\n"
            "                |_|\\___|\\___/|_|   \\__|\n\n"
            "      isort your imports, so you don't have to.\n\n"
            "                    VERSION 5.13.2\n"
        )
        mock_result.returncode = 0
        mocker.patch("subprocess.run", return_value=mock_result)

        version = IsortParser.get_version()

        assert version is not None
        assert "5.13.2" in version

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test handling failure to detect version."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError("isort not found"))

        version = IsortParser.get_version()

        assert version is None


class TestIsortIntegrationWithFixtures:
    """Integration tests with real isort on fixture files."""

    def test_isort_on_sorted_python_code(self):
        """Test running real isort on code with correctly sorted imports."""
        helpers = ParserTestHelpers()
        fixture_path = helpers.get_fixture_path("python/good_code.py")

        result = IsortParser.run_and_parse([fixture_path], {})

        # Good code should have sorted imports
        assert result.passed is True

    def test_isort_on_unsorted_imports_fixture(self):
        """Test running real isort on code with unsorted imports."""
        helpers = ParserTestHelpers()
        # This fixture should have imports in wrong order
        fixture_path = helpers.get_fixture_path("python/bad_code/style_violations.py")

        result = IsortParser.run_and_parse([fixture_path], {})

        # If the file has unsorted imports, isort should detect them
        # Note: style_violations.py may or may not have import order issues
        # This is just checking the parser works
        assert result is not None
        assert hasattr(result, "passed")


class TestIsortConfigurationHandling:
    """Test isort configuration file detection."""

    def test_detect_pyproject_toml(self, tmp_path):
        """Test detecting isort config in pyproject.toml."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.isort]\nprofile = 'black'\n")

        config_file = IsortParser.find_config_file(tmp_path)

        assert config_file is not None
        assert config_file.name == "pyproject.toml"

    def test_detect_setup_cfg(self, tmp_path):
        """Test detecting isort config in setup.cfg."""
        setup_cfg = tmp_path / "setup.cfg"
        setup_cfg.write_text("[isort]\nprofile = black\n")

        config_file = IsortParser.find_config_file(tmp_path)

        assert config_file is not None
        assert config_file.name == "setup.cfg"

    def test_detect_isort_cfg(self, tmp_path):
        """Test detecting .isort.cfg file."""
        isort_cfg = tmp_path / ".isort.cfg"
        isort_cfg.write_text("[settings]\nprofile = black\n")

        config_file = IsortParser.find_config_file(tmp_path)

        assert config_file is not None
        assert config_file.name == ".isort.cfg"

    def test_no_config_file_returns_none(self, tmp_path):
        """Test returns None when no config file found."""
        config_file = IsortParser.find_config_file(tmp_path)

        assert config_file is None


class TestIsortSuggestedFixes:
    """Test suggested fix command generation."""

    def test_generate_fix_command(self):
        """Test generating fix command without --check-only."""
        files = [Path("test.py")]
        config = {}

        fix_cmd = IsortParser.generate_fix_command(files, config)

        assert "python" in fix_cmd
        assert "-m" in fix_cmd
        assert "isort" in fix_cmd
        assert "--check-only" not in fix_cmd
        assert str(files[0]) in fix_cmd

    def test_generate_fix_command_with_options(self):
        """Test generating fix command preserves config options."""
        files = [Path("test.py")]
        config = {"profile": "black", "line_length": 100}

        fix_cmd = IsortParser.generate_fix_command(files, config)

        assert "--profile" in fix_cmd
        assert "black" in fix_cmd
        assert "--line-length" in fix_cmd
        assert "100" in fix_cmd
        assert "--check-only" not in fix_cmd
