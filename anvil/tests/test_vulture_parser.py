"""
Tests for vulture parser - detects dead/unused code with confidence scores.

This module tests the VultureParser class which parses vulture output to identify
unused functions, methods, classes, variables, imports, and properties with
confidence percentages for each finding.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from anvil.parsers.vulture_parser import VultureParser


class TestVultureUnusedCodeDetection:
    """Test parsing vulture output for various unused code types."""

    def test_parse_output_with_no_unused_code(self):
        """Test parsing vulture output with no unused code detected."""
        vulture_output = ""

        result = VultureParser.parse_text(vulture_output, [Path("src/app.py")], {})

        assert result.passed is True
        assert result.validator_name == "vulture"
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_unused_function_detection(self):
        """Test parsing unused function with confidence score."""
        vulture_output = "src/utils.py:15: unused function 'helper' (60% confidence)"

        result = VultureParser.parse_text(
            vulture_output, [Path("src/utils.py")], {"min_confidence": 50}
        )

        assert result.passed is False
        assert len(result.warnings) == 1
        issue = result.warnings[0]
        assert issue.file_path == "src/utils.py"
        assert issue.line_number == 15
        assert "unused function 'helper'" in issue.message
        assert "60% confidence" in issue.message
        assert issue.severity == "warning"

    def test_parse_unused_method_detection(self):
        """Test parsing unused method in a class."""
        vulture_output = "src/models.py:42: unused method 'get_data' (80% confidence)"

        result = VultureParser.parse_text(vulture_output, [Path("src/models.py")], {})

        assert result.passed is False
        assert len(result.warnings) == 1
        issue = result.warnings[0]
        assert issue.file_path == "src/models.py"
        assert issue.line_number == 42
        assert "unused method" in issue.message

    def test_parse_unused_class_detection(self):
        """Test parsing unused class."""
        vulture_output = "src/legacy.py:10: unused class 'OldHandler' (100% confidence)"

        result = VultureParser.parse_text(vulture_output, [Path("src/legacy.py")], {})

        assert result.passed is False
        assert len(result.warnings) == 1
        issue = result.warnings[0]
        assert "unused class" in issue.message
        assert "100% confidence" in issue.message

    def test_parse_unused_variable_detection(self):
        """Test parsing unused variable."""
        vulture_output = "src/config.py:5: unused variable 'DEBUG_MODE' (70% confidence)"

        result = VultureParser.parse_text(vulture_output, [Path("src/config.py")], {})

        assert result.passed is False
        assert len(result.warnings) == 1
        issue = result.warnings[0]
        assert "unused variable" in issue.message

    def test_parse_unused_import_detection(self):
        """Test parsing unused import."""
        vulture_output = "src/main.py:3: unused import 'os' (90% confidence)"

        result = VultureParser.parse_text(vulture_output, [Path("src/main.py")], {})

        assert result.passed is False
        assert len(result.warnings) == 1
        issue = result.warnings[0]
        assert "unused import" in issue.message

    def test_parse_unused_property_detection(self):
        """Test parsing unused property."""
        vulture_output = "src/model.py:25: unused property 'name' (60% confidence)"

        result = VultureParser.parse_text(vulture_output, [Path("src/model.py")], {})

        assert result.passed is False
        assert len(result.warnings) == 1
        issue = result.warnings[0]
        assert "unused property" in issue.message

    def test_parse_multiple_unused_items(self):
        """Test parsing multiple unused items from different files."""
        vulture_output = """src/utils.py:15: unused function 'helper' (60% confidence)
src/models.py:42: unused method 'get_data' (80% confidence)
src/legacy.py:10: unused class 'OldHandler' (100% confidence)
src/config.py:5: unused variable 'DEBUG_MODE' (70% confidence)"""

        result = VultureParser.parse_text(
            vulture_output,
            [Path("src/utils.py"), Path("src/models.py"), Path("src/legacy.py")],
            {},
        )

        assert result.passed is False
        assert len(result.warnings) == 4

    def test_filter_by_minimum_confidence_threshold(self):
        """Test filtering unused code by minimum confidence threshold."""
        vulture_output = """src/utils.py:15: unused function 'helper' (60% confidence)
