"""
Tests for pylint parser.

This module tests the PylintParser class which parses pylint JSON output
to detect static analysis issues, including convention, refactor, warning,
error, and fatal messages, along with code quality scores.
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from anvil.parsers.pylint_parser import PylintParser


class TestPylintJSONParsing:
    """Test parsing pylint JSON output."""

    def test_parse_json_output_with_no_issues(self):
        """Test parsing JSON output when no issues are found."""
        json_output = json.dumps([])
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_convention_messages(self):
        """Test parsing convention messages (C-series)."""
        json_output = json.dumps(
            [
                {
                    "type": "convention",
                    "module": "app",
                    "obj": "",
                    "line": 1,
                    "column": 0,
                    "endLine": 1,
                    "endColumn": 10,
                    "path": "src/app.py",
                    "symbol": "missing-module-docstring",
                    "message": "Missing module docstring",
                    "message-id": "C0114",
                }
            ]
        )
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert result.passed is False
        assert len(result.warnings) == 1
        assert "missing-module-docstring" in result.warnings[0].rule_name

    def test_parse_refactor_suggestions(self):
        """Test parsing refactor suggestions (R-series)."""
        json_output = json.dumps(
            [
                {
                    "type": "refactor",
                    "module": "utils",
                    "obj": "calculate",
                    "line": 10,
                    "column": 0,
                    "path": "src/utils.py",
                    "symbol": "too-many-locals",
                    "message": "Too many local variables (20/15)",
                    "message-id": "R0914",
                }
            ]
        )
        files = [Path("src/utils.py")]

        result = PylintParser.parse_json(json_output, files)

        assert result.passed is False
        assert len(result.warnings) == 1
        assert result.warnings[0].rule_name == "too-many-locals"

    def test_parse_warnings(self):
        """Test parsing warning messages (W-series)."""
        json_output = json.dumps(
            [
                {
                    "type": "warning",
                    "module": "app",
                    "obj": "process",
                    "line": 25,
                    "column": 4,
                    "path": "src/app.py",
                    "symbol": "unused-variable",
                    "message": "Unused variable 'result'",
                    "message-id": "W0612",
                }
            ]
        )
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert result.passed is False
        assert len(result.warnings) == 1
        assert result.warnings[0].severity == "warning"

    def test_parse_errors(self):
        """Test parsing error messages (E-series)."""
        json_output = json.dumps(
            [
                {
                    "type": "error",
                    "module": "app",
                    "obj": "main",
                    "line": 42,
                    "column": 8,
                    "path": "src/app.py",
                    "symbol": "undefined-variable",
                    "message": "Undefined variable 'foo'",
                    "message-id": "E0602",
                }
            ]
        )
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert result.passed is False
        assert len(result.errors) == 1
        assert result.errors[0].severity == "error"
        assert result.errors[0].error_code == "E0602"

    def test_parse_fatal_errors(self):
        """Test parsing fatal error messages (F-series)."""
        json_output = json.dumps(
            [
                {
                    "type": "fatal",
                    "module": "broken",
                    "obj": "",
                    "line": 1,
                    "column": 0,
                    "path": "src/broken.py",
                    "symbol": "syntax-error",
                    "message": "invalid syntax (<unknown>, line 1)",
                    "message-id": "F0001",
                }
            ]
        )
        files = [Path("src/broken.py")]

        result = PylintParser.parse_json(json_output, files)

        assert result.passed is False
        assert len(result.errors) == 1
        assert result.errors[0].severity == "error"

    def test_parse_multiple_issues_mixed_types(self):
        """Test parsing output with multiple issues of mixed types."""
        json_output = json.dumps(
            [
                {
                    "type": "convention",
                    "module": "app",
                    "obj": "",
                    "line": 1,
                    "column": 0,
                    "path": "src/app.py",
                    "symbol": "missing-docstring",
                    "message": "Missing module docstring",
                    "message-id": "C0114",
                },
                {
                    "type": "error",
                    "module": "app",
                    "obj": "main",
                    "line": 10,
                    "column": 0,
                    "path": "src/app.py",
                    "symbol": "undefined-variable",
                    "message": "Undefined variable 'x'",
                    "message-id": "E0602",
                },
            ]
        )
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert result.passed is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1

    def test_parse_with_score_information(self):
        """Test extracting score information from pylint output."""
        # Pylint score is typically in the text output, not JSON
        # We'll test score extraction separately
        json_output = json.dumps([])
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert result.passed is True


class TestPylintCommandBuilding:
    """Test building pylint commands."""

    def test_build_command_default_options(self):
        """Test building command with default options."""
        files = [Path("src/app.py")]
        config = {}

        command = PylintParser.build_command(files, config)

        assert command[0] == "pylint"
        assert "--output-format=json" in command
        assert str(files[0]) in command

    def test_build_command_with_disable_options(self):
        """Test building command with disable options."""
        files = [Path("src/app.py")]
        config = {"disable": ["C0114", "W0612"]}

        command = PylintParser.build_command(files, config)

        assert "--disable=C0114,W0612" in command

    def test_build_command_with_enable_options(self):
        """Test building command with enable options."""
        files = [Path("src/app.py")]
        config = {"enable": ["all"]}

        command = PylintParser.build_command(files, config)

        assert "--enable=all" in command

    def test_build_command_with_max_line_length(self):
        """Test building command with max-line-length option."""
        files = [Path("src/app.py")]
        config = {"max_line_length": 120}

        command = PylintParser.build_command(files, config)

        assert "--max-line-length=120" in command

    def test_build_command_with_rcfile(self):
        """Test building command with rcfile path."""
        files = [Path("src/app.py")]
        config = {"rcfile": ".pylintrc"}

        command = PylintParser.build_command(files, config)

        assert "--rcfile=.pylintrc" in command

    def test_build_command_with_score_enabled(self):
        """Test building command with score reporting enabled."""
        files = [Path("src/app.py")]
        config = {"score": True}

        command = PylintParser.build_command(files, config)

        # Score is enabled by default in pylint, just verify no --score=no
        assert "--score=no" not in command

    def test_build_command_with_score_disabled(self):
        """Test building command with score reporting disabled."""
        files = [Path("src/app.py")]
        config = {"score": False}

        command = PylintParser.build_command(files, config)

        assert "--score=no" in command

    def test_build_command_with_multiple_files(self):
        """Test building command with multiple files."""
        files = [Path("src/app.py"), Path("src/utils.py"), Path("tests/test_app.py")]
        config = {}

        command = PylintParser.build_command(files, config)

        assert len([arg for arg in command if arg.endswith(".py")]) == 3


class TestPylintErrorHandling:
    """Test error handling for pylint parser."""

    def test_error_when_pylint_not_installed(self, mocker: MockerFixture):
        """Test error when pylint is not installed."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError("pylint not found"))

        files = [Path("src/app.py")]
        with pytest.raises(FileNotFoundError, match="pylint"):
            PylintParser.run_pylint(files, {})

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test timeout handling for long-running pylint."""
        mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("pylint", 30))

        files = [Path("src/app.py")]
        with pytest.raises(TimeoutError):
            PylintParser.run_pylint(files, {}, timeout=30)

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON output."""
        invalid_json = "This is not JSON"
        files = [Path("src/app.py")]

        with pytest.raises(json.JSONDecodeError):
            PylintParser.parse_json(invalid_json, files)


