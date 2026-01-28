"""
Test warning and error extraction from compiler output.

Tests extraction of compiler warnings and errors from GCC, Clang, and MSVC
output formats with file/line/column information.
"""

from forge.inspector.build_inspector import BuildInspector


class TestGCCWarningExtraction:
    """Test warning extraction from GCC output."""

    def test_extract_simple_gcc_warning(self):
        """Test extraction of simple GCC warning."""
        output = "file.cpp:10:5: warning: unused variable 'x' [-Wunused-variable]"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].file == "file.cpp"
        assert warnings[0].line == 10
        assert warnings[0].column == 5
        assert "unused variable" in warnings[0].message
        assert warnings[0].warning_type == "unused-variable"

    def test_extract_gcc_warning_with_full_path(self):
        """Test extraction with absolute file path."""
        output = (
            "/home/user/project/src/file.cpp:25:10: warning: comparison between signed and unsigned"
        )

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].file == "/home/user/project/src/file.cpp"
        assert warnings[0].line == 25
        assert warnings[0].column == 10

    def test_extract_multiple_gcc_warnings(self):
        """Test extraction of multiple warnings from output."""
        output = """file.cpp:10:5: warning: unused variable 'x' [-Wunused-variable]
file.cpp:15:8: warning: unused variable 'y' [-Wunused-variable]
file.cpp:20:3: warning: comparison of integer expressions"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 3
        assert warnings[0].line == 10
        assert warnings[1].line == 15
        assert warnings[2].line == 20

    def test_extract_gcc_warning_without_column(self):
        """Test extraction when column number is missing."""
        output = "file.cpp:10: warning: something went wrong"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].file == "file.cpp"
        assert warnings[0].line == 10
        assert warnings[0].column is None

    def test_extract_gcc_multiline_warning(self):
        """Test extraction of multiline warning message."""
        output = """file.cpp:10:5: warning: unused variable 'x' [-Wunused-variable]
    int x = 5;
        ^"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].line == 10
        assert "unused variable" in warnings[0].message


class TestClangWarningExtraction:
    """Test warning extraction from Clang output."""

    def test_extract_simple_clang_warning(self):
        """Test extraction of simple Clang warning."""
        output = "file.cpp:10:5: warning: unused variable 'x' [-Wunused-variable]"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].file == "file.cpp"
        assert warnings[0].line == 10
        assert warnings[0].column == 5

    def test_extract_clang_warning_with_note(self):
        """Test extraction when warning has associated note."""
        output = """file.cpp:10:5: warning: unused variable 'x' [-Wunused-variable]
file.cpp:8:1: note: variable declared here"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].line == 10

    def test_extract_clang_warning_with_fixit(self):
        """Test extraction with fix-it suggestion."""
        output = """file.cpp:10:5: warning: unused variable 'x' [-Wunused-variable]
  int x = 5;
      ^
file.cpp:10:7: note: remove unused variable 'x'"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1


class TestMSVCWarningExtraction:
    """Test warning extraction from MSVC output."""

    def test_extract_simple_msvc_warning(self):
        """Test extraction of simple MSVC warning."""
        output = "file.cpp(10): warning C4101: 'x': unreferenced local variable"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].file == "file.cpp"
        assert warnings[0].line == 10
        assert warnings[0].column is None
        assert "unreferenced local variable" in warnings[0].message
        assert warnings[0].warning_type == "C4101"

    def test_extract_msvc_warning_with_column(self):
        """Test extraction when MSVC provides column."""
        output = "file.cpp(10,5): warning C4101: 'x': unreferenced local variable"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].line == 10
        assert warnings[0].column == 5

    def test_extract_msvc_warning_with_full_path(self):
        """Test extraction with Windows absolute path."""
        output = "C:\\Users\\name\\project\\file.cpp(10): warning C4101: 'x': unreferenced"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].file == "C:\\Users\\name\\project\\file.cpp"

    def test_extract_multiple_msvc_warnings(self):
        """Test extraction of multiple MSVC warnings."""
        output = """file.cpp(10): warning C4101: 'x': unreferenced local variable
file.cpp(15): warning C4189: 'y': local variable is initialized but not referenced
file.cpp(20): warning C4700: uninitialized local variable 'z' used"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 3
        assert warnings[0].warning_type == "C4101"
        assert warnings[1].warning_type == "C4189"
        assert warnings[2].warning_type == "C4700"


class TestGCCErrorExtraction:
    """Test error extraction from GCC output."""

    def test_extract_simple_gcc_error(self):
        """Test extraction of simple GCC error."""
        output = "file.cpp:10:5: error: 'x' was not declared in this scope"

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert len(errors) == 1
        assert errors[0].file == "file.cpp"
        assert errors[0].line == 10
        assert errors[0].column == 5
        assert "not declared" in errors[0].message

    def test_extract_gcc_fatal_error(self):
        """Test extraction of fatal error."""
        output = "file.cpp:1:10: fatal error: iostream: No such file or directory"

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert len(errors) == 1
        assert errors[0].file == "file.cpp"
        assert "No such file or directory" in errors[0].message

    def test_extract_multiple_gcc_errors(self):
        """Test extraction of multiple errors."""
        output = """file.cpp:10:5: error: 'x' was not declared in this scope