src/models.py:42: unused method 'get_data' (80% confidence)
src/legacy.py:10: unused class 'OldHandler' (40% confidence)"""

        result = VultureParser.parse_text(
            vulture_output,
            [Path("src/utils.py"), Path("src/models.py"), Path("src/legacy.py")],
            {"min_confidence": 50},
        )

        assert result.passed is False
        assert len(result.warnings) == 2  # Only 60% and 80%, not 40%


class TestVultureCommandBuilding:
    """Test building vulture commands with various options."""

    def test_build_command_default_options(self):
        """Test building vulture command with default options."""
        files = [Path("src/app.py"), Path("src/utils.py")]
        config = {}

        cmd = VultureParser.build_command(files, config)

        assert cmd[0] == "vulture"
        assert str(Path("src/app.py")) in [str(p) for p in cmd]
        assert str(Path("src/utils.py")) in [str(p) for p in cmd]

    def test_build_command_with_min_confidence(self):
        """Test building command with minimum confidence threshold."""
        files = [Path("src/app.py")]
        config = {"min_confidence": 80}

        cmd = VultureParser.build_command(files, config)

        assert "--min-confidence" in cmd
        assert "80" in cmd

    def test_build_command_with_exclude_patterns(self):
        """Test building command with exclude patterns."""
        files = [Path("src/")]
        config = {"exclude": ["*/tests/*", "*/migrations/*"]}

        cmd = VultureParser.build_command(files, config)

        assert "--exclude" in cmd
        # Should have exclude patterns in command
        cmd_str = " ".join(cmd)
        assert "tests" in cmd_str or "migrations" in cmd_str

    def test_build_command_with_ignore_decorators(self):
        """Test building command with ignore-decorators option."""
        files = [Path("src/app.py")]
        config = {"ignore_decorators": ["@app.route", "@celery.task"]}

        cmd = VultureParser.build_command(files, config)

        assert "--ignore-decorators" in cmd
        cmd_str = " ".join(cmd)
        assert "app.route" in cmd_str or "celery.task" in cmd_str

    def test_build_command_with_ignore_names(self):
        """Test building command with ignore-names option."""
        files = [Path("src/app.py")]
        config = {"ignore_names": ["_*", "test_*"]}

        cmd = VultureParser.build_command(files, config)

        assert "--ignore-names" in cmd

    def test_build_command_with_make_whitelist(self):
        """Test building command with make-whitelist option."""
        files = [Path("src/app.py")]
        config = {"make_whitelist": True}

        cmd = VultureParser.build_command(files, config)

        assert "--make-whitelist" in cmd

    def test_build_command_with_sort_by_size(self):
        """Test building command with sort-by-size option."""
        files = [Path("src/app.py")]
        config = {"sort_by_size": True}

        cmd = VultureParser.build_command(files, config)

        assert "--sort-by-size" in cmd


class TestVultureErrorHandling:
    """Test error handling for vulture execution."""

    def test_error_when_vulture_not_installed(self, mocker: MockerFixture):
        """Test error handling when vulture is not installed."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = FileNotFoundError("vulture not found")

        files = [Path("src/app.py")]
        config = {}

        with pytest.raises(FileNotFoundError):
            VultureParser.run_vulture(files, config)

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test timeout handling for long-running vulture execution."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.TimeoutExpired("vulture", 30)

        files = [Path("src/app.py")]
        config = {}

        with pytest.raises(subprocess.TimeoutExpired):
            VultureParser.run_vulture(files, config, timeout=30)

    def test_parse_with_empty_output(self):
        """Test parsing empty output from vulture."""
        vulture_output = ""

        result = VultureParser.parse_text(vulture_output, [Path("src/app.py")], {})

        assert result.passed is True
        assert len(result.warnings) == 0


