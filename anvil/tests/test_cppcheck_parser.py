"""
Test cppcheck parser for C++ static analysis.

Tests the parser for cppcheck XML output with various issue types including
bugs, warnings, style issues, performance issues, and portability concerns.
"""

import subprocess
from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from anvil.parsers.cppcheck_parser import CppcheckParser


class TestCppcheckXMLParsing:
    """Test cppcheck XML version 2 format parsing."""

    def test_parse_xml_with_no_errors(self):
        """Test parsing XML output with no errors."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
</errors>
</results>"""

        result = CppcheckParser.parse_xml(xml_output, [Path("src/main.cpp")], {})

        assert result.passed is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_parse_error_severity_issue(self):
        """Test parsing error severity issue."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="nullPointer" severity="error" msg="Null pointer dereference" verbose="Possible null pointer dereference: ptr">
<location file="src/main.cpp" line="42" column="5"/>
</error>
</errors>
</results>"""

        result = CppcheckParser.parse_xml(xml_output, [Path("src/main.cpp")], {})

        assert result.passed is False
        assert len(result.errors) == 1
        assert result.errors[0].severity == "error"
        assert "nullPointer" in result.errors[0].rule_name
        assert "Null pointer dereference" in result.errors[0].message

    def test_parse_warning_severity_issue(self):
        """Test parsing warning severity issue."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="uninitvar" severity="warning" msg="Uninitialized variable: x">
<location file="src/main.cpp" line="10" column="9"/>
</error>
</errors>
</results>"""

        result = CppcheckParser.parse_xml(xml_output, [Path("src/main.cpp")], {})

        assert result.passed is False
        assert len(result.warnings) == 1
        assert result.warnings[0].severity == "warning"
        assert "uninitvar" in result.warnings[0].rule_name

    def test_parse_style_issue(self):
        """Test parsing style severity issue."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="unusedVariable" severity="style" msg="Unused variable: temp">
<location file="src/main.cpp" line="15"/>
</error>
</errors>
</results>"""

        result = CppcheckParser.parse_xml(xml_output, [Path("src/main.cpp")], {})

        assert len(result.warnings) == 1
        assert result.warnings[0].severity == "warning"
        assert "unusedVariable" in result.warnings[0].rule_name

    def test_parse_performance_issue(self):
        """Test parsing performance severity issue."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="passedByValue" severity="performance" msg="Function parameter should be passed by const reference">
<location file="src/main.cpp" line="20"/>
</error>
</errors>
</results>"""

        result = CppcheckParser.parse_xml(xml_output, [Path("src/main.cpp")], {})

        assert len(result.warnings) == 1
        assert "passedByValue" in result.warnings[0].rule_name

    def test_parse_portability_issue(self):
        """Test parsing portability severity issue."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="invalidPointerCast" severity="portability" msg="Casting between incompatible pointer types">
<location file="src/main.cpp" line="30"/>
</error>
</errors>
</results>"""

        result = CppcheckParser.parse_xml(xml_output, [Path("src/main.cpp")], {})

        assert len(result.warnings) == 1
        assert "invalidPointerCast" in result.warnings[0].rule_name

    def test_parse_information_message(self):
        """Test parsing information severity message."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="missingInclude" severity="information" msg="Include file not found">
<location file="src/main.cpp" line="5"/>
</error>
</errors>
</results>"""

        result = CppcheckParser.parse_xml(xml_output, [Path("src/main.cpp")], {})

        assert len(result.warnings) == 1
        assert result.warnings[0].severity == "info"

    def test_extract_cwe_id(self):
        """Test extraction of CWE ID when available."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="bufferAccessOutOfBounds" severity="error" msg="Buffer overflow" cwe="119">
<location file="src/main.cpp" line="50"/>
</error>
</errors>
</results>"""

        result = CppcheckParser.parse_xml(xml_output, [Path("src/main.cpp")], {})

        assert len(result.errors) == 1
        assert result.errors[0].error_code == "CWE-119"

    def test_parse_inconclusive_results(self):
        """Test parsing inconclusive results."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="memleak" severity="error" msg="Memory leak: ptr" inconclusive="true">
<location file="src/main.cpp" line="60"/>
</error>
</errors>
</results>"""

        result = CppcheckParser.parse_xml(xml_output, [Path("src/main.cpp")], {})

        assert len(result.errors) == 1
        assert "(inconclusive)" in result.errors[0].message.lower()

    def test_parse_multiple_locations(self):
        """Test parsing error with multiple locations."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="uninitvar" severity="warning" msg="Uninitialized variable: x">
<location file="src/main.cpp" line="10"/>
<location file="src/main.cpp" line="15" info="x is used here"/>
</error>
</errors>
</results>"""

        result = CppcheckParser.parse_xml(xml_output, [Path("src/main.cpp")], {})

        assert len(result.warnings) == 1
        # Should use the first location
        assert result.warnings[0].line_number == 10


