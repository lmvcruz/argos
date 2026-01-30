"""
Tests for flake8 parser.

This module tests the flake8 output parser that converts flake8 JSON/text output
into ValidationResult objects for the Anvil quality gate system.
"""

import json
import subprocess
from pathlib import Path

import pytest
from helpers.parser_test_helpers import ParserTestHelpers
from pytest_mock import MockerFixture

from anvil.parsers import Flake8Parser


class TestFlake8JSONParsing:
    """Test parsing flake8 JSON output format."""

    def test_parse_json_output_with_no_errors(self):
        """Test parsing flake8 JSON output when no errors are found."""
        json_output = json.dumps({})

        result = Flake8Parser.parse_json(json_output, [Path("test.py")])

        helpers = ParserTestHelpers()
        helpers.assert_validation_result_structure(result)
        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_json_output_with_e_series_errors(self):
        """Test parsing PEP 8 E-series errors from flake8 JSON output."""
        json_output = json.dumps(
            {
                "test.py": [
                    {
                        "code": "E501",
                        "filename": "test.py",
                        "line_number": 10,
                        "column_number": 80,
                        "text": "line too long (95 > 79 characters)",
                        "physical_line": "    # This is a very long comment...",
                    }
                ]
            }
        )

        result = Flake8Parser.parse_json(json_output, [Path("test.py")])

        assert result.passed is False
        assert len(result.errors) == 1
        assert result.errors[0].severity == "error"
        assert result.errors[0].rule_name == "E501"
        assert "line too long" in result.errors[0].message

    def test_parse_json_output_with_w_series_warnings(self):
        """Test parsing W-series warnings from flake8 JSON output."""
        json_output = json.dumps(
            {
                "test.py": [
                    {
                        "code": "W503",
                        "filename": "test.py",
                        "line_number": 15,
                        "column_number": 1,
                        "text": "line break before binary operator",
                        "physical_line": "    and condition",
                    }
                ]
            }
        )

        result = Flake8Parser.parse_json(json_output, [Path("test.py")])

        assert result.passed is False
        assert len(result.warnings) == 1
        assert result.warnings[0].severity == "warning"
        assert result.warnings[0].rule_name == "W503"

    def test_parse_json_output_with_f_series_errors(self):
        """Test parsing PyFlakes F-series errors from flake8 JSON output."""
        json_output = json.dumps(
            {
                "test.py": [
                    {
                        "code": "F401",
                        "filename": "test.py",
                        "line_number": 5,
                        "column_number": 1,
                        "text": "'sys' imported but unused",
                        "physical_line": "import sys",
                    }
                ]
            }
        )

        result = Flake8Parser.parse_json(json_output, [Path("test.py")])

        assert result.passed is False
        assert len(result.errors) == 1
        assert result.errors[0].rule_name == "F401"
        assert "imported but unused" in result.errors[0].message

    def test_parse_json_output_with_c_series_complexity_warnings(self):
        """Test parsing C-series complexity warnings from flake8 JSON output."""
        json_output = json.dumps(
            {
                "test.py": [
                    {
                        "code": "C901",
                        "filename": "test.py",
                        "line_number": 20,
                        "column_number": 1,
                        "text": "'complex_function' is too complex (15)",
                        "physical_line": "def complex_function():",
                    }
                ]
            }
        )

        result = Flake8Parser.parse_json(json_output, [Path("test.py")])

        assert result.passed is False
        assert len(result.warnings) == 1
        assert result.warnings[0].rule_name == "C901"
        assert "too complex" in result.warnings[0].message

    def test_parse_multiple_files_with_mixed_results(self):
        """Test parsing flake8 output with errors in multiple files."""
        json_output = json.dumps(
            {
                "file1.py": [
                    {
                        "code": "E501",
                        "filename": "file1.py",
                        "line_number": 10,
                        "column_number": 80,
                        "text": "line too long",
                        "physical_line": "# long line",
                    }
                ],
                "file2.py": [
                    {
                        "code": "F401",
                        "filename": "file2.py",
                        "line_number": 5,
                        "column_number": 1,
                        "text": "'os' imported but unused",
                        "physical_line": "import os",
                    }
                ],
            }
        )

        files = [Path("file1.py"), Path("file2.py")]
        result = Flake8Parser.parse_json(json_output, files)

        assert result.passed is False
        assert len(result.errors) == 2
        file_paths = [issue.file_path for issue in result.errors]
        assert Path("file1.py") in file_paths
        assert Path("file2.py") in file_paths


