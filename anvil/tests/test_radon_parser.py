"""
Tests for radon parser.

This module tests the RadonParser class which parses radon JSON output
to extract cyclomatic complexity metrics, maintainability index,
and raw code metrics (LOC, LLOC, comments).
"""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from anvil.parsers.radon_parser import RadonParser


class TestRadonCyclomaticComplexity:
    """Test parsing radon cyclomatic complexity (CC) output."""

    def test_parse_cc_output_with_no_functions(self):
        """Test parsing CC output when no functions are found."""
        json_output = json.dumps({})
        files = [Path("src/app.py")]

        result = RadonParser.parse_cc(json_output, files)

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_cc_output_with_low_complexity_functions(self):
        """Test parsing CC output with low complexity functions (A grade)."""
        json_output = json.dumps(
            {
                "src/app.py": [
                    {
                        "type": "function",
                        "name": "simple_func",
                        "lineno": 10,
                        "col_offset": 0,
                        "endline": 12,
                        "complexity": 1,
                        "rank": "A",
                    }
                ]
            }
        )
        files = [Path("src/app.py")]

        result = RadonParser.parse_cc(json_output, files)

        assert result.passed is True
        assert len(result.warnings) == 0

    def test_parse_cc_output_with_high_complexity_functions(self):
        """Test parsing CC output with high complexity functions."""
        json_output = json.dumps(
            {
                "src/utils.py": [
                    {
                        "type": "function",
                        "name": "complex_func",
                        "lineno": 25,
                        "col_offset": 0,
                        "endline": 100,
                        "complexity": 15,
                        "rank": "C",
                    }
                ]
            }
        )
        files = [Path("src/utils.py")]
        config = {"max_complexity": 10}

        result = RadonParser.parse_cc(json_output, files, config)

        assert result.passed is False
        assert len(result.warnings) == 1
        assert "complex_func" in result.warnings[0].message
        assert "15" in result.warnings[0].message

    def test_parse_cc_output_with_multiple_functions(self):
        """Test parsing CC output with multiple functions."""
        json_output = json.dumps(
            {
                "src/app.py": [
                    {
                        "type": "function",
                        "name": "func1",
                        "lineno": 10,
                        "col_offset": 0,
                        "complexity": 2,
                        "rank": "A",
                    },
                    {
                        "type": "function",
                        "name": "func2",
                        "lineno": 20,
                        "col_offset": 0,
                        "complexity": 12,
                        "rank": "C",
                    },
                ]
            }
        )
        files = [Path("src/app.py")]
        config = {"max_complexity": 10}

        result = RadonParser.parse_cc(json_output, files, config)

        assert result.passed is False
        assert len(result.warnings) == 1
        assert "func2" in result.warnings[0].message

    def test_parse_cc_output_with_methods(self):
        """Test parsing CC output with class methods."""
        json_output = json.dumps(
            {
                "src/models.py": [
                    {
                        "type": "method",
                        "name": "MyClass.process",
                        "lineno": 35,
                        "col_offset": 4,
                        "complexity": 8,
                        "rank": "B",
                    }
                ]
            }
        )
        files = [Path("src/models.py")]

        result = RadonParser.parse_cc(json_output, files)

        assert result.passed is True

    def test_parse_cc_output_with_closures(self):
        """Test parsing CC output with closures."""
        json_output = json.dumps(
            {
                "src/functional.py": [
                    {
                        "type": "function",
                        "name": "outer",
                        "lineno": 10,
                        "col_offset": 0,
                        "complexity": 3,
                        "rank": "A",
                        "closures": [
                            {
                                "type": "function",
                                "name": "inner",
                                "lineno": 12,
                                "col_offset": 4,
                                "complexity": 2,
                                "rank": "A",
                            }
                        ],
                    }
                ]
            }
        )
        files = [Path("src/functional.py")]

        result = RadonParser.parse_cc(json_output, files)

        assert result.passed is True

    def test_parse_cc_complexity_ranks(self):
        """Test parsing different complexity ranks (A-F)."""
        json_output = json.dumps(
            {
                "src/app.py": [
                    {"name": "rank_a", "lineno": 1, "complexity": 1, "rank": "A"},
                    {"name": "rank_b", "lineno": 10, "complexity": 6, "rank": "B"},
                    {"name": "rank_c", "lineno": 20, "complexity": 11, "rank": "C"},
                    {"name": "rank_d", "lineno": 30, "complexity": 21, "rank": "D"},
                    {"name": "rank_e", "lineno": 40, "complexity": 31, "rank": "E"},
                    {"name": "rank_f", "lineno": 50, "complexity": 41, "rank": "F"},
                ]
            }
        )
        files = [Path("src/app.py")]
        config = {"max_complexity": 100}  # Allow all for testing

        result = RadonParser.parse_cc(json_output, files, config)

        # All should be parsed without errors
        assert isinstance(result.passed, bool)


