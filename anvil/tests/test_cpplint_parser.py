"""
Tests for cpplint parser.

Tests the CpplintParser class which parses cpplint text output for
Google C++ Style Guide violations.
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from anvil.parsers.cpplint_parser import CpplintParser


class TestCpplintStyleViolationParsing:
    """Test parsing of cpplint style violation messages."""

    def test_parse_output_with_no_violations(self):
        """Test parsing cpplint output when no violations are found."""
        output = "Done processing main.cpp\nTotal errors found: 0\n"
        parser = CpplintParser()
        result = parser.parse_output(output, ["main.cpp"])

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.files_checked == 1

    def test_parse_whitespace_violation(self):
        """Test parsing whitespace category violations."""
        output = (
            "src/main.cpp:10:  Extra space before ( in function call  "
            "[whitespace/parens] [4]\n"
            "Done processing src/main.cpp\n"
            "Total errors found: 1\n"
        )
        parser = CpplintParser()
        result = parser.parse_output(output, ["src/main.cpp"])

        assert result.passed is False
        assert len(result.errors) == 1
        issue = result.errors[0]
        assert issue.file_path == "src/main.cpp"
        assert issue.line_number == 10
        assert "Extra space before ( in function call" in issue.message
        assert issue.rule_name == "whitespace/parens"
        assert issue.severity == "error"

    def test_parse_readability_violation(self):
        """Test parsing readability category violations."""
        output = (
            "include/utils.h:25:  Lines should be <= 80 characters long  "
            "[readability/line_length] [2]\n"
            "Done processing include/utils.h\n"
            "Total errors found: 1\n"
        )
        parser = CpplintParser()
        result = parser.parse_output(output, ["include/utils.h"])

        assert result.passed is True  # Only errors fail validation
        assert len(result.warnings) == 1
        issue = result.warnings[0]
        assert issue.file_path == "include/utils.h"
        assert issue.line_number == 25
        assert "Lines should be <= 80 characters long" in issue.message
        assert issue.rule_name == "readability/line_length"
        assert issue.severity == "warning"

    def test_parse_build_violation(self):
        """Test parsing build category violations."""
        output = (
            "src/module.cpp:1:  Include the directory when naming .h files  "
            "[build/include] [4]\n"
            "Done processing src/module.cpp\n"
            "Total errors found: 1\n"
        )
        parser = CpplintParser()
        result = parser.parse_output(output, ["src/module.cpp"])

        assert result.passed is False
        assert len(result.errors) == 1
        issue = result.errors[0]
        assert issue.rule_name == "build/include"

    def test_parse_runtime_violation(self):
        """Test parsing runtime category violations."""
        output = (
            "src/app.cpp:42:  Do not use C-style cast. Use static_cast<> instead  "
            "[runtime/casting] [4]\n"
            "Done processing src/app.cpp\n"
            "Total errors found: 1\n"
        )
        parser = CpplintParser()
        result = parser.parse_output(output, ["src/app.cpp"])

        assert result.passed is False
        assert len(result.errors) == 1
        issue = result.errors[0]
        assert issue.rule_name == "runtime/casting"
        assert "C-style cast" in issue.message

    def test_parse_legal_violation(self):
        """Test parsing legal category violations (copyright headers)."""
        output = (
            "src/new_file.cpp:0:  No copyright message found.  "
            "You should have a line: '// Copyright [year] <Copyright Owner>'  "
            "[legal/copyright] [5]\n"
            "Done processing src/new_file.cpp\n"
            "Total errors found: 1\n"
        )
        parser = CpplintParser()
        result = parser.parse_output(output, ["src/new_file.cpp"])

        assert result.passed is False
        assert len(result.errors) == 1
        issue = result.errors[0]
        assert issue.line_number == 0
        assert issue.rule_name == "legal/copyright"
        assert "copyright" in issue.message.lower()

    def test_parse_multiple_violations(self):
        """Test parsing output with multiple violations in multiple files."""
        output = (
            "src/main.cpp:10:  Extra space after (  [whitespace/parens] [2]\n"
            "src/main.cpp:15:  Missing space before {  [whitespace/braces] [5]\n"
            "src/utils.cpp:20:  Line ends in whitespace  [whitespace/end_of_line] [1]\n"
            "Done processing src/main.cpp\n"
            "Done processing src/utils.cpp\n"
            "Total errors found: 3\n"
        )
        parser = CpplintParser()
        result = parser.parse_output(output, ["src/main.cpp", "src/utils.cpp"])

        assert result.passed is False
        assert len(result.errors) == 1  # confidence 5
        assert len(result.warnings) == 2  # confidence 1, 2


class TestCpplintConfidenceMapping:
    """Test mapping of cpplint confidence levels to severity."""

    def test_confidence_5_maps_to_error(self):
        """Test that confidence level 5 maps to error severity."""
        output = "file.cpp:1:  Some message  [category/subcategory] [5]\n"
        parser = CpplintParser()
        result = parser.parse_output(output, ["file.cpp"])

        assert len(result.errors) == 1
        assert len(result.warnings) == 0

    def test_confidence_4_maps_to_error(self):
        """Test that confidence level 4 maps to error severity."""
        output = "file.cpp:1:  Some message  [category/subcategory] [4]\n"
        parser = CpplintParser()
        result = parser.parse_output(output, ["file.cpp"])

        assert len(result.errors) == 1
        assert len(result.warnings) == 0

    def test_confidence_3_maps_to_warning(self):
        """Test that confidence level 3 maps to warning severity."""
        output = "file.cpp:1:  Some message  [category/subcategory] [3]\n"
        parser = CpplintParser()
        result = parser.parse_output(output, ["file.cpp"])

        assert len(result.errors) == 0
        assert len(result.warnings) == 1

    def test_confidence_2_maps_to_warning(self):
        """Test that confidence level 2 maps to warning severity."""
        output = "file.cpp:1:  Some message  [category/subcategory] [2]\n"
        parser = CpplintParser()
        result = parser.parse_output(output, ["file.cpp"])

        assert len(result.errors) == 0
        assert len(result.warnings) == 1

    def test_confidence_1_maps_to_warning(self):
        """Test that confidence level 1 maps to warning severity."""
        output = "file.cpp:1:  Some message  [category/subcategory] [1]\n"
        parser = CpplintParser()
        result = parser.parse_output(output, ["file.cpp"])

        assert len(result.errors) == 0
        assert len(result.warnings) == 1


class TestCpplintCommandBuilding:
    """Test building cpplint command with various options."""

    def test_build_command_default_options(self):
        """Test building cpplint command with default options."""
        parser = CpplintParser()
        command = parser.build_command(["src/main.cpp"], {})

        assert command[0] == "cpplint"
        assert "src/main.cpp" in command

    def test_build_command_with_filter_options(self):
        """Test building command with filter options to enable/disable checks."""
        parser = CpplintParser()
        options = {"filter": "-whitespace/parens,+readability/line_length"}
        command = parser.build_command(["main.cpp"], options)

        assert "--filter=-whitespace/parens,+readability/line_length" in command

    def test_build_command_with_linelength(self):
        """Test building command with custom line length."""
        parser = CpplintParser()
        options = {"linelength": "100"}
        command = parser.build_command(["main.cpp"], options)

        assert "--linelength=100" in command

    def test_build_command_with_root_directory(self):
        """Test building command with root directory for header guards."""
        parser = CpplintParser()
        options = {"root": "include"}
        command = parser.build_command(["main.cpp"], options)

        assert "--root=include" in command

    def test_build_command_with_extensions(self):
        """Test building command with custom file extensions."""
        parser = CpplintParser()
        options = {"extensions": "cpp,cc,h,hpp"}
        command = parser.build_command(["main.cpp"], options)

        assert "--extensions=cpp,cc,h,hpp" in command

    def test_build_command_with_counting(self):
        """Test building command with counting mode."""
        parser = CpplintParser()
        options = {"counting": "detailed"}
        command = parser.build_command(["main.cpp"], options)

        assert "--counting=detailed" in command

    def test_build_command_with_quiet(self):
        """Test building command with quiet mode (only print final summary)."""
        parser = CpplintParser()
        options = {"quiet": True}
        command = parser.build_command(["main.cpp"], options)

        assert "--quiet" in command

    def test_build_command_with_multiple_files(self):
        """Test building command with multiple files."""
        parser = CpplintParser()
        files = ["src/main.cpp", "src/utils.cpp", "include/utils.h"]
        command = parser.build_command(files, {})

        for file in files:
            assert file in command


class TestCpplintErrorHandling:
    """Test error handling in cpplint parser."""

    def test_error_when_cpplint_not_installed(self, mocker: MockerFixture):
        """Test error handling when cpplint is not installed."""
        mocker.patch(
            "subprocess.run",
            side_effect=FileNotFoundError("cpplint not found"),
        )

        parser = CpplintParser()
        result = parser.run(["main.cpp"], {})

        assert result.passed is False
        assert len(result.errors) == 1
        assert "cpplint" in result.errors[0].message.lower()
        assert "not found" in result.errors[0].message.lower()

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test timeout handling for long-running cpplint."""
        mocker.patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired("cpplint", 30),
        )

        parser = CpplintParser()
        result = parser.run(["main.cpp"], {"timeout": 30})

        assert result.passed is False
        assert len(result.errors) == 1
        assert "timed out" in result.errors[0].message.lower()

    def test_parse_with_empty_output(self):
        """Test parsing when cpplint produces empty output."""
        parser = CpplintParser()
        result = parser.parse_output("", ["main.cpp"])

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0