class TestFlake8CommandBuilding:
    """Test building flake8 command with various options."""

    def test_build_command_with_default_options(self):
        """Test building basic flake8 command."""
        cmd = Flake8Parser.build_command([Path("test.py")], {})

        assert "python" in cmd
        assert "-m" in cmd
        assert "flake8" in cmd
        assert "test.py" in cmd

    def test_build_command_with_ignore_list(self):
        """Test building flake8 command with ignore list."""
        config = {"ignore": ["E501", "W503"]}
        cmd = Flake8Parser.build_command([Path("test.py")], config)

        assert "--ignore=E501,W503" in " ".join(cmd)

    def test_build_command_with_max_line_length(self):
        """Test building flake8 command with custom line length."""
        config = {"max_line_length": 100}
        cmd = Flake8Parser.build_command([Path("test.py")], config)

        assert "--max-line-length=100" in " ".join(cmd)

    def test_build_command_with_select_rules(self):
        """Test building flake8 command with select option."""
        config = {"select": ["E", "W", "F"]}
        cmd = Flake8Parser.build_command([Path("test.py")], config)

        assert "--select=E,W,F" in " ".join(cmd)

    def test_build_command_with_exclude_patterns(self):
        """Test building flake8 command with exclude patterns."""
        config = {"exclude": ["*.pyc", "__pycache__"]}
        cmd = Flake8Parser.build_command([Path("test.py")], config)

        assert "--exclude" in " ".join(cmd)

    def test_build_command_with_max_complexity(self):
        """Test building flake8 command with max complexity threshold."""
        config = {"max_complexity": 10}
        cmd = Flake8Parser.build_command([Path("test.py")], config)

        assert "--max-complexity=10" in " ".join(cmd)


class TestFlake8TextFormatParsing:
    """Test parsing flake8 legacy text format output (fallback)."""

    def test_parse_text_format_with_errors(self):
        """Test parsing flake8 text output format."""
        text_output = """test.py:10:80: E501 line too long (95 > 79 characters)
test.py:15:1: F401 'sys' imported but unused"""

        result = Flake8Parser.parse_text(text_output, [Path("test.py")])

        assert result.passed is False
        assert len(result.errors) == 2

    def test_parse_text_format_with_no_output(self):
        """Test parsing empty text output (no errors)."""
        text_output = ""

        result = Flake8Parser.parse_text(text_output, [Path("test.py")])

        assert result.passed is True
        assert len(result.errors) == 0