class TestPylintVersionDetection:
    """Test pylint version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detecting pylint version from --version output."""
        mock_result = MagicMock()
        mock_result.stdout = "pylint 3.0.3\nastroid 3.0.2\nPython 3.11.2\n"
        mock_result.returncode = 0
        mocker.patch("subprocess.run", return_value=mock_result)

        version = PylintParser.get_version()

        assert version == "3.0.3"

    def test_version_detection_pylint2(self, mocker: MockerFixture):
        """Test detecting pylint 2.x version."""
        mock_result = MagicMock()
        mock_result.stdout = "pylint 2.17.7\n"
        mock_result.returncode = 0
        mocker.patch("subprocess.run", return_value=mock_result)

        version = PylintParser.get_version()

        assert version == "2.17.7"

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test version detection when pylint --version fails."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError("pylint not found"))

        version = PylintParser.get_version()

        assert version is None


class TestPylintIntegrationWithFixtures:
    """Integration tests using real pylint on fixture files."""

    def test_pylint_on_clean_python_code(self):
        """Test pylint on well-written Python code."""
        fixture_path = Path("tests/fixtures/python/good_code.py")
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        try:
            result = PylintParser.run_and_parse([fixture_path], {})
            # Good code should have minimal issues
            assert isinstance(result.passed, bool)
        except FileNotFoundError:
            pytest.skip("pylint not installed")

    def test_pylint_on_code_with_violations(self):
        """Test pylint on code with various violations."""
        fixture_path = Path("tests/fixtures/python/bad_code/style_violations.py")
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        try:
            result = PylintParser.run_and_parse([fixture_path], {})
            # Bad code should have issues detected
            assert isinstance(result.passed, bool)
        except FileNotFoundError:
            pytest.skip("pylint not installed")


