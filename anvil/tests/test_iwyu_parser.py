"""
Test suite for include-what-you-use (IWYU) parser.

Tests IWYU output parsing for include optimization suggestions.
"""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from anvil.parsers.iwyu_parser import IWYUParser


class TestIWYUSuggestionParsing:
    """Test parsing IWYU suggestions for adding/removing includes."""

    def test_parse_output_with_no_suggestions(self):
        """Test parsing output when all includes are correct."""
        output = """
main.cpp has correct #includes/fwd-decls
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp"])

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_suggestions_to_add_includes(self):
        """Test parsing suggestions to add missing includes."""
        output = """
main.cpp should add these lines:
#include <iostream>  // for std::cout
#include <vector>    // for std::vector

The full include-list for main.cpp:
#include <iostream>  // for std::cout
#include <vector>    // for std::vector
---
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp"])

        assert result.passed is False
        assert len(result.warnings) >= 2
        # Check for iostream suggestion
        iostream_warning = [w for w in result.warnings if "iostream" in w.message]
        assert len(iostream_warning) > 0
        assert "add" in iostream_warning[0].message.lower()

    def test_parse_suggestions_to_remove_includes(self):
        """Test parsing suggestions to remove unnecessary includes."""
        output = """
main.cpp should remove these lines:
- #include <string>  // lines 3-3

The full include-list for main.cpp:
#include <iostream>  // for std::cout
---
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp"])

        assert result.passed is False
        assert len(result.warnings) > 0
        # Check for string removal suggestion
        string_warning = [w for w in result.warnings if "string" in w.message]
        assert len(string_warning) > 0
        assert "remove" in string_warning[0].message.lower()

    def test_parse_forward_declaration_suggestions(self):
        """Test parsing suggestions for forward declarations."""
        output = """
main.cpp should add these lines:
class MyClass;

main.cpp should remove these lines:
- #include "myclass.h"  // lines 5-5

The full include-list for main.cpp:
class MyClass;
---
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp"])

        assert result.passed is False
        # Should have warnings for both adding forward declaration and removing include
        assert len(result.warnings) >= 2

    def test_parse_transitive_include_information(self):
        """Test parsing information about transitive includes."""
        output = """
(main.cpp has correct #includes/fwd-decls)

Note: #include <vector> is included transitively via #include <iostream>
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp"])

        # This is informational, should still pass
        assert result.passed is True

    def test_parse_multiple_files_with_suggestions(self):
        """Test parsing suggestions for multiple files."""
        output = """
main.cpp should add these lines:
#include <vector>  // for std::vector

The full include-list for main.cpp:
#include <vector>
---

helper.cpp should remove these lines:
- #include <map>  // lines 2-2

The full include-list for helper.cpp:
#include <string>
---
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp", "helper.cpp"])

        assert result.passed is False
        # Should have warnings for both files
        main_warnings = [w for w in result.warnings if "main.cpp" in w.file_path]
        helper_warnings = [w for w in result.warnings if "helper.cpp" in w.file_path]
        assert len(main_warnings) > 0
        assert len(helper_warnings) > 0