class TestFlake8ErrorHandling:
    """Test error handling for flake8 parser."""

    def test_error_when_flake8_not_installed(self, mocker: MockerFixture):
        """Test handling when flake8 is not installed."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError())

        with pytest.raises(FileNotFoundError, match="flake8 not found"):
            Flake8Parser.run_flake8([Path("test.py")], {})

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test handling of flake8 timeout."""
        mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("flake8", 30))

        with pytest.raises(TimeoutError):
            Flake8Parser.run_flake8([Path("test.py")], {"timeout": 30})

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON output."""
        invalid_json = "This is not JSON"

        with pytest.raises(json.JSONDecodeError):
            Flake8Parser.parse_json(invalid_json, [Path("test.py")])


class TestFlake8VersionDetection:
    """Test flake8 version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detecting flake8 version."""
        mock_result = mocker.Mock()
        mock_result.stdout = "7.0.0\n"
        mock_result.returncode = 0
        mocker.patch("subprocess.run", return_value=mock_result)

        version = Flake8Parser.get_version()
        assert version == "7.0.0"

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test handling when version detection fails."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError())

        version = Flake8Parser.get_version()
        assert version is None


class TestFlake8IntegrationWithFixtures:
    """Integration tests with real flake8 on fixture files."""

    def test_flake8_on_good_python_code(self):
        """Test running real flake8 on clean Python code."""
        helpers = ParserTestHelpers()
        fixture_path = helpers.get_fixture_path("python/good_code.py")

        result = Flake8Parser.run_and_parse([fixture_path], {})

        assert result.passed is True
        assert len(result.errors) == 0

    def test_flake8_on_style_violations_fixture(self):
        """Test running real flake8 on code with style violations."""
        helpers = ParserTestHelpers()
        fixture_path = helpers.get_fixture_path("python/bad_code/style_violations.py")

        result = Flake8Parser.run_and_parse([fixture_path], {})

        assert result.passed is False
        assert len(result.errors) > 0 or len(result.warnings) > 0

    def test_flake8_on_syntax_error_fixture(self):
        """Test running real flake8 on code with syntax errors."""
        helpers = ParserTestHelpers()
        fixture_path = helpers.get_fixture_path("python/bad_code/syntax_error.py")

        result = Flake8Parser.run_and_parse([fixture_path], {})

        assert result.passed is False
        # Find E999 syntax error
        syntax_errors = [e for e in result.errors if e.rule_name == "E999"]
        assert len(syntax_errors) > 0

    def test_flake8_on_unused_imports_fixture(self):
        """Test running real flake8 on code with unused imports."""
        helpers = ParserTestHelpers()
        fixture_path = helpers.get_fixture_path("python/bad_code/unused_code.py")

        result = Flake8Parser.run_and_parse([fixture_path], {})

        assert result.passed is False
        # Find F401 unused import errors
        unused_errors = [e for e in result.errors if e.rule_name == "F401"]
        assert len(unused_errors) > 0


class TestFlake8SeverityMapping:
    """Test severity mapping from flake8 codes to Anvil severities."""

    def test_e_series_maps_to_error(self):
        """Test that E-series codes map to 'error' severity."""
        assert Flake8Parser.map_severity("E501") == "error"
        assert Flake8Parser.map_severity("E999") == "error"

    def test_w_series_maps_to_warning(self):
        """Test that W-series codes map to 'warning' severity."""
        assert Flake8Parser.map_severity("W503") == "warning"
        assert Flake8Parser.map_severity("W605") == "warning"

    def test_f_series_maps_to_error(self):
        """Test that F-series (PyFlakes) codes map to 'error' severity."""
        assert Flake8Parser.map_severity("F401") == "error"
        assert Flake8Parser.map_severity("F821") == "error"

    def test_c_series_maps_to_warning(self):
        """Test that C-series (complexity) codes map to 'warning' severity."""
        assert Flake8Parser.map_severity("C901") == "warning"

    def test_n_series_maps_to_warning(self):
        """Test that N-series (naming) codes map to 'warning' severity."""
        assert Flake8Parser.map_severity("N801") == "warning"


class TestFlake8ConfigurationHandling:
    """Test handling of flake8 configuration files."""

    def test_detect_flake8_config_file(self, tmp_path: Path):
        """Test detection of .flake8 config file."""
        config_file = tmp_path / ".flake8"
        config_file.write_text("[flake8]\nmax-line-length = 100\n")

        found = Flake8Parser.find_config_file(tmp_path)
        assert found == config_file

    def test_detect_setup_cfg_flake8_section(self, tmp_path: Path):
        """Test detection of flake8 section in setup.cfg."""
        config_file = tmp_path / "setup.cfg"
        config_file.write_text("[flake8]\nmax-line-length = 100\n")

        found = Flake8Parser.find_config_file(tmp_path)
        assert found == config_file

    def test_detect_tox_ini_flake8_section(self, tmp_path: Path):
        """Test detection of flake8 section in tox.ini."""
        config_file = tmp_path / "tox.ini"
        config_file.write_text("[flake8]\nmax-line-length = 100\n")

        found = Flake8Parser.find_config_file(tmp_path)
        assert found == config_file