file.cpp:15:8: error: expected ';' before 'y'
file.cpp:20:3: error: invalid conversion from 'int' to 'const char*'"""

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert len(errors) == 3
        assert errors[0].line == 10
        assert errors[1].line == 15
        assert errors[2].line == 20


class TestClangErrorExtraction:
    """Test error extraction from Clang output."""

    def test_extract_simple_clang_error(self):
        """Test extraction of simple Clang error."""
        output = "file.cpp:10:5: error: use of undeclared identifier 'x'"

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert len(errors) == 1
        assert errors[0].file == "file.cpp"
        assert errors[0].line == 10

    def test_extract_clang_error_with_multiline(self):
        """Test extraction of multiline error."""
        output = """file.cpp:10:5: error: use of undeclared identifier 'x'
  return x + 5;
         ^"""

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert len(errors) == 1


class TestMSVCErrorExtraction:
    """Test error extraction from MSVC output."""

    def test_extract_simple_msvc_error(self):
        """Test extraction of simple MSVC error."""
        output = "file.cpp(10): error C2065: 'x': undeclared identifier"

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert len(errors) == 1
        assert errors[0].file == "file.cpp"
        assert errors[0].line == 10
        assert errors[0].error_code == "C2065"

    def test_extract_msvc_error_with_column(self):
        """Test extraction when MSVC provides column."""
        output = "file.cpp(10,5): error C2065: 'x': undeclared identifier"

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert len(errors) == 1
        assert errors[0].column == 5

    def test_extract_msvc_fatal_error(self):
        """Test extraction of MSVC fatal error."""
        output = "file.cpp(1): fatal error C1083: Cannot open include file: 'iostream'"

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert len(errors) == 1
        assert errors[0].error_code == "C1083"


class TestWarningWithoutFileInfo:
    """Test warnings without complete file/line information."""

    def test_extract_warning_without_file_info(self):
        """Test extraction of warning without file/line."""
        output = "warning: optimization flag '-O3' is not supported"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].file is None
        assert warnings[0].line is None
        assert "optimization flag" in warnings[0].message

    def test_extract_linker_warning(self):
        """Test extraction of linker warning without file info."""
        output = "ld: warning: ignoring file libfoo.a, missing required architecture x86_64"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].file is None


class TestColoredOutputHandling:
    """Test handling of ANSI color codes in output."""

    def test_extract_warning_with_ansi_colors(self):
        """Test extraction from output with ANSI color codes."""
        output = "\033[1mfile.cpp:10:5: \033[0m\033[0;1;35mwarning: \033[0m\033[1munused variable 'x'\033[0m"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].file == "file.cpp"
        assert warnings[0].line == 10
        assert "unused variable" in warnings[0].message
        assert "\033[" not in warnings[0].message

    def test_extract_error_with_ansi_colors(self):
        """Test error extraction with ANSI codes."""
        output = (
            "\033[1mfile.cpp:10:5: \033[0m\033[0;1;31merror: \033[0m\033[1m'x' not declared\033[0m"
        )

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert len(errors) == 1
        assert "\033[" not in errors[0].message


class TestWarningCounting:
    """Test warning counting functionality."""

    def test_count_warnings(self):
        """Test counting total warnings."""
        output = """file.cpp:10:5: warning: unused variable 'x'