class TestRadonMaintainabilityIndex:
    """Test parsing radon maintainability index (MI) output."""

    def test_parse_mi_output_high_maintainability(self):
        """Test parsing MI output with high maintainability (A grade)."""
        json_output = json.dumps(
            {
                "src/app.py": {
                    "mi": 85.5,
                    "rank": "A",
                }
            }
        )
        files = [Path("src/app.py")]

        result = RadonParser.parse_mi(json_output, files)

        assert result.passed is True
        assert len(result.warnings) == 0

    def test_parse_mi_output_low_maintainability(self):
        """Test parsing MI output with low maintainability."""
        json_output = json.dumps(
            {
                "src/legacy.py": {
                    "mi": 45.2,
                    "rank": "C",
                }
            }
        )
        files = [Path("src/legacy.py")]
        config = {"min_maintainability": 50}

        result = RadonParser.parse_mi(json_output, files, config)

        assert result.passed is False
        assert len(result.warnings) == 1
        assert "45.2" in result.warnings[0].message

    def test_parse_mi_output_multiple_files(self):
        """Test parsing MI output with multiple files."""
        json_output = json.dumps(
            {
                "src/app.py": {"mi": 80.0, "rank": "A"},
                "src/utils.py": {"mi": 75.5, "rank": "A"},
                "src/legacy.py": {"mi": 40.0, "rank": "C"},
            }
        )
        files = [Path("src/app.py"), Path("src/utils.py"), Path("src/legacy.py")]
        config = {"min_maintainability": 50}

        result = RadonParser.parse_mi(json_output, files, config)

        assert result.passed is False
        assert len(result.warnings) == 1

    def test_parse_mi_ranks(self):
        """Test parsing different MI ranks (A-C)."""
        json_output = json.dumps(
            {
                "file_a.py": {"mi": 90.0, "rank": "A"},
                "file_b.py": {"mi": 75.0, "rank": "A"},
                "file_c.py": {"mi": 60.0, "rank": "B"},
                "file_d.py": {"mi": 40.0, "rank": "C"},
            }
        )
        files = [
            Path("file_a.py"),
            Path("file_b.py"),
            Path("file_c.py"),
            Path("file_d.py"),
        ]

        result = RadonParser.parse_mi(json_output, files)

        assert isinstance(result.passed, bool)


class TestRadonRawMetrics:
    """Test parsing radon raw metrics output."""

    def test_parse_raw_metrics(self):
        """Test parsing raw metrics (LOC, LLOC, comments)."""
        json_output = json.dumps(
            {
                "src/app.py": {
                    "loc": 150,
                    "lloc": 100,
                    "sloc": 120,
                    "comments": 30,
                    "multi": 5,
                    "blank": 20,
                    "single_comments": 25,
                }
            }
        )
        files = [Path("src/app.py")]

        result = RadonParser.parse_raw(json_output, files)

        # Raw metrics are informational, should always pass
        assert result.passed is True
        assert len(result.errors) == 0

    def test_parse_raw_metrics_multiple_files(self):
        """Test parsing raw metrics for multiple files."""
        json_output = json.dumps(
            {
                "src/app.py": {"loc": 150, "lloc": 100, "comments": 30},
                "src/utils.py": {"loc": 80, "lloc": 60, "comments": 15},
            }
        )
        files = [Path("src/app.py"), Path("src/utils.py")]

        result = RadonParser.parse_raw(json_output, files)

        assert result.passed is True