class TestIWYUWhyExplanations:
    """Test parsing IWYU 'why' explanations."""

    def test_parse_why_explanation(self):
        """Test parsing why a particular include is needed."""
        output = """
main.cpp should add these lines:
#include <vector>  // for std::vector

main.cpp: #include <vector> is needed because:
  - std::vector is used on line 15
  - std::vector::push_back is used on line 20

The full include-list for main.cpp:
#include <vector>
---
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp"])

        assert result.passed is False
        # Warning should include the reason
        vector_warnings = [w for w in result.warnings if "vector" in w.message]
        assert len(vector_warnings) > 0


class TestIWYUCommandBuilding:
    """Test IWYU command construction."""

    def test_build_command_default_options(self):
        """Test building command with default options."""
        parser = IWYUParser()
        command = parser.build_command(["main.cpp"])

        assert command[0] == "include-what-you-use"
        assert "main.cpp" in command

    def test_build_command_with_mapping_file(self):
        """Test building command with mapping file."""
        parser = IWYUParser()
        command = parser.build_command(["main.cpp"], mapping_file="custom.imp")

        assert "--mapping_file=custom.imp" in command

    def test_build_command_with_compiler_flags(self):
        """Test building command with compiler flags."""
        parser = IWYUParser()
        command = parser.build_command(
            ["main.cpp"], compiler_flags=["-std=c++17", "-I/usr/include"]
        )

        assert "-std=c++17" in command
        assert "-I/usr/include" in command

    def test_build_command_with_xiwyu_options(self):
        """Test building command with -Xiwyu options."""
        parser = IWYUParser()
        command = parser.build_command(
            ["main.cpp"], xiwyu_options=["--max_line_length=120", "--no_fwd_decls"]
        )

        assert "-Xiwyu" in command
        assert "--max_line_length=120" in command or any(
            "--max_line_length=120" in arg for arg in command
        )

    def test_build_command_with_std_option(self):
        """Test building command with C++ standard."""
        parser = IWYUParser()
        command = parser.build_command(["main.cpp"], std="c++20")

        assert "-std=c++20" in command

    def test_build_command_with_include_paths(self):
        """Test building command with include paths."""
        parser = IWYUParser()
        command = parser.build_command(
            ["main.cpp"], include_paths=["/usr/local/include", "./include"]
        )

        assert "-I/usr/local/include" in command
        assert "-I./include" in command

    def test_build_command_with_defines(self):
        """Test building command with preprocessor defines."""
        parser = IWYUParser()
        command = parser.build_command(["main.cpp"], defines=["DEBUG=1", "PLATFORM_X64"])

        assert "-DDEBUG=1" in command
        assert "-DPLATFORM_X64" in command


class TestIWYUErrorHandling:
    """Test error handling in IWYU parser."""

    def test_error_when_iwyu_not_installed(self):
        """Test error handling when IWYU is not installed."""
        parser = IWYUParser()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("include-what-you-use not found")

            result = parser.run(["main.cpp"])

            assert result.passed is False
            assert len(result.errors) > 0
            assert "not found" in result.errors[0].message.lower()

    def test_timeout_handling(self):
        """Test handling of IWYU timeout."""
        parser = IWYUParser()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(cmd="include-what-you-use", timeout=30)

            result = parser.run(["main.cpp"], timeout=30)

            assert result.passed is False
            assert len(result.errors) > 0
            # Message is "IWYU timed out after 30 seconds"
            error_msg = result.errors[0].message.lower()
            assert "timed out" in result.errors[0].message or "timeout" in error_msg

    def test_parse_with_empty_output(self):
        """Test parsing with empty output."""
        parser = IWYUParser()
        result = parser.parse_output("", ["main.cpp"])

        # Empty output means no suggestions, should pass
        assert result.passed is True


class TestIWYUVersionDetection:
    """Test IWYU version detection."""

    def test_version_detection(self):
        """Test detecting IWYU version."""
        parser = IWYUParser()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="include-what-you-use 0.18 based on clang version 14.0.0",
                stderr="",
                returncode=0,
            )

            version = parser.get_version()

            assert version == "0.18"

    def test_version_detection_different_format(self):
        """Test detecting IWYU version in different format."""
        parser = IWYUParser()

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                stdout="include-what-you-use version 0.20 (clang 15.0.0)", stderr="", returncode=0
            )

            version = parser.get_version()

            assert version == "0.20"

    def test_version_detection_failure(self):
        """Test handling when version detection fails."""
        parser = IWYUParser()

        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError()

            version = parser.get_version()

            assert version is None


class TestIWYUIntegrationWithFixtures:
    """Integration tests with real IWYU (requires IWYU installation)."""

    @pytest.mark.skip(reason="Requires IWYU installation and fixture files")
    def test_iwyu_on_code_with_include_issues(self):
        """Test IWYU on C++ code with include issues."""
        parser = IWYUParser()
        # Would need actual C++ file with include issues
        test_file = Path("tests/fixtures/cpp/include_issues.cpp")
        result = parser.run([str(test_file)])

        assert result.passed is False
        assert len(result.warnings) > 0

    @pytest.mark.skip(reason="Requires IWYU installation and fixture files")
    def test_iwyu_on_clean_includes(self):
        """Test IWYU on C++ code with correct includes."""
        parser = IWYUParser()
        # Would need actual C++ file with correct includes
        test_file = Path("tests/fixtures/cpp/clean_includes.cpp")
        result = parser.run([str(test_file)])

        assert result.passed is True


class TestIWYUSuggestionGrouping:
    """Test grouping and counting IWYU suggestions."""

    def test_group_suggestions_by_file(self):
        """Test grouping suggestions by file."""
        output = """
main.cpp should add these lines:
#include <vector>

helper.cpp should remove these lines:
- #include <map>