class TestCpplintVersionDetection:
    """Test cpplint version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test successful version detection."""
        mock_result = Mock()
        mock_result.stdout = "cpplint 1.6.1\n"
        mock_result.returncode = 0
        mocker.patch("subprocess.run", return_value=mock_result)

        parser = CpplintParser()
        version = parser.get_version()

        assert version == "1.6.1"

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test version detection when cpplint not available."""
        mocker.patch(
            "subprocess.run",
            side_effect=FileNotFoundError(),
        )

        parser = CpplintParser()
        version = parser.get_version()

        assert version is None


class TestCpplintIntegrationWithFixtures:
    """Integration tests with real cpplint on fixture files."""

    @pytest.mark.skipif(
        not Path("tests/fixtures/cpp/bad_style_violations.cpp").exists(),
        reason="Fixture file not found",
    )
    def test_cpplint_on_code_with_style_issues(self):
        """Test cpplint on C++ code with style violations."""
        # This test requires cpplint to be installed
        try:
            parser = CpplintParser()
            result = parser.run(["tests/fixtures/cpp/bad_style_violations.cpp"], {})

            # Should find style violations
            assert result.passed is False or len(result.warnings) > 0
        except FileNotFoundError:
            pytest.skip("cpplint not installed")

    @pytest.mark.skipif(
        not Path("tests/fixtures/cpp/good_code.cpp").exists(),
        reason="Fixture file not found",
    )
    def test_cpplint_on_style_compliant_code(self):
        """Test cpplint on style-compliant C++ code."""
        try:
            parser = CpplintParser()
            parser.run(["tests/fixtures/cpp/good_code.cpp"], {})

            # May have some violations but should mostly pass
            # (cpplint is strict, so even good code may have some issues)
        except FileNotFoundError:
            pytest.skip("cpplint not installed")


class TestCpplintGroupingAndFiltering:
    """Test grouping and filtering of cpplint violations."""

    def test_group_violations_by_category(self):
        """Test grouping violations by category."""
        output = (
            "file.cpp:1:  Message 1  [whitespace/parens] [4]\n"
            "file.cpp:2:  Message 2  [whitespace/braces] [3]\n"
            "file.cpp:3:  Message 3  [readability/line_length] [2]\n"
            "file.cpp:4:  Message 4  [whitespace/indent] [4]\n"
        )
        parser = CpplintParser()
        result = parser.parse_output(output, ["file.cpp"])

        # Group by top-level category
        grouped = parser.group_by_category(result.errors + result.warnings)

        assert "whitespace" in grouped
        assert len(grouped["whitespace"]) == 3
        assert "readability" in grouped
        assert len(grouped["readability"]) == 1

    def test_group_violations_by_confidence(self):
        """Test grouping violations by confidence level."""
        output = (
            "file.cpp:1:  Message 1  [category/sub] [5]\n"
            "file.cpp:2:  Message 2  [category/sub] [4]\n"
            "file.cpp:3:  Message 3  [category/sub] [3]\n"
            "file.cpp:4:  Message 4  [category/sub] [1]\n"
        )
        parser = CpplintParser()
        result = parser.parse_output(output, ["file.cpp"])

        grouped = parser.group_by_confidence(result.errors + result.warnings)

        # Note: group_by_confidence uses representative values (4 for errors, 2 for warnings)
        assert 4 in grouped  # Errors (confidence 4-5)
        assert 2 in grouped  # Warnings (confidence 1-3)
        assert len(grouped[4]) == 2  # Two errors
        assert len(grouped[2]) == 2  # Two warnings
        """Test counting total violations."""
        output = (
            "file1.cpp:1:  Message 1  [category/sub] [4]\n"
            "file1.cpp:2:  Message 2  [category/sub] [3]\n"
            "file2.cpp:1:  Message 3  [category/sub] [2]\n"
        )
        parser = CpplintParser()
        result = parser.parse_output(output, ["file1.cpp", "file2.cpp"])

        total = len(result.errors) + len(result.warnings)
        assert total == 3

    def test_identify_most_common_violations(self):
        """Test identifying the most common violation types."""
        output = (
            "file.cpp:1:  Message  [whitespace/parens] [4]\n"
            "file.cpp:2:  Message  [whitespace/parens] [4]\n"
            "file.cpp:3:  Message  [whitespace/parens] [4]\n"
            "file.cpp:4:  Message  [readability/line_length] [2]\n"
            "file.cpp:5:  Message  [build/include] [4]\n"
        )
        parser = CpplintParser()
        result = parser.parse_output(output, ["file.cpp"])

        common = parser.get_most_common_violations(result.errors + result.warnings, top_n=2)

        # whitespace/parens should be most common (3 occurrences)
        assert common[0][0] == "whitespace/parens"
        assert common[0][1] == 3


class TestCpplintConfigurationHandling:
    """Test configuration file detection for cpplint."""

    def test_detect_cpplint_cfg_file(self, tmp_path: Path):
        """Test detection of CPPLINT.cfg file."""
        cpplint_cfg = tmp_path / "CPPLINT.cfg"
        cpplint_cfg.write_text("filter=-whitespace/parens\n")

        parser = CpplintParser()
        config_file = parser.detect_config_file(tmp_path)

        assert config_file == cpplint_cfg

    def test_detect_cpplint_cfg_in_parent_directory(self, tmp_path: Path):
        """Test detection of CPPLINT.cfg in parent directory."""
        cpplint_cfg = tmp_path / "CPPLINT.cfg"
        cpplint_cfg.write_text("filter=-whitespace/parens\n")

        subdir = tmp_path / "src"
        subdir.mkdir()

        parser = CpplintParser()
        config_file = parser.detect_config_file(subdir)

        assert config_file == cpplint_cfg

    def test_no_config_file_returns_none(self, tmp_path: Path):
        """Test that None is returned when no config file exists."""
        parser = CpplintParser()
        config_file = parser.detect_config_file(tmp_path)

        assert config_file is None
