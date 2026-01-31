"""
Comprehensive test suite for clang-tidy parser.

Tests parsing of clang-tidy YAML output with diagnostics and fix suggestions.
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from anvil.parsers.clang_tidy_parser import ClangTidyParser


class TestClangTidyDiagnosticParsing:
    """Test parsing of clang-tidy diagnostic messages."""

    def test_parse_output_with_no_diagnostics(self, mocker: MockerFixture):
        """Test parsing when clang-tidy finds no issues."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics: []
...
        """

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("src/main.cpp")], {})

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_warning_diagnostic(self, mocker: MockerFixture):
        """Test parsing warning-level diagnostic."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics:
  - DiagnosticName: 'readability-identifier-naming'
    DiagnosticMessage:
      Message: 'variable name must be in lowercase'
      FilePath: 'src/main.cpp'
      FileOffset: 100
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
...
        """

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("src/main.cpp")], {})

        assert result.passed is False
        assert len(result.warnings) == 1
        assert len(result.errors) == 0
        # Message includes the check name prefix
        assert (
            "readability-identifier-naming: variable name must be in lowercase"
            == result.warnings[0].message
        )
        # file_path is a string (per Issue API)
        assert result.warnings[0].file_path == str(Path("src/main.cpp"))
        assert "readability-identifier-naming" in result.warnings[0].rule_name

    def test_parse_error_diagnostic(self, mocker: MockerFixture):
        """Test parsing error-level diagnostic."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics:
  - DiagnosticName: 'clang-diagnostic-error'
    DiagnosticMessage:
      Message: "use of undeclared identifier 'foo'"
      FilePath: 'src/main.cpp'
      FileOffset: 200
      Replacements: []
    Level: Error
    BuildDirectory: '/path/to/build'
...
        """

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("src/main.cpp")], {})

        assert result.passed is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 0
        assert "undeclared identifier" in result.errors[0].message

    def test_parse_note_diagnostic(self, mocker: MockerFixture):
        """Test parsing note-level diagnostic (informational)."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics:
  - DiagnosticName: 'modernize-use-nullptr'
    DiagnosticMessage:
      Message: 'use nullptr instead of NULL'
      FilePath: 'src/main.cpp'
      FileOffset: 150
      Replacements: []
    Level: Note
    BuildDirectory: '/path/to/build'
...
        """

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("src/main.cpp")], {})

        # Notes are typically warnings in our system
        assert len(result.warnings) == 1
        assert "nullptr" in result.warnings[0].message

    def test_parse_diagnostic_with_line_column(self, mocker: MockerFixture):
        """Test parsing diagnostic with line and column information."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics:
  - DiagnosticName: 'cppcoreguidelines-init-variables'
    DiagnosticMessage:
      Message: 'variable must be initialized'
      FilePath: 'src/main.cpp'
      FileOffset: 300
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
...
        """

        # Mock offset-to-line conversion
        mocker.patch.object(
            ClangTidyParser,
            "_convert_offset_to_line",
            return_value=(10, 5),
        )

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("src/main.cpp")], {})

        assert len(result.warnings) == 1
        assert result.warnings[0].line_number == 10
        assert result.warnings[0].column_number == 5

    def test_parse_multiple_diagnostics(self, mocker: MockerFixture):
        """Test parsing output with multiple diagnostics."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics:
  - DiagnosticName: 'readability-magic-numbers'
    DiagnosticMessage:
      Message: 'avoid magic numbers'
      FilePath: 'src/main.cpp'
      FileOffset: 100
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
  - DiagnosticName: 'modernize-use-auto'
    DiagnosticMessage:
      Message: 'use auto when initializing with cast'
      FilePath: 'src/main.cpp'
      FileOffset: 200
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
  - DiagnosticName: 'bugprone-use-after-move'
    DiagnosticMessage:
      Message: 'use of moved value'
      FilePath: 'src/main.cpp'
      FileOffset: 300
      Replacements: []
    Level: Error
    BuildDirectory: '/path/to/build'
