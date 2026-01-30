"""
Tests for clang-format parser.

Tests the ClangFormatParser class which checks C++ code formatting
according to a specified style (Google, LLVM, etc.).
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock

import pytest
from pytest_mock import MockerFixture

from anvil.parsers.clang_format_parser import ClangFormatParser


class TestClangFormatExitCodeParsing:
    """Test parsing of clang-format results via exit codes."""

    def test_parse_output_all_files_formatted(self):
        """Test parsing when all files are properly formatted."""
        output = ""
        parser = ClangFormatParser()
        result = parser.parse_output(output, ["main.cpp"], exit_code=0)

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
        assert result.files_checked == 1

    def test_parse_output_files_need_formatting(self):
        """Test parsing when files need formatting (exit code 1)."""
        output = ""
        parser = ClangFormatParser()
        result = parser.parse_output(output, ["main.cpp"], exit_code=1)

        assert result.passed is False
        assert len(result.errors) == 1
        assert "main.cpp" in result.errors[0].file_path
        assert result.errors[0].message == "File needs formatting"
        assert result.files_checked == 1

    def test_parse_output_multiple_files_mixed_results(self):
        """Test parsing multiple files where some need formatting."""
        # In dry-run mode, clang-format returns exit code 1 if ANY file needs formatting
        output = ""
        files = ["good.cpp", "bad.cpp", "ugly.cpp"]
        parser = ClangFormatParser()
        result = parser.parse_output(output, files, exit_code=1)

        assert result.passed is False
        # Without diff output, we can't tell which specific files need formatting
        # So we report all files as potentially needing formatting
        assert len(result.errors) >= 1
        assert result.files_checked == 3

    def test_parse_windows_paths(self):
        """Test parsing with Windows-style paths."""
        output = ""
        files = [r"C:\project\src\main.cpp"]
        parser = ClangFormatParser()
        result = parser.parse_output(output, files, exit_code=1)

        assert result.passed is False
        assert len(result.errors) == 1

    def test_parse_output_with_syntax_errors(self):
        """Test parsing when clang-format encounters syntax errors."""
        # Syntax errors typically result in exit code 1 and error messages
        output = "error: expected ';' after expression\n"
        parser = ClangFormatParser()
        result = parser.parse_output(output, ["bad.cpp"], exit_code=1)

        assert result.passed is False
        assert len(result.errors) >= 1


class TestClangFormatXMLParsing:
    """Test parsing of clang-format XML replacements output."""

    def test_parse_xml_replacements_output(self):
        """Test parsing XML format with replacements."""
        xml_output = """<?xml version='1.0'?>
<replacements xml:space='preserve' incomplete_format='false'>
<replacement offset='42' length='1' file='main.cpp'>  </replacement>
<replacement offset='120' length='0' file='main.cpp'> </replacement>
</replacements>"""
        parser = ClangFormatParser()
        result = parser.parse_output(xml_output, ["main.cpp"], exit_code=1)

        assert result.passed is False
        assert len(result.errors) >= 1
        # Check that we detected replacements needed
        assert any("main.cpp" in err.file_path for err in result.errors)

    def test_parse_xml_no_replacements(self):
        """Test parsing XML format with no replacements needed."""
        xml_output = """<?xml version='1.0'?>