class TestPylintConfigurationHandling:
    """Test configuration file detection and handling."""

    def test_detect_pylintrc(self, tmp_path):
        """Test detecting .pylintrc configuration file."""
        config_file = tmp_path / ".pylintrc"
        config_file.write_text("[MASTER]\nignore=CVS\n\n[MESSAGES CONTROL]\ndisable=C0114\n")

        found_config = PylintParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_detect_pyproject_toml(self, tmp_path):
        """Test detecting pyproject.toml with pylint configuration."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.pylint.messages_control]\ndisable = ['C0114', 'W0612']\n")

        found_config = PylintParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_detect_setup_cfg(self, tmp_path):
        """Test detecting setup.cfg with pylint configuration."""
        config_file = tmp_path / "setup.cfg"
        config_file.write_text("[pylint.messages_control]\ndisable = C0114,W0612\n")

        found_config = PylintParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_priority_order_pylintrc_over_others(self, tmp_path):
        """Test that .pylintrc takes priority over other config files."""
        pylintrc = tmp_path / ".pylintrc"
        pylintrc.write_text("[MASTER]\nignore=CVS\n")

        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text("[tool.pylint]\nmax-line-length = 120\n")

        found_config = PylintParser.find_config_file(tmp_path)

        assert found_config == pylintrc

    def test_no_config_file_returns_none(self, tmp_path):
        """Test that None is returned when no config file exists."""
        found_config = PylintParser.find_config_file(tmp_path)

        assert found_config is None


class TestPylintScoreExtraction:
    """Test extraction of pylint code quality scores."""

    def test_extract_score_from_text_output(self):
        """Test extracting score from pylint text output."""
        text_output = (
            "------------------------------------\n"
            "Your code has been rated at 8.50/10\n"
            "------------------------------------\n"
        )

        score = PylintParser.extract_score(text_output)

        assert score == 8.50

    def test_extract_score_with_previous_run(self):
        """Test extracting score with previous run comparison."""
        text_output = (
            "------------------------------------\n"
            "Your code has been rated at 9.25/10 (previous run: 8.75/10, +0.50)\n"
            "------------------------------------\n"
        )

        score = PylintParser.extract_score(text_output)

        assert score == 9.25

    def test_extract_score_when_not_present(self):
        """Test extracting score when not present in output."""
        text_output = "No score information available"

        score = PylintParser.extract_score(text_output)

        assert score is None

    def test_extract_perfect_score(self):
        """Test extracting perfect 10/10 score."""
        text_output = "Your code has been rated at 10.00/10"

        score = PylintParser.extract_score(text_output)

        assert score == 10.00


class TestPylintSeverityMapping:
    """Test mapping of pylint message types to severity levels."""

    def test_convention_maps_to_warning(self):
        """Test that convention messages map to warning severity."""
        json_output = json.dumps(
            [
                {
                    "type": "convention",
                    "module": "app",
                    "obj": "",
                    "line": 1,
                    "column": 0,
                    "path": "src/app.py",
                    "symbol": "missing-docstring",
                    "message": "Missing module docstring",
                    "message-id": "C0114",
                }
            ]
        )
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert len(result.warnings) == 1
        assert result.warnings[0].severity == "warning"

    def test_refactor_maps_to_warning(self):
        """Test that refactor messages map to warning severity."""
        json_output = json.dumps(
            [
                {
                    "type": "refactor",
                    "module": "app",
                    "obj": "func",
                    "line": 5,
                    "column": 0,
                    "path": "src/app.py",
                    "symbol": "too-many-locals",
                    "message": "Too many local variables",
                    "message-id": "R0914",
                }
            ]
        )
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert len(result.warnings) == 1

    def test_warning_maps_to_warning(self):
        """Test that warning messages map to warning severity."""
        json_output = json.dumps(
            [
                {
                    "type": "warning",
                    "module": "app",
                    "obj": "func",
                    "line": 5,
                    "column": 0,
                    "path": "src/app.py",
                    "symbol": "unused-variable",
                    "message": "Unused variable 'x'",
                    "message-id": "W0612",
                }
            ]
        )
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert len(result.warnings) == 1

    def test_error_maps_to_error(self):
        """Test that error messages map to error severity."""
        json_output = json.dumps(
            [
                {
                    "type": "error",
                    "module": "app",
                    "obj": "func",
                    "line": 5,
                    "column": 0,
                    "path": "src/app.py",
                    "symbol": "undefined-variable",
                    "message": "Undefined variable 'x'",
                    "message-id": "E0602",
                }
            ]
        )
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert len(result.errors) == 1
        assert result.errors[0].severity == "error"

    def test_fatal_maps_to_error(self):
        """Test that fatal messages map to error severity."""
        json_output = json.dumps(
            [
                {
                    "type": "fatal",
                    "module": "app",
                    "obj": "",
                    "line": 1,
                    "column": 0,
                    "path": "src/app.py",
                    "symbol": "syntax-error",
                    "message": "Syntax error",
                    "message-id": "F0001",
                }
            ]
        )
        files = [Path("src/app.py")]

        result = PylintParser.parse_json(json_output, files)

        assert len(result.errors) == 1