class TestCppcheckCommandBuilding:
    """Test building cppcheck commands with various options."""

    def test_build_command_default_options(self):
        """Test building command with default options."""
        files = [Path("src/main.cpp")]
        config = {}

        command = CppcheckParser.build_command(files, config)

        assert command[0] == "cppcheck"
        assert "--xml" in command
        assert "--xml-version=2" in command
        # Files should be in command
        file_paths = [str(Path(arg)) for arg in command]
        assert str(Path("src/main.cpp")) in file_paths

    def test_build_command_with_enable_categories(self):
        """Test building command with enabled check categories."""
        files = [Path("src/main.cpp")]
        config = {"enable": ["warning", "style", "performance"]}

        command = CppcheckParser.build_command(files, config)

        assert any("--enable=" in arg for arg in command)
        enable_arg = [arg for arg in command if "--enable=" in arg][0]
        assert "warning" in enable_arg
        assert "style" in enable_arg
        assert "performance" in enable_arg

    def test_build_command_with_suppressions(self):
        """Test building command with suppressions."""
        files = [Path("src/main.cpp")]
        config = {"suppress": ["unusedFunction", "missingInclude"]}

        command = CppcheckParser.build_command(files, config)

        suppress_args = [arg for arg in command if arg.startswith("--suppress=")]
        assert len(suppress_args) == 2

    def test_build_command_with_std_option(self):
        """Test building command with C++ standard."""
        files = [Path("src/main.cpp")]
        config = {"std": "c++17"}

        command = CppcheckParser.build_command(files, config)

        assert "--std=c++17" in command

    def test_build_command_with_platform(self):
        """Test building command with platform option."""
        files = [Path("src/main.cpp")]
        config = {"platform": "unix64"}

        command = CppcheckParser.build_command(files, config)

        assert "--platform=unix64" in command

    def test_build_command_with_includes(self):
        """Test building command with include paths."""
        files = [Path("src/main.cpp")]
        config = {"includes": ["include/", "external/headers/"]}

        command = CppcheckParser.build_command(files, config)

        include_args = [arg for arg in command if arg.startswith("-I")]
        assert len(include_args) == 2

    def test_build_command_with_defines(self):
        """Test building command with preprocessor defines."""
        files = [Path("src/main.cpp")]
        config = {"defines": ["DEBUG", "VERSION=2"]}

        command = CppcheckParser.build_command(files, config)

        define_args = [arg for arg in command if arg.startswith("-D")]
        assert len(define_args) == 2

    def test_build_command_with_inconclusive(self):
        """Test building command with inconclusive checks."""
        files = [Path("src/main.cpp")]
        config = {"inconclusive": True}

        command = CppcheckParser.build_command(files, config)

        assert "--inconclusive" in command

    def test_build_command_with_multiple_files(self):
        """Test building command with multiple files."""
        files = [Path("src/main.cpp"), Path("src/helper.cpp"), Path("include/utils.h")]
        config = {}

        command = CppcheckParser.build_command(files, config)

        file_paths = [str(Path(arg)) for arg in command]
        assert str(Path("src/main.cpp")) in file_paths
        assert str(Path("src/helper.cpp")) in file_paths
        assert str(Path("include/utils.h")) in file_paths


class TestCppcheckErrorHandling:
    """Test error handling for cppcheck execution."""

    def test_error_when_cppcheck_not_installed(self, mocker: MockerFixture):
        """Test error handling when cppcheck is not installed."""
        mocker.patch(
            "anvil.parsers.cppcheck_parser.subprocess.run",
            side_effect=FileNotFoundError("cppcheck not found"),
        )

        result = CppcheckParser.run_and_parse(
            [Path("src/main.cpp")],
            {},
        )

        assert result.passed is False
        assert len(result.errors) > 0
        assert any("not installed" in err.message.lower() for err in result.errors)

    def test_timeout_handling(self, mocker: MockerFixture):
        """Test timeout handling for long-running cppcheck."""
        mocker.patch(
            "anvil.parsers.cppcheck_parser.subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="cppcheck", timeout=60),
        )

        config = {"timeout": 60}
        result = CppcheckParser.run_and_parse(
            [Path("src/main.cpp")],
            config,
        )

        assert result.passed is False
        assert len(result.errors) > 0
        assert any("timed out" in err.message.lower() for err in result.errors)

    def test_parse_with_invalid_xml(self):
        """Test parsing invalid XML output."""
        invalid_xml = """<?xml version="1.0"?>
<results version="2">
<errors>
<error id="test" [invalid xml structure
</results>"""

        result = CppcheckParser.parse_xml(invalid_xml, [Path("src/main.cpp")], {})

        assert result.passed is False
        assert len(result.errors) > 0
        assert any("xml" in err.message.lower() for err in result.errors)