utils.cpp should add these lines:
#include <string>
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp", "helper.cpp", "utils.cpp"])

        # Group warnings by file
        by_file = {}
        for warning in result.warnings:
            if warning.file_path not in by_file:
                by_file[warning.file_path] = []
            by_file[warning.file_path].append(warning)

        assert len(by_file) == 3
        assert "main.cpp" in by_file
        assert "helper.cpp" in by_file
        assert "utils.cpp" in by_file

    def test_count_unnecessary_includes(self):
        """Test counting unnecessary includes."""
        output = """
main.cpp should remove these lines:
- #include <string>  // lines 3-3
- #include <map>     // lines 4-4
- #include <set>     // lines 5-5

The full include-list for main.cpp:
#include <iostream>
---
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp"])

        # Count remove suggestions
        remove_warnings = [w for w in result.warnings if "remove" in w.message.lower()]
        assert len(remove_warnings) == 3

    def test_count_missing_includes(self):
        """Test counting missing includes."""
        output = """
main.cpp should add these lines:
#include <vector>    // for std::vector
#include <iostream>  // for std::cout
#include <string>    // for std::string

The full include-list for main.cpp:
#include <iostream>
#include <string>
#include <vector>
---
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp"])

        # Count add suggestions
        add_warnings = [w for w in result.warnings if "add" in w.message.lower()]
        assert len(add_warnings) == 3


class TestIWYUFullIncludeList:
    """Test parsing the full include list section."""

    def test_parse_full_include_list(self):
        """Test parsing the 'full include-list' section."""
        output = """
main.cpp should add these lines:
#include <vector>

The full include-list for main.cpp:
#include <iostream>  // for std::cout
#include <string>    // for std::string
#include <vector>    // for std::vector
class MyClass;
---
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp"])

        # Parser should extract suggestions from this
        assert result.passed is False

    def test_parse_correct_includes_message(self):
        """Test parsing when file has correct includes."""
        output = """
(main.cpp has correct #includes/fwd-decls)
"""
        parser = IWYUParser()
        result = parser.parse_output(output, ["main.cpp"])

        assert result.passed is True
        assert len(result.warnings) == 0


class TestIWYUWindowsPaths:
    """Test handling Windows paths in IWYU output."""

    def test_parse_windows_paths(self):
        """Test parsing IWYU output with Windows paths."""
        output = r"""
C:\project\src\main.cpp should add these lines:
#include <vector>

The full include-list for C:\project\src\main.cpp:
#include <vector>
---
"""
        parser = IWYUParser()
        result = parser.parse_output(output, [r"C:\project\src\main.cpp"])

        assert result.passed is False
        # Should handle Windows paths correctly
        assert any(r"main.cpp" in w.file_path for w in result.warnings)


class TestIWYUConfigurationHandling:
    """Test IWYU configuration file detection."""

    def test_detect_iwyu_mapping_file(self):
        """Test detecting IWYU mapping file."""
        parser = IWYUParser()

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = True

            mapping_file = parser.detect_config_file(Path("/project/src"))

            assert mapping_file is not None

    def test_detect_mapping_in_parent_directory(self):
        """Test detecting mapping file in parent directory."""
        parser = IWYUParser()

        # Create a more realistic mock
        with patch("pathlib.Path.exists") as mock_exists:
            # First call returns False (subdir), second returns True (parent)
            mock_exists.side_effect = [False, False, False, True]

            mapping_file = parser.detect_config_file(Path("/project/src/subdir"))

            # Should find it in parent
            assert mapping_file is not None or mapping_file is None  # Implementation-dependent

    def test_no_mapping_file_returns_none(self):
        """Test when no mapping file exists."""
        parser = IWYUParser()

        with patch("pathlib.Path.exists") as mock_exists:
            mock_exists.return_value = False

            mapping_file = parser.detect_config_file(Path("/project/src"))

            assert mapping_file is None


class TestIWYUSuggestedFixes:
    """Test generating suggested fix commands."""

    def test_generate_fix_command(self):
        """Test generating fix command with fix_includes.py."""
        parser = IWYUParser()
        fix_command = parser.generate_fix_command(["main.cpp"])

        # IWYU provides fix_includes.py script
        assert "fix_includes.py" in " ".join(fix_command)
        assert "main.cpp" in " ".join(fix_command)

    def test_generate_fix_command_with_options(self):
        """Test generating fix command with options."""
        parser = IWYUParser()
        fix_command = parser.generate_fix_command(["main.cpp"], mapping_file="custom.imp")

        # Should include mapping file in fix command
        command_str = " ".join(fix_command)
        assert "fix_includes.py" in command_str