file.cpp:15:8: warning: unused variable 'y'
file.cpp:20:3: warning: comparison warning"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 3

    def test_count_by_type(self):
        """Test counting warnings by type."""
        output = """file.cpp:10:5: warning: unused variable 'x' [-Wunused-variable]
file.cpp:15:8: warning: unused variable 'y' [-Wunused-variable]
file.cpp:20:3: warning: comparison of integers [-Wsign-compare]"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        unused_count = sum(1 for w in warnings if w.warning_type == "unused-variable")
        compare_count = sum(1 for w in warnings if w.warning_type == "sign-compare")

        assert unused_count == 2
        assert compare_count == 1


class TestWarningDeduplication:
    """Test deduplication of identical warnings."""

    def test_deduplicate_identical_warnings(self):
        """Test that identical warnings are deduplicated."""
        output = """file.cpp:10:5: warning: unused variable 'x'
file.cpp:10:5: warning: unused variable 'x'
file.cpp:15:8: warning: unused variable 'y'"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output, deduplicate=True)

        assert len(warnings) == 2

    def test_no_deduplication_when_disabled(self):
        """Test that warnings are not deduplicated when disabled."""
        output = """file.cpp:10:5: warning: unused variable 'x'
file.cpp:10:5: warning: unused variable 'x'
file.cpp:15:8: warning: unused variable 'y'"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output, deduplicate=False)

        assert len(warnings) == 3

    def test_deduplicate_by_file_line_message(self):
        """Test deduplication considers file, line, and message."""
        output = """file.cpp:10:5: warning: unused variable 'x'
file.cpp:10:8: warning: unused variable 'y'
file.cpp:15:5: warning: unused variable 'x'
other.cpp:10:5: warning: unused variable 'x'"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output, deduplicate=True)

        assert len(warnings) == 4


class TestMixedWarningsAndErrors:
    """Test extraction when output contains both warnings and errors."""

    def test_extract_warnings_ignores_errors(self):
        """Test that extract_warnings only returns warnings."""
        output = """file.cpp:10:5: warning: unused variable 'x'
file.cpp:15:8: error: 'y' was not declared
file.cpp:20:3: warning: unused variable 'z'"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 2
        assert warnings[0].line == 10
        assert warnings[1].line == 20

    def test_extract_errors_ignores_warnings(self):
        """Test that extract_errors only returns errors."""
        output = """file.cpp:10:5: warning: unused variable 'x'
file.cpp:15:8: error: 'y' was not declared
file.cpp:20:3: error: expected ';'"""

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert len(errors) == 2


class TestEmptyAndInvalidOutput:
    """Test handling of empty or invalid output."""

    def test_extract_warnings_from_empty_output(self):
        """Test extraction from empty output."""
        inspector = BuildInspector()
        warnings = inspector.extract_warnings("")

        assert warnings == []

    def test_extract_errors_from_empty_output(self):
        """Test extraction from empty output."""
        inspector = BuildInspector()
        errors = inspector.extract_errors("")

        assert errors == []

    def test_extract_from_output_without_warnings(self):
        """Test extraction from output with no warnings."""
        output = """Building CXX object file.o
Linking executable program
Build succeeded"""

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert warnings == []

    def test_extract_from_output_without_errors(self):
        """Test extraction from output with no errors."""
        output = """Building CXX object file.o
Linking executable program
Build succeeded"""

        inspector = BuildInspector()
        errors = inspector.extract_errors(output)

        assert errors == []


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_warning_with_special_characters_in_filename(self):
        """Test extraction from file with special characters."""
        output = "file-name_v2.1.cpp:10:5: warning: unused variable"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert warnings[0].file == "file-name_v2.1.cpp"

    def test_warning_with_spaces_in_windows_path(self):
        """Test extraction from Windows path with spaces."""
        output = "C:\\Program Files\\project\\file.cpp(10): warning C4101: unused"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert "Program Files" in warnings[0].file

    def test_very_long_warning_message(self):
        """Test extraction of very long warning message."""
        long_message = "x" * 500
        output = f"file.cpp:10:5: warning: {long_message}"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert len(warnings[0].message) > 400

    def test_warning_with_unicode_characters(self):
        """Test extraction of warning with unicode characters."""
        output = "file.cpp:10:5: warning: variable 'café' is unused"

        inspector = BuildInspector()
        warnings = inspector.extract_warnings(output)

        assert len(warnings) == 1
        assert "café" in warnings[0].message