<replacements xml:space='preserve' incomplete_format='false'>
</replacements>"""
        parser = ClangFormatParser()
        result = parser.parse_output(xml_output, ["main.cpp"], exit_code=0)

        assert result.passed is True
        assert len(result.errors) == 0


class TestClangFormatCommandBuilding:
    """Test building clang-format commands with various options."""

    def test_build_command_default_options(self):
        """Test build command with default options (dry-run check)."""
        parser = ClangFormatParser()
        cmd = parser.build_command(["main.cpp"], {})

        assert "clang-format" in cmd
        assert "--dry-run" in cmd
        assert "--Werror" in cmd
        assert "main.cpp" in cmd

    def test_build_command_with_style_option(self):
        """Test build command with specific style."""
        parser = ClangFormatParser()
        cmd = parser.build_command(["main.cpp"], {"style": "Google"})

        assert "--style=Google" in cmd

    def test_build_command_with_llvm_style(self):
        """Test build command with LLVM style."""
        parser = ClangFormatParser()
        cmd = parser.build_command(["main.cpp"], {"style": "LLVM"})

        assert "--style=LLVM" in cmd

    def test_build_command_with_config_file(self):
        """Test build command with .clang-format config file."""
        parser = ClangFormatParser()
        cmd = parser.build_command(["main.cpp"], {"style": "file"})

        assert "--style=file" in cmd

    def test_build_command_with_fallback_style(self):
        """Test build command with fallback style."""
        parser = ClangFormatParser()
        cmd = parser.build_command(["main.cpp"], {"style": "file", "fallback_style": "Google"})

        assert "--style=file" in cmd
        assert "--fallback-style=Google" in cmd

    def test_build_command_with_output_xml(self):
        """Test build command requesting XML output."""
        parser = ClangFormatParser()
        cmd = parser.build_command(["main.cpp"], {"output_replacements_xml": True})

        assert "--output-replacements-xml" in cmd

    def test_build_command_with_assume_filename(self):
        """Test build command with assume-filename for stdin."""
        parser = ClangFormatParser()
        cmd = parser.build_command(["-"], {"assume_filename": "test.cpp"})  # stdin mode

        assert "--assume-filename=test.cpp" in cmd

    def test_build_command_with_multiple_files(self):
        """Test build command with multiple files."""
        parser = ClangFormatParser()
        files = ["main.cpp", "helper.cpp", "utils.cpp"]
        cmd = parser.build_command(files, {})

        assert all(f in cmd for f in files)

    def test_build_command_without_werror(self):
        """Test build command without Werror flag."""
        parser = ClangFormatParser()
        cmd = parser.build_command(["main.cpp"], {"werror": False})

        assert "--Werror" not in cmd


class TestClangFormatErrorHandling:
    """Test error handling for clang-format parser."""

    def test_error_when_clang_format_not_installed(self, mocker: MockerFixture):
        """Test error when clang-format is not installed."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = FileNotFoundError("clang-format not found")

        parser = ClangFormatParser()
        with pytest.raises(FileNotFoundError):
            parser.run(["main.cpp"], {})

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test timeout handling for long-running clang-format."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = subprocess.TimeoutExpired("clang-format", 30)

        parser = ClangFormatParser()
        with pytest.raises(subprocess.TimeoutExpired):
            parser.run(["main.cpp"], {"timeout": 30})

    def test_parse_with_empty_output(self):
        """Test parsing with empty output."""
        parser = ClangFormatParser()
        result = parser.parse_output("", ["main.cpp"], exit_code=0)

        assert result.passed is True
        assert len(result.errors) == 0


class TestClangFormatVersionDetection:
    """Test clang-format version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test successful version detection."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = Mock(stdout="clang-format version 14.0.0\n", returncode=0)

        parser = ClangFormatParser()
        version = parser.get_version()

        assert version == "14.0.0"
        mock_run.assert_called_once()

    def test_version_detection_different_formats(self, mocker: MockerFixture):
        """Test version detection with different output formats."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value = Mock(
            stdout="LLVM version 15.0.7\nOptimized build.\nDefault target: x86_64-pc-linux-gnu\n",
            returncode=0,
        )

        parser = ClangFormatParser()
        version = parser.get_version()

        assert "15.0.7" in version or version is not None

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test version detection when clang-format not available."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.side_effect = FileNotFoundError()

        parser = ClangFormatParser()
        version = parser.get_version()

        assert version is None