class TestRadonCommandBuilding:
    """Test building radon commands."""

    def test_build_cc_command_default_options(self):
        """Test building CC command with default options."""
        files = [Path("src/app.py")]
        config = {}

        command = RadonParser.build_cc_command(files, config)

        assert command[0] == "radon"
        assert "cc" in command
        assert "--json" in command
        assert str(files[0]) in command

    def test_build_cc_command_with_min_grade(self):
        """Test building CC command with min grade threshold."""
        files = [Path("src/app.py")]
        config = {"min_grade": "B"}

        command = RadonParser.build_cc_command(files, config)

        assert "--min=B" in command

    def test_build_cc_command_with_show_closures(self):
        """Test building CC command with show-closures option."""
        files = [Path("src/app.py")]
        config = {"show_closures": True}

        command = RadonParser.build_cc_command(files, config)

        assert "--show-closures" in command

    def test_build_cc_command_with_exclude_patterns(self):
        """Test building CC command with exclude patterns."""
        files = [Path("src/app.py")]
        config = {"exclude": "test_*.py,*_test.py"}

        command = RadonParser.build_cc_command(files, config)

        assert "--exclude=test_*.py,*_test.py" in command

    def test_build_mi_command_default_options(self):
        """Test building MI command with default options."""
        files = [Path("src/app.py")]
        config = {}

        command = RadonParser.build_mi_command(files, config)

        assert command[0] == "radon"
        assert "mi" in command
        assert "--json" in command
        assert str(files[0]) in command

    def test_build_mi_command_with_show_details(self):
        """Test building MI command with show details option."""
        files = [Path("src/app.py")]
        config = {"show_details": True}

        command = RadonParser.build_mi_command(files, config)

        assert "--show" in command

    def test_build_raw_command_default_options(self):
        """Test building raw metrics command with default options."""
        files = [Path("src/app.py")]
        config = {}

        command = RadonParser.build_raw_command(files, config)

        assert command[0] == "radon"
        assert "raw" in command
        assert "--json" in command
        assert str(files[0]) in command

    def test_build_command_with_multiple_files(self):
        """Test building command with multiple files."""
        files = [Path("src/app.py"), Path("src/utils.py"), Path("tests/test_app.py")]
        config = {}

        command = RadonParser.build_cc_command(files, config)

        assert len([arg for arg in command if arg.endswith(".py")]) == 3


class TestRadonErrorHandling:
    """Test error handling for radon parser."""

    def test_error_when_radon_not_installed(self, mocker: MockerFixture):
        """Test error when radon is not installed."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError("radon not found"))

        files = [Path("src/app.py")]
        with pytest.raises(FileNotFoundError, match="radon"):
            RadonParser.run_radon_cc(files, {})

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test timeout handling for long-running radon."""
        mocker.patch("subprocess.run", side_effect=subprocess.TimeoutExpired("radon", 30))

        files = [Path("src/app.py")]
        with pytest.raises(TimeoutError):
            RadonParser.run_radon_cc(files, {}, timeout=30)

    def test_invalid_json_handling(self):
        """Test handling of invalid JSON output."""
        invalid_json = "This is not JSON"
        files = [Path("src/app.py")]

        with pytest.raises(json.JSONDecodeError):
            RadonParser.parse_cc(invalid_json, files)