class TestVultureVersionDetection:
    """Test vulture version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detecting vulture version from --version output."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = MagicMock(stdout="vulture 2.7\n", stderr="", returncode=0)

        version = VultureParser.get_version()

        assert version == "2.7"

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test handling version detection failure."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = FileNotFoundError("vulture not found")

        version = VultureParser.get_version()

        assert version is None


class TestVultureIntegrationWithFixtures:
    """Integration tests with real vulture on fixture code."""

    @pytest.mark.skipif(
        not Path("vulture").exists() and not Path("/usr/bin/vulture").exists(),
        reason="vulture not installed",
    )
    def test_vulture_on_code_with_unused_items(self, tmp_path: Path):
        """Test real vulture execution on code with unused items."""
        # Create temporary Python file with unused code
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def used_function():
    return 42

def unused_function():
    return 0

x = used_function()
unused_variable = 100
""")

        result = VultureParser.run_and_parse([test_file], {"min_confidence": 60})

        # Should detect at least the unused function and variable
        assert len(result.warnings) >= 1

    @pytest.mark.skipif(
        not Path("vulture").exists() and not Path("/usr/bin/vulture").exists(),
        reason="vulture not installed",
    )
    def test_vulture_on_clean_code(self, tmp_path: Path):
        """Test real vulture execution on code with all items used."""
        test_file = tmp_path / "test.py"
        test_file.write_text("""
def add(a, b):
    return a + b

result = add(1, 2)
print(result)
""")

        result = VultureParser.run_and_parse([test_file], {})

        assert result.passed is True or len(result.warnings) == 0


class TestVultureStatistics:
    """Test statistics and grouping functions."""

    def test_group_unused_items_by_type(self):
        """Test grouping unused items by type (function, class, etc.)."""
        vulture_output = """src/utils.py:15: unused function 'helper' (60% confidence)
src/models.py:42: unused method 'get_data' (80% confidence)
src/legacy.py:10: unused class 'OldHandler' (100% confidence)
src/config.py:5: unused variable 'DEBUG_MODE' (70% confidence)
src/main.py:3: unused import 'os' (90% confidence)"""

        grouped = VultureParser.group_by_type(vulture_output)

        assert "function" in grouped
        assert "method" in grouped
        assert "class" in grouped
        assert "variable" in grouped
        assert "import" in grouped
        assert len(grouped["function"]) == 1
        assert len(grouped["class"]) == 1

    def test_calculate_total_unused_count(self):
        """Test calculating total count of unused items."""
        vulture_output = """src/utils.py:15: unused function 'helper' (60% confidence)
src/models.py:42: unused method 'get_data' (80% confidence)
src/legacy.py:10: unused class 'OldHandler' (100% confidence)"""

        count = VultureParser.count_unused_items(vulture_output)

        assert count == 3

    def test_extract_confidence_scores(self):
        """Test extracting confidence scores from output."""
        vulture_output = """src/utils.py:15: unused function 'helper' (60% confidence)
src/models.py:42: unused method 'get_data' (80% confidence)
src/legacy.py:10: unused class 'OldHandler' (100% confidence)"""

        scores = VultureParser.extract_confidence_scores(vulture_output)

        assert len(scores) == 3
        assert 60 in scores
        assert 80 in scores
        assert 100 in scores

    def test_calculate_average_confidence(self):
        """Test calculating average confidence score."""
        vulture_output = """src/utils.py:15: unused function 'helper' (60% confidence)
src/models.py:42: unused method 'get_data' (80% confidence)
src/legacy.py:10: unused class 'OldHandler' (100% confidence)"""

        avg = VultureParser.calculate_average_confidence(vulture_output)

        assert avg == 80.0  # (60 + 80 + 100) / 3


class TestVultureConfigurationHandling:
    """Test configuration file detection for vulture."""

    def test_detect_vulture_config_in_pyproject_toml(self, tmp_path: Path):
        """Test detecting vulture config in pyproject.toml."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("""
[tool.vulture]
min_confidence = 80
exclude = ["tests/", "migrations/"]
""")

        detected = VultureParser.find_config_file(tmp_path)

        assert detected == config_file

    def test_detect_vulture_config_in_setup_cfg(self, tmp_path: Path):
        """Test detecting vulture config in setup.cfg."""
        config_file = tmp_path / "setup.cfg"
        config_file.write_text("""
[vulture]
min_confidence = 80
""")

        detected = VultureParser.find_config_file(tmp_path)

        assert detected == config_file

    def test_no_config_file_returns_none(self, tmp_path: Path):
        """Test that no config file returns None."""
        detected = VultureParser.find_config_file(tmp_path)

        assert detected is None