class TestCppcheckVersionDetection:
    """Test cppcheck version detection."""

    def test_version_detection(self, mocker: MockerFixture):
        """Test detection of cppcheck version."""
        mock_run = mocker.patch("subprocess.run")
        mock_run.return_value.stdout = "Cppcheck 2.10\n"
        mock_run.return_value.returncode = 0

        version = CppcheckParser.get_version()

        assert version == "2.10"

    def test_version_detection_failure(self, mocker: MockerFixture):
        """Test handling of version detection failure."""
        mocker.patch(
            "subprocess.run",
            side_effect=FileNotFoundError(),
        )

        version = CppcheckParser.get_version()

        assert version is None


class TestCppcheckIntegrationWithFixtures:
    """Integration tests with real cppcheck (skipped if not installed)."""

    @pytest.mark.skipif(not CppcheckParser.is_installed(), reason="cppcheck not installed")
    def test_cppcheck_on_clean_cpp_code(self):
        """Test cppcheck on clean C++ code."""
        # This would use fixtures/cpp/good_code.cpp
        pytest.skip("Integration test requires cppcheck and fixture setup")

    @pytest.mark.skipif(not CppcheckParser.is_installed(), reason="cppcheck not installed")
    def test_cppcheck_on_code_with_bugs(self):
        """Test cppcheck on C++ code with bugs."""
        # This would use fixtures/cpp/bad_code_static_analysis.cpp
        pytest.skip("Integration test requires cppcheck and fixture setup")


class TestCppcheckGroupingAndFiltering:
    """Test grouping and filtering of cppcheck results."""

    def test_group_errors_by_id(self):
        """Test grouping errors by error ID."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="nullPointer" severity="error" msg="Null pointer dereference">
<location file="src/main.cpp" line="10"/>
</error>
<error id="nullPointer" severity="error" msg="Another null pointer">
<location file="src/helper.cpp" line="20"/>
</error>
<error id="memleak" severity="error" msg="Memory leak">
<location file="src/main.cpp" line="30"/>
</error>
</errors>
</results>"""

        grouped = CppcheckParser.group_by_error_id(xml_output)

        assert "nullPointer" in grouped
        assert len(grouped["nullPointer"]) == 2
        assert "memleak" in grouped
        assert len(grouped["memleak"]) == 1

    def test_group_errors_by_file(self):
        """Test grouping errors by file."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="nullPointer" severity="error" msg="Error 1">
<location file="src/main.cpp" line="10"/>
</error>
<error id="uninitvar" severity="warning" msg="Error 2">
<location file="src/main.cpp" line="20"/>
</error>
<error id="memleak" severity="error" msg="Error 3">
<location file="src/helper.cpp" line="30"/>
</error>
</errors>
</results>"""

        grouped = CppcheckParser.group_by_file(xml_output)

        assert str(Path("src/main.cpp")) in grouped
        assert len(grouped[str(Path("src/main.cpp"))]) == 2
        assert str(Path("src/helper.cpp")) in grouped
        assert len(grouped[str(Path("src/helper.cpp"))]) == 1

    def test_filter_by_severity(self):
        """Test filtering errors by severity."""
        xml_output = """<?xml version="1.0" encoding="UTF-8"?>
<results version="2">
<cppcheck version="2.10"/>
<errors>
<error id="error1" severity="error" msg="Error message">
<location file="src/main.cpp" line="10"/>
</error>
<error id="warning1" severity="warning" msg="Warning message">
<location file="src/main.cpp" line="20"/>
</error>
<error id="style1" severity="style" msg="Style message">
<location file="src/main.cpp" line="30"/>
</error>
</errors>
</results>"""

        errors_only = CppcheckParser.filter_by_severity(xml_output, "error")
        warnings_only = CppcheckParser.filter_by_severity(xml_output, "warning")

        assert len(errors_only) == 1
        assert errors_only[0]["id"] == "error1"
        assert len(warnings_only) == 1
        assert warnings_only[0]["id"] == "warning1"


class TestCppcheckConfigurationHandling:
    """Test cppcheck configuration file handling."""

    def test_detect_cppcheck_suppressions_file(self, tmp_path):
        """Test detection of cppcheck suppressions file."""
        suppressions_file = tmp_path / "suppressions.txt"
        suppressions_file.write_text("unusedFunction\nmissingInclude\n")

        result = CppcheckParser.find_suppressions_file(tmp_path)

        assert result == suppressions_file

    def test_detect_suppressions_in_parent_directory(self, tmp_path):
        """Test detection of suppressions file in parent directory."""
        suppressions_file = tmp_path / "suppressions.txt"
        suppressions_file.write_text("test")

        subdir = tmp_path / "src"
        subdir.mkdir()

        result = CppcheckParser.find_suppressions_file(subdir)

        assert result == suppressions_file

    def test_no_suppressions_file_returns_none(self, tmp_path):
        """Test that missing suppressions file returns None."""
        result = CppcheckParser.find_suppressions_file(tmp_path)

        assert result is None