class TestRadonVersionDetection:
    """Test radon version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detecting radon version from --version output."""
        mock_result = MagicMock()
        mock_result.stdout = "radon 5.1.0\n"
        mock_result.returncode = 0
        mocker.patch("subprocess.run", return_value=mock_result)

        version = RadonParser.get_version()

        assert version == "5.1.0"

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test version detection when radon --version fails."""
        mocker.patch("subprocess.run", side_effect=FileNotFoundError("radon not found"))

        version = RadonParser.get_version()

        assert version is None


class TestRadonIntegrationWithFixtures:
    """Integration tests using real radon on fixture files."""

    def test_radon_cc_on_simple_python_code(self):
        """Test radon CC on simple Python code."""
        fixture_path = Path("tests/fixtures/python/good_code.py")
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        try:
            result = RadonParser.run_and_parse_cc([fixture_path], {})
            assert isinstance(result.passed, bool)
        except FileNotFoundError:
            pytest.skip("radon not installed")

    def test_radon_mi_on_python_code(self):
        """Test radon MI on Python code."""
        fixture_path = Path("tests/fixtures/python/good_code.py")
        if not fixture_path.exists():
            pytest.skip("Fixture file not found")

        try:
            result = RadonParser.run_and_parse_mi([fixture_path], {})
            assert isinstance(result.passed, bool)
        except FileNotFoundError:
            pytest.skip("radon not installed")


class TestRadonComplexityAggregation:
    """Test complexity aggregation and statistics."""

    def test_calculate_average_complexity(self):
        """Test calculating average complexity across functions."""
        json_output = json.dumps(
            {
                "src/app.py": [
                    {"name": "func1", "lineno": 1, "complexity": 2, "rank": "A"},
                    {"name": "func2", "lineno": 10, "complexity": 4, "rank": "A"},
                    {"name": "func3", "lineno": 20, "complexity": 6, "rank": "B"},
                ]
            }
        )

        avg_complexity = RadonParser.calculate_average_complexity(json_output)

        assert avg_complexity == 4.0

    def test_calculate_average_complexity_with_empty_data(self):
        """Test calculating average complexity with no functions."""
        json_output = json.dumps({})

        avg_complexity = RadonParser.calculate_average_complexity(json_output)

        assert avg_complexity == 0.0

    def test_identify_high_complexity_functions(self):
        """Test identifying functions above complexity threshold."""
        json_output = json.dumps(
            {
                "src/app.py": [
                    {"name": "simple", "lineno": 1, "complexity": 2, "rank": "A"},
                    {"name": "complex", "lineno": 10, "complexity": 15, "rank": "C"},
                    {"name": "verycomplex", "lineno": 20, "complexity": 25, "rank": "D"},
                ]
            }
        )
        threshold = 10

        high_complexity = RadonParser.identify_high_complexity_functions(json_output, threshold)

        assert len(high_complexity) == 2
        assert "complex" in [f["name"] for f in high_complexity]
        assert "verycomplex" in [f["name"] for f in high_complexity]


class TestRadonConfigurationHandling:
    """Test configuration file detection and handling."""

    def test_detect_radon_config_in_pyproject_toml(self, tmp_path):
        """Test detecting radon configuration in pyproject.toml."""
        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.radon]\nmax_complexity = 10\nmin_maintainability = 50\n")

        found_config = RadonParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_detect_radon_config_in_setup_cfg(self, tmp_path):
        """Test detecting radon configuration in setup.cfg."""
        config_file = tmp_path / "setup.cfg"
        config_file.write_text("[radon]\nmax_complexity = 10\n")

        found_config = RadonParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_no_config_file_returns_none(self, tmp_path):
        """Test that None is returned when no config file exists."""
        found_config = RadonParser.find_config_file(tmp_path)

        assert found_config is None


class TestRadonEdgeCasesAndClosures:
    """Test edge cases and closure handling for better coverage."""

    def test_parse_cc_with_closures(self):
        """Test parsing cyclomatic complexity with nested closures."""
        json_output = json.dumps(
            {
                "src/nested.py": [
                    {
                        "type": "function",
                        "name": "outer_func",
                        "lineno": 10,
                        "complexity": 3,
                        "rank": "A",
                        "closures": [
                            {
                                "type": "function",
                                "name": "inner_func",
                                "lineno": 12,
                                "complexity": 12,
                                "rank": "C",
                            }
                        ],
                    }
                ]
            }
        )
        files = [Path("src/nested.py")]
        config = {"max_complexity": 10}

        result = RadonParser.parse_cc(json_output, files, config)

        # Should detect high complexity in closure
        assert result.passed is False
        assert len(result.warnings) == 1
        assert "inner_func" in result.warnings[0].message
        assert "12" in result.warnings[0].message
        assert "Closure" in result.warnings[0].message

    def test_parse_cc_with_multiple_closures(self):
        """Test parsing with multiple closures at different complexity levels."""
        json_output = json.dumps(
            {
                "src/multi.py": [
                    {
                        "type": "function",
                        "name": "parent",
                        "lineno": 5,
                        "complexity": 2,
                        "rank": "A",
                        "closures": [
                            {
                                "name": "closure1",
                                "lineno": 8,
                                "complexity": 15,
                                "rank": "C",
                            },
                            {
                                "name": "closure2",
                                "lineno": 12,
                                "complexity": 20,
                                "rank": "D",
                            },
                        ],
                    }
                ]
            }
        )
        files = [Path("src/multi.py")]
        config = {"max_complexity": 10}

        result = RadonParser.parse_cc(json_output, files, config)

        # Both closures should trigger warnings
        assert len(result.warnings) == 2
        warning_messages = [w.message for w in result.warnings]
        assert any("closure1" in msg for msg in warning_messages)
        assert any("closure2" in msg for msg in warning_messages)

    def test_parse_cc_with_empty_closures_list(self):
        """Test parsing function with empty closures list."""
        json_output = json.dumps(
            {
                "src/test.py": [
                    {
                        "type": "function",
                        "name": "no_closures",
                        "lineno": 10,
                        "complexity": 2,
                        "rank": "A",
                        "closures": [],
                    }
                ]
            }
        )
        files = [Path("src/test.py")]

        result = RadonParser.parse_cc(json_output, files)

        # Should handle empty closures gracefully
        assert result.passed is True
        assert len(result.warnings) == 0

    def test_parse_mi_with_invalid_json(self):
        """Test MI parsing with invalid JSON input raises JSONDecodeError."""
        import json

        invalid_json = "not valid json {"

        # Function raises JSONDecodeError as documented in docstring
        with pytest.raises(json.JSONDecodeError):
            RadonParser.parse_mi(invalid_json, [Path("test.py")])

    def test_parse_raw_with_invalid_json(self):
        """Test raw metrics parsing with invalid JSON input raises JSONDecodeError."""
        import json

        invalid_json = "{ broken json"

        # Function raises JSONDecodeError as documented in docstring
        with pytest.raises(json.JSONDecodeError):
            RadonParser.parse_raw(invalid_json, [Path("test.py")])

    def test_parse_cc_with_file_having_no_functions(self):
        """Test parsing when file exists in JSON but has empty function list."""
        json_output = json.dumps({"src/empty.py": []})
        files = [Path("src/empty.py")]

        result = RadonParser.parse_cc(json_output, files)

        # Empty list should be handled - no warnings
        assert result.passed is True
        assert len(result.warnings) == 0

    def test_parse_mi_with_multiple_files_mixed_scores(self):
        """Test MI parsing with multiple files having different maintainability."""
        json_output = json.dumps(
            {
                "good.py": {"mi": 85.5, "rank": "A"},
                "bad.py": {"mi": 20.3, "rank": "C"},
                "ugly.py": {"mi": 10.1, "rank": "C"},
            }
        )
        files = [Path("good.py"), Path("bad.py"), Path("ugly.py")]
        config = {"min_maintainability": 50}

        result = RadonParser.parse_mi(json_output, files, config)

        # Should flag bad.py and ugly.py
        assert len(result.warnings) == 2
        assert result.passed is False

    def test_calculate_average_complexity_with_no_data(self):
        """Test average complexity calculation with no functions."""
        json_output = json.dumps({})

        avg = RadonParser.calculate_average_complexity(json_output)

        assert avg == 0.0

    def test_identify_high_complexity_with_no_high_complexity_functions(self):
        """Test identifying high complexity when none exist."""
        json_output = json.dumps(
            {
                "simple.py": [
                    {"name": "func1", "complexity": 1, "rank": "A"},
                    {"name": "func2", "complexity": 2, "rank": "A"},
                ]
            }
        )
        threshold = 10

        high_complexity = RadonParser.identify_high_complexity_functions(json_output, threshold)

        assert len(high_complexity) == 0