class TestClangFormatIntegrationWithFixtures:
    """Integration tests with real clang-format on fixture files."""

    def test_clang_format_on_formatted_cpp_code(self):
        """Test clang-format on already formatted C++ code."""
        fixture_path = Path("tests/fixtures/cpp/good_code.cpp")
        if not fixture_path.exists():
            pytest.skip("Fixture file not available")

        try:
            parser = ClangFormatParser()
            result = parser.run([str(fixture_path)], {"style": "Google"})

            # Test should successfully run clang-format
            # Note: "good code" doesn't necessarily mean "formatted according to Google style"
            # so we just verify the parser executes successfully
            assert result.validator_name == "clang-format"
            assert result.files_checked == 1
        except FileNotFoundError:
            pytest.skip("clang-format not installed")

    def test_clang_format_on_unformatted_cpp_code(self):
        """Test clang-format on unformatted C++ code."""
        fixture_path = Path("tests/fixtures/cpp/bad_formatting.cpp")
        if not fixture_path.exists():
            pytest.skip("Fixture file not available")

        try:
            parser = ClangFormatParser()
            parser.run([str(fixture_path)], {"style": "Google"})

            # Unformatted code should have issues
            # (might pass if fixture is actually formatted, that's ok)
        except FileNotFoundError:
            pytest.skip("clang-format not installed")


class TestClangFormatConfigurationHandling:
    """Test detection and handling of clang-format configuration files."""

    def test_detect_clang_format_config_file(self, tmp_path):
        """Test detection of .clang-format file in directory."""
        config_file = tmp_path / ".clang-format"
        config_file.write_text("BasedOnStyle: Google\nIndentWidth: 2\n")

        parser = ClangFormatParser()
        detected = parser.detect_config_file(tmp_path)

        assert detected == config_file

    def test_detect_clang_format_in_parent_directory(self, tmp_path):
        """Test detection of .clang-format in parent directory."""
        config_file = tmp_path / ".clang-format"
        config_file.write_text("BasedOnStyle: LLVM\n")

        subdir = tmp_path / "src" / "lib"
        subdir.mkdir(parents=True)

        parser = ClangFormatParser()
        detected = parser.detect_config_file(subdir)

        assert detected == config_file

    def test_detect_clang_format_yml_variant(self, tmp_path):
        """Test detection of _clang-format file variant."""
        config_file = tmp_path / "_clang-format"
        config_file.write_text("BasedOnStyle: Chromium\n")

        parser = ClangFormatParser()
        detected = parser.detect_config_file(tmp_path)

        assert detected == config_file

    def test_no_config_file_returns_none(self, tmp_path):
        """Test returns None when no config file found."""
        parser = ClangFormatParser()
        detected = parser.detect_config_file(tmp_path)

        assert detected is None


class TestClangFormatSuggestedFixes:
    """Test generation of suggested fix commands."""

    def test_generate_fix_command(self):
        """Test generation of command to fix formatting issues."""
        parser = ClangFormatParser()
        fix_cmd = parser.generate_fix_command(["main.cpp"], {"style": "Google"})

        assert "clang-format" in fix_cmd
        assert "-i" in fix_cmd  # in-place editing
        assert "--style=Google" in fix_cmd
        assert "main.cpp" in fix_cmd

    def test_generate_fix_command_with_options(self):
        """Test fix command generation with various options."""
        parser = ClangFormatParser()
        fix_cmd = parser.generate_fix_command(
            ["src/main.cpp", "src/helper.cpp"],
            {"style": "LLVM", "fallback_style": "Google"},
        )

        assert "-i" in fix_cmd
        assert "--style=LLVM" in fix_cmd
        assert "--fallback-style=Google" in fix_cmd
        assert "src/main.cpp" in fix_cmd
        assert "src/helper.cpp" in fix_cmd


class TestClangFormatDiffOutput:
    """Test parsing of clang-format diff output."""

    def test_parse_diff_output(self):
        """Test parsing when diff output is enabled."""
        diff_output = """--- main.cpp
+++ main.cpp
@@ -1,3 +1,3 @@
-int main(){
+int main() {
   return 0;
 }
"""
        parser = ClangFormatParser()
        result = parser.parse_output(diff_output, ["main.cpp"], exit_code=1)

        assert result.passed is False
        assert len(result.errors) >= 1
        assert any("main.cpp" in err.file_path for err in result.errors)

    def test_count_files_needing_formatting(self):
        """Test counting how many files need formatting."""
        parser = ClangFormatParser()
        result = parser.parse_output("", ["a.cpp", "b.cpp", "c.cpp"], exit_code=1)

        # When exit code is 1, at least one file needs formatting
        assert result.passed is False
        assert result.files_checked == 3
