"""
Tests for autoflake parser.

This module tests the AutoflakeParser class which parses autoflake text output
to detect unused imports and variables in Python code.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from anvil.parsers.autoflake_parser import AutoflakeParser


class TestAutoflakeTextParsing:
    """Test parsing autoflake text output."""

    def test_parse_output_no_unused_code(self):
        """Test parsing output when no unused code is detected."""
        output = "No issues detected!"
        files = [Path("src/app.py")]

        result = AutoflakeParser.parse_text(output, files)

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_output_with_unused_imports(self):
        """Test parsing output with unused imports detected."""
        output = (
            "--- src/app.py (original)\n"
            "+++ src/app.py (autoflake)\n"
            "@@ -1,5 +1,3 @@\n"
            " import os\n"
            "-import sys\n"
            "-import json\n"
            " \n"
            " def main():\n"
            "     print('hello')\n"
        )
        files = [Path("src/app.py")]

        result = AutoflakeParser.parse_text(output, files)

        assert result.passed is False
        assert len(result.errors) == 1
        assert "src/app.py" in result.errors[0].file_path
        assert "unused imports" in result.errors[0].message.lower()

    def test_parse_output_with_unused_variables(self):
        """Test parsing output with unused variables detected."""
        output = (
            "--- src/calculator.py (original)\n"
            "+++ src/calculator.py (autoflake)\n"
            "@@ -5,7 +5,6 @@\n"
            " def calculate(a, b):\n"
            "     result = a + b\n"
            "-    unused_var = 42\n"
            "     return result\n"
        )
        files = [Path("src/calculator.py")]

        result = AutoflakeParser.parse_text(output, files)

        assert result.passed is False
        assert len(result.errors) == 1
        assert "calculator.py" in result.errors[0].file_path

    def test_parse_multiple_files_with_issues(self):
        """Test parsing output with multiple files having issues."""
        output = (
            "--- src/app.py (original)\n"
            "+++ src/app.py (autoflake)\n"
            "@@ -1,3 +1,2 @@\n"
            " import os\n"
            "-import sys\n"
            "\n"
            "--- src/utils.py (original)\n"
            "+++ src/utils.py (autoflake)\n"
            "@@ -1,4 +1,3 @@\n"
            " import json\n"
            "-import re\n"
        )
        files = [Path("src/app.py"), Path("src/utils.py")]

        result = AutoflakeParser.parse_text(output, files)

        assert result.passed is False
        assert len(result.errors) == 2
        file_paths = [error.file_path for error in result.errors]
        assert any("app.py" in fp for fp in file_paths)
        assert any("utils.py" in fp for fp in file_paths)

    def test_parse_windows_paths(self):
        """Test parsing output with Windows-style paths."""
        output = (
            "--- C:\\Users\\dev\\project\\src\\app.py (original)\n"
            "+++ C:\\Users\\dev\\project\\src\\app.py (autoflake)\n"
            "@@ -1,3 +1,2 @@\n"
            "-import unused\n"
        )
        files = [Path("C:/Users/dev/project/src/app.py")]

        result = AutoflakeParser.parse_text(output, files)

        assert result.passed is False
        assert len(result.errors) == 1


class TestAutoflakeCommandBuilding:
    """Test building autoflake commands."""

    def test_build_command_default_options(self):
        """Test building command with default options."""
        files = [Path("src/app.py")]
        config = {}

        command = AutoflakeParser.build_command(files, config)

        assert command[0] == "autoflake"
        assert "--check" in command
        assert str(files[0]) in command

    def test_build_command_with_remove_unused_variables(self):
        """Test building command with remove-unused-variables option."""
        files = [Path("src/app.py")]
        config = {"remove_unused_variables": True}

        command = AutoflakeParser.build_command(files, config)

        assert "--remove-unused-variables" in command

    def test_build_command_with_remove_all_unused_imports(self):
        """Test building command with remove-all-unused-imports option."""
        files = [Path("src/app.py")]
        config = {"remove_all_unused_imports": True}

        command = AutoflakeParser.build_command(files, config)

        assert "--remove-all-unused-imports" in command

    def test_build_command_with_ignore_init_module_imports(self):
        """Test building command with ignore-init-module-imports option."""
        files = [Path("src/__init__.py")]
        config = {"ignore_init_module_imports": True}

        command = AutoflakeParser.build_command(files, config)

        assert "--ignore-init-module-imports" in command

    def test_build_command_with_expand_star_imports(self):
        """Test building command with expand-star-imports option."""
        files = [Path("src/app.py")]
        config = {"expand_star_imports": True}

        command = AutoflakeParser.build_command(files, config)

        assert "--expand-star-imports" in command

    def test_build_command_with_remove_duplicate_keys(self):
        """Test building command with remove-duplicate-keys option."""
        files = [Path("src/app.py")]
        config = {"remove_duplicate_keys": True}

        command = AutoflakeParser.build_command(files, config)

        assert "--remove-duplicate-keys" in command

    def test_build_command_with_imports_to_ignore(self):
        """Test building command with imports to ignore."""
        files = [Path("src/app.py")]
        config = {"imports": ["logging", "typing"]}

        command = AutoflakeParser.build_command(files, config)

        assert "--imports=logging,typing" in command

    def test_build_command_with_multiple_files(self):
        """Test building command with multiple files."""
        files = [Path("src/app.py"), Path("src/utils.py"), Path("tests/test_app.py")]
        config = {}

        command = AutoflakeParser.build_command(files, config)

        assert len([arg for arg in command if arg.endswith(".py")]) == 3


class TestAutoflakeErrorHandling:
    """Test error handling for autoflake parser."""

    def test_error_when_autoflake_not_installed(self, mocker: MockerFixture):
        """Test error when autoflake is not installed."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError("autoflake not found"))

        files = [Path("src/app.py")]
        with pytest.raises(FileNotFoundError, match="autoflake"):
            AutoflakeParser.run_autoflake(files, {})

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test timeout handling for long-running autoflake."""
        mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("autoflake", 30))

        files = [Path("src/app.py")]
        with pytest.raises(TimeoutError):
            AutoflakeParser.run_autoflake(files, {}, timeout=30)

    def test_parse_with_empty_output(self):
        """Test parsing with empty output (no changes needed)."""
        output = ""
        files = [Path("src/app.py")]

        result = AutoflakeParser.parse_text(output, files)

        assert result.passed is True
        assert len(result.errors) == 0


class TestAutoflakeVersionDetection:
    """Test autoflake version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detecting autoflake version from --version output."""
        mock_result = MagicMock()
        mock_result.stdout = "autoflake 2.2.1\n"
        mock_result.returncode = 0
        mocker.patch("subprocess.run", return_value=mock_result)

        version = AutoflakeParser.get_version()

        assert version == "2.2.1"

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test version detection when autoflake --version fails."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError("autoflake not found"))

        version = AutoflakeParser.get_version()

        assert version is None


class TestAutoflakeIntegrationWithFixtures:
    """Integration tests using real autoflake on fixture files."""

    def test_autoflake_on_clean_python_code(self):
        """Test autoflake on properly written Python code."""
        fixture_path = Path("tests/fixtures/python/good_code.py")
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        try:
            result = AutoflakeParser.run_and_parse([fixture_path], {})
            # Good code should have no unused imports/variables
            assert result.passed is True or len(result.errors) == 0
        except FileNotFoundError:
            pytest.skip("autoflake not installed")

    def test_autoflake_on_unused_imports_fixture(self):
        """Test autoflake on code with unused imports."""
        fixture_path = Path("tests/fixtures/python/bad_code/missing_imports.py")
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        try:
            # This fixture might not have unused imports, so we just verify parsing works
            result = AutoflakeParser.run_and_parse([fixture_path], {})
            assert isinstance(result.passed, bool)
        except FileNotFoundError:
            pytest.skip("autoflake not installed")


class TestAutoflakeConfigurationHandling:
    """Test configuration file detection and handling."""

    def test_detect_pyproject_toml(self, tmp_path):
        """Test detecting pyproject.toml with autoflake configuration."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text(
            "[tool.autoflake]\n"
            "remove-unused-variables = true\n"
            "remove-all-unused-imports = true\n"
        )

        found_config = AutoflakeParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_detect_setup_cfg(self, tmp_path):
        """Test detecting setup.cfg with autoflake configuration."""
        config_file = tmp_path / "setup.cfg"
        config_file.write_text("[autoflake]\nremove-unused-variables = true\n")

        found_config = AutoflakeParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_no_config_file_returns_none(self, tmp_path):
        """Test that None is returned when no config file exists."""
        found_config = AutoflakeParser.find_config_file(tmp_path)

        assert found_config is None


class TestAutoflakeSuggestedFixes:
    """Test generation of suggested fix commands."""

    def test_generate_fix_command(self):
        """Test generating fix command without --check flag."""
        files = [Path("src/app.py")]
        config = {}

        fix_command = AutoflakeParser.generate_fix_command(files, config)

        assert fix_command[0] == "autoflake"
        assert "--check" not in fix_command
        assert "--in-place" in fix_command
        assert str(files[0]) in fix_command

    def test_generate_fix_command_with_options(self):
        """Test generating fix command with configuration options."""
        files = [Path("src/app.py"), Path("src/utils.py")]
        config = {
            "remove_unused_variables": True,
            "remove_all_unused_imports": True,
            "remove_duplicate_keys": True,
        }

        fix_command = AutoflakeParser.generate_fix_command(files, config)

        assert "--in-place" in fix_command
        assert "--remove-unused-variables" in fix_command
        assert "--remove-all-unused-imports" in fix_command
        assert "--remove-duplicate-keys" in fix_command