...
        """

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("src/main.cpp")], {})

        assert result.passed is False
        assert len(result.warnings) == 2
        assert len(result.errors) == 1


class TestClangTidyReplacements:
    """Test parsing of clang-tidy fix suggestions (replacements)."""

    def test_parse_diagnostic_with_replacements(self, mocker: MockerFixture):
        """Test parsing diagnostic with fix suggestions."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics:
  - DiagnosticName: 'modernize-use-nullptr'
    DiagnosticMessage:
      Message: 'use nullptr'
      FilePath: 'src/main.cpp'
      FileOffset: 100
      Replacements:
        - FilePath: 'src/main.cpp'
          Offset: 100
          Length: 4
          ReplacementText: 'nullptr'
    Level: Warning
    BuildDirectory: '/path/to/build'
...
        """

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("src/main.cpp")], {})

        assert len(result.warnings) == 1
        assert "nullptr" in result.warnings[0].message

    def test_count_fixable_diagnostics(self, mocker: MockerFixture):
        """Test counting diagnostics with fix suggestions."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics:
  - DiagnosticName: 'modernize-use-nullptr'
    DiagnosticMessage:
      Message: 'use nullptr'
      FilePath: 'src/main.cpp'
      FileOffset: 100
      Replacements:
        - FilePath: 'src/main.cpp'
          Offset: 100
          Length: 4
          ReplacementText: 'nullptr'
    Level: Warning
    BuildDirectory: '/path/to/build'
  - DiagnosticName: 'readability-magic-numbers'
    DiagnosticMessage:
      Message: 'avoid magic numbers'
      FilePath: 'src/main.cpp'
      FileOffset: 200
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
...
        """

        fixable_count = ClangTidyParser.count_fixable_diagnostics(yaml_output)

        assert fixable_count == 1


class TestClangTidyCommandBuilding:
    """Test building clang-tidy commands with various options."""

    def test_build_command_default_options(self):
        """Test building command with default options."""
        files = [Path("src/main.cpp")]
        config = {}

        command = ClangTidyParser.build_command(files, config)

        assert "clang-tidy" in command[0]
        # Normalize path for comparison (Windows uses backslashes)
        file_paths = [str(Path(arg)) for arg in command]
        assert str(Path("src/main.cpp")) in file_paths
        assert "--export-fixes=-" in command

    def test_build_command_with_checks(self):
        """Test building command with specific checks."""
        files = [Path("src/main.cpp")]
        config = {"checks": "modernize-*,readability-*"}

        command = ClangTidyParser.build_command(files, config)

        assert any("--checks=" in arg for arg in command)
        checks_arg = [arg for arg in command if "--checks=" in arg][0]
        assert "modernize-*" in checks_arg
        assert "readability-*" in checks_arg

    def test_build_command_with_header_filter(self):
        """Test building command with header filter."""
        files = [Path("src/main.cpp")]
        config = {"header_filter": ".*\\.h$"}

        command = ClangTidyParser.build_command(files, config)

        assert any("--header-filter=" in arg for arg in command)

    def test_build_command_with_warnings_as_errors(self):
        """Test building command with warnings-as-errors."""
        files = [Path("src/main.cpp")]
        config = {"warnings_as_errors": "*"}

        command = ClangTidyParser.build_command(files, config)

        assert any("--warnings-as-errors=" in arg for arg in command)

    def test_build_command_with_config_file(self):
        """Test building command with .clang-tidy config file."""
        files = [Path("src/main.cpp")]
        config = {"config_file": ".clang-tidy"}

        command = ClangTidyParser.build_command(files, config)

        # When config file exists, no --checks needed
        assert not any("--checks=" in arg for arg in command)

    def test_build_command_with_extra_args(self):
        """Test building command with extra compiler arguments."""
        files = [Path("src/main.cpp")]
        config = {"extra_args": ["-std=c++17", "-I/usr/include"]}

        command = ClangTidyParser.build_command(files, config)

        assert "--" in command
        dash_index = command.index("--")
        assert "-std=c++17" in command[dash_index + 1 :]
        assert "-I/usr/include" in command[dash_index + 1 :]

    def test_build_command_with_compile_commands(self):
        """Test building command with compile_commands.json."""
        files = [Path("src/main.cpp")]
        config = {"compile_commands": "build/compile_commands.json"}

        command = ClangTidyParser.build_command(files, config)

        assert any("-p" in arg or "--p=" in arg for arg in command)

    def test_build_command_with_multiple_files(self):
        """Test building command with multiple files."""
        files = [Path("src/main.cpp"), Path("src/helper.cpp"), Path("include/header.h")]
        config = {}

        command = ClangTidyParser.build_command(files, config)

        # Normalize paths for comparison (Windows uses backslashes)
        file_paths = [str(Path(arg)) for arg in command]
        assert str(Path("src/main.cpp")) in file_paths
        assert str(Path("src/helper.cpp")) in file_paths
        assert str(Path("include/header.h")) in file_paths


class TestClangTidyErrorHandling:
    """Test error handling for clang-tidy execution."""

    def test_error_when_clang_tidy_not_installed(self, mocker: MockerFixture):
        """Test error handling when clang-tidy is not installed."""
        # Mock subprocess.run in the module where it's used
        mocker.patch(
            "anvil.parsers.clang_tidy_parser.subprocess.run",
            side_effect=FileNotFoundError("clang-tidy not found"),
        )

        result = ClangTidyParser.run_and_parse(
            [Path("src/main.cpp")],
            {},
        )

        assert result.passed is False
        assert len(result.errors) > 0
        assert any("not installed" in err.message.lower() for err in result.errors)

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test timeout handling for long-running clang-tidy."""
        # Mock subprocess.run in the module where it's used
        mocker.patch(
            "anvil.parsers.clang_tidy_parser.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="clang-tidy", timeout=60),
        )

        config = {"timeout": 60}
        result = ClangTidyParser.run_and_parse(
            [Path("src/main.cpp")],
            config,
        )

        assert result.passed is False
        assert len(result.errors) > 0
        # Check for "timed out" in the error message
        assert any("timed out" in err.message.lower() for err in result.errors)

    def test_parse_with_invalid_yaml(self, mocker: MockerFixture):
        """Test parsing invalid YAML output."""
        invalid_yaml = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics: [invalid yaml structure
...
        """

        result = ClangTidyParser.parse_yaml(invalid_yaml, [Path("src/main.cpp")], {})

        assert result.passed is False
        assert len(result.errors) > 0


class TestClangTidyVersionDetection:
    """Test clang-tidy version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detection of clang-tidy version."""
        mock_result = MagicMock()
        mock_result.stdout = "LLVM version 14.0.0\n"
        mock_result.returncode = 0
        mocker.patch("subprocess.run", return_value=mock_result)

        version = ClangTidyParser.get_version()

        assert version is not None
        assert "14.0" in version

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test handling when version detection fails."""
        mocker.patch(
            "subprocess.run",
            side_effect=FileNotFoundError("clang-tidy not found"),
        )

        version = ClangTidyParser.get_version()

        assert version is None


class TestClangTidyIntegrationWithFixtures:
    """Integration tests with real clang-tidy (skipped if not installed)."""

    @pytest.mark.skipif(
        not ClangTidyParser.is_installed(),
        reason="clang-tidy not installed",
    )
    def test_clang_tidy_on_clean_cpp_code(self):
        """Test clang-tidy on clean C++ code."""
        # Would need real C++ fixture file
        pytest.skip("Requires C++ fixture setup")

    @pytest.mark.skipif(
        not ClangTidyParser.is_installed(),
        reason="clang-tidy not installed",
    )
    def test_clang_tidy_on_code_with_issues(self):
        """Test clang-tidy on C++ code with issues."""
        # Would need real C++ fixture file
        pytest.skip("Requires C++ fixture setup")


class TestClangTidyGroupingAndFiltering:
    """Test grouping and filtering of diagnostics."""

    def test_group_diagnostics_by_check_name(self, mocker: MockerFixture):
        """Test grouping diagnostics by check name."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics:
  - DiagnosticName: 'readability-magic-numbers'
    DiagnosticMessage:
      Message: 'avoid magic numbers'
      FilePath: 'src/main.cpp'
      FileOffset: 100
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
  - DiagnosticName: 'readability-magic-numbers'
    DiagnosticMessage:
      Message: 'avoid magic numbers'
      FilePath: 'src/helper.cpp'
      FileOffset: 50
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
  - DiagnosticName: 'modernize-use-auto'
    DiagnosticMessage:
      Message: 'use auto'
      FilePath: 'src/main.cpp'
      FileOffset: 200
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
...
        """

        grouped = ClangTidyParser.group_by_check_name(yaml_output)

        assert "readability-magic-numbers" in grouped
        assert "modernize-use-auto" in grouped
        assert len(grouped["readability-magic-numbers"]) == 2
        assert len(grouped["modernize-use-auto"]) == 1

    def test_group_diagnostics_by_file(self, mocker: MockerFixture):
        """Test grouping diagnostics by file."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics:
  - DiagnosticName: 'readability-magic-numbers'
    DiagnosticMessage:
      Message: 'avoid magic numbers'
      FilePath: 'src/main.cpp'
      FileOffset: 100
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
  - DiagnosticName: 'modernize-use-auto'
    DiagnosticMessage:
      Message: 'use auto'
      FilePath: 'src/helper.cpp'
      FileOffset: 200
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
...
        """

        grouped = ClangTidyParser.group_by_file(yaml_output)

        assert "src/main.cpp" in grouped
        assert "src/helper.cpp" in grouped
        assert len(grouped["src/main.cpp"]) == 1
        assert len(grouped["src/helper.cpp"]) == 1

    def test_filter_diagnostics_by_severity(self, mocker: MockerFixture):
        """Test filtering diagnostics by severity level."""
        yaml_output = """
---
MainSourceFile: 'src/main.cpp'
Diagnostics:
  - DiagnosticName: 'readability-magic-numbers'
    DiagnosticMessage:
      Message: 'avoid magic numbers'
      FilePath: 'src/main.cpp'
      FileOffset: 100
      Replacements: []
    Level: Warning
    BuildDirectory: '/path/to/build'
  - DiagnosticName: 'bugprone-use-after-move'
    DiagnosticMessage:
      Message: 'use of moved value'
      FilePath: 'src/main.cpp'
      FileOffset: 200
      Replacements: []
    Level: Error
    BuildDirectory: '/path/to/build'
...
        """

        errors = ClangTidyParser.filter_by_severity(yaml_output, "Error")
        warnings = ClangTidyParser.filter_by_severity(yaml_output, "Warning")

        assert len(errors) == 1
        assert len(warnings) == 1


class TestClangTidyConfigurationHandling:
    """Test configuration file detection and handling."""

    def test_detect_clang_tidy_config_file(self, tmp_path: Path):
        """Test detection of .clang-tidy configuration file."""
        config_file = tmp_path / ".clang-tidy"
        config_file.write_text("Checks: 'modernize-*'")

        found_config = ClangTidyParser.find_config_file(tmp_path)

        assert found_config == config_file

    def test_detect_clang_tidy_in_parent_directory(self, tmp_path: Path):
        """Test detection of .clang-tidy in parent directory."""
        parent_config = tmp_path / ".clang-tidy"
        parent_config.write_text("Checks: 'modernize-*'")

        subdir = tmp_path / "src"
        subdir.mkdir()

        found_config = ClangTidyParser.find_config_file(subdir)

        assert found_config == parent_config

    def test_no_config_file_returns_none(self, tmp_path: Path):
        """Test that None is returned when no config file exists."""
        found_config = ClangTidyParser.find_config_file(tmp_path)

        assert found_config is None


class TestClangTidyEdgeCasesAndErrorPaths:
    """Test edge cases and error paths for better coverage."""

    def test_parse_yaml_with_no_docs(self):
        """Test parsing YAML with no documents."""
        yaml_output = ""

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("test.cpp")], {})

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_yaml_with_empty_doc(self):
        """Test parsing YAML with empty document."""
        yaml_output = "---\n...\n"

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("test.cpp")], {})

        assert result.passed is True
        assert len(result.errors) == 0

    def test_parse_yaml_with_doc_without_diagnostics_key(self):
        """Test parsing YAML document without Diagnostics key."""
        yaml_output = """
---
MainSourceFile: 'test.cpp'
BuildDirectory: '/build'
...
        """

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("test.cpp")], {})

        assert result.passed is True
        assert len(result.errors) == 0

    def test_parse_diagnostic_with_malformed_data(self):
        """Test parsing diagnostic with missing/malformed fields."""
        # Diagnostic missing required fields - defaults are used
        diagnostic = {}

        issue = ClangTidyParser._parse_diagnostic(diagnostic, [Path("test.cpp")])

        # Should create issue with defaults when dict is valid but empty
        assert issue is not None
        assert issue.file_path == "test.cpp"
        assert issue.rule_name == "unknown"

    def test_parse_diagnostic_with_no_filepath(self):
        """Test diagnostic parsing when FilePath is missing."""
        yaml_output = """
---
Diagnostics:
  - DiagnosticName: 'test-check'
    DiagnosticMessage:
      Message: 'test message'
      FileOffset: 0
    Level: Warning
...
        """

        result = ClangTidyParser.parse_yaml(yaml_output, [Path("fallback.cpp")], {})

        # Should use fallback file path
        assert len(result.warnings) == 1
        assert "fallback.cpp" in result.warnings[0].file_path

    def test_convert_offset_to_line_file_not_exists(self):
        """Test offset conversion when file doesn't exist."""
        nonexistent = Path("/nonexistent/file.cpp")

        line, col = ClangTidyParser._convert_offset_to_line(nonexistent, 100)

        assert line == 0
        assert col == 0

    def test_convert_offset_to_line_with_io_error(self, tmp_path: Path, mocker: MockerFixture):
        """Test offset conversion when file read fails."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int main() {}")

        # Mock open to raise IOError
        mocker.patch("builtins.open", side_effect=IOError("Permission denied"))

        line, col = ClangTidyParser._convert_offset_to_line(test_file, 10)

        assert line == 0
        assert col == 0

    def test_convert_offset_to_line_at_start_of_file(self, tmp_path: Path):
        """Test offset conversion at start of file (no newlines before)."""
        test_file = tmp_path / "test.cpp"
        test_file.write_text("int main() {}")

        line, col = ClangTidyParser._convert_offset_to_line(test_file, 3)

        # Should be line 1, column 4 (offset 3 = 4th character)
        assert line == 1
        assert col == 4

    def test_convert_offset_to_line_after_newlines(self, tmp_path: Path):
        """Test offset conversion after multiple newlines."""
        test_file = tmp_path / "test.cpp"
        # Use binary write to ensure exact bytes
        test_file.write_bytes(b"line1\nline2\nline3")

        # Offset  after "line1\n" (6 bytes): should be line 2, column 1
        line, col = ClangTidyParser._convert_offset_to_line(test_file, 6)

        assert line == 2  # After first newline
        assert col == 1

    def test_map_level_to_severity_note(self):
        """Test mapping Note level to warning severity."""
        severity = ClangTidyParser._map_level_to_severity("Note")
        assert severity == "warning"

    def test_map_level_to_severity_remark(self):
        """Test mapping Remark level to warning severity."""
        severity = ClangTidyParser._map_level_to_severity("Remark")
        assert severity == "warning"

    def test_map_level_to_severity_error(self):
        """Test mapping Error level to error severity."""
        severity = ClangTidyParser._map_level_to_severity("Error")
        assert severity == "error"

    def test_map_level_to_severity_fatal(self):
        """Test mapping Fatal level defaults to warning (not explicitly handled)."""
        severity = ClangTidyParser._map_level_to_severity("Fatal")
        # "Fatal" is not explicitly mapped, falls through to default
        assert severity == "warning"

    def test_map_level_to_severity_unknown(self):
        """Test mapping unknown level defaults to warning."""
        severity = ClangTidyParser._map_level_to_severity("UnknownLevel")
        assert severity == "warning"

    def test_yaml_parse_error_creates_error_issue(self):
        """Test that YAML parsing errors are captured as issues."""
        # Invalid YAML syntax
        invalid_yaml = "---\n  - invalid: [\n  missing bracket"

        result = ClangTidyParser.parse_yaml(invalid_yaml, [Path("test.cpp")], {})

        # Should create an error issue for YAML parse failure
        assert len(result.errors) == 1
        assert "Failed to parse clang-tidy YAML output" in result.errors[0].message
        assert result.errors[0].rule_name == "yaml-parse-error"
        assert result.passed is False

    def test_diagnostic_with_typed_error(self):
        """Test diagnostic parsing with TypeError exception path."""

        # Use a dict subclass that raises TypeError on .get()
        class BrokenDict(dict):
            def get(self, key, default=None):
                raise TypeError("Simulated TypeError")

        diagnostic = BrokenDict({"DiagnosticName": "test"})

        issue = ClangTidyParser._parse_diagnostic(diagnostic, [Path("test.cpp")])

        # Should return None when TypeError occurs
        assert issue is None
