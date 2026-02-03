"""
Tests for LintParser class.

This module tests the LintParser that parses flake8, black, and isort outputs
into structured lint data.
"""

from pathlib import Path

from anvil.parsers.lint_parser import LintParser


class TestLintParserFlake8:
    """Test parsing flake8 output."""

    def test_parse_flake8_output_with_single_error(self):
        """Test parsing single flake8 E-series error."""
        parser = LintParser()
        output = "test.py:10:5: E501 line too long (105 > 100 characters)"

        result = parser.parse_flake8_output(output)

        assert result.validator == "flake8"
        assert result.total_violations == 1
        assert result.files_scanned == 1
        assert result.errors == 1
        assert result.warnings == 0
        assert result.info == 0
        assert "E501" in result.by_code
        assert result.by_code["E501"] == 1
        assert len(result.file_violations) == 1

        file_viol = result.file_violations[0]
        assert file_viol.file_path == "test.py"
        assert file_viol.validator == "flake8"
        assert len(file_viol.violations) == 1

        viol = file_viol.violations[0]
        assert viol["line_number"] == 10
        assert viol["column_number"] == 5
        assert viol["severity"] == "ERROR"
        assert viol["code"] == "E501"
        assert "line too long" in viol["message"]

    def test_parse_flake8_output_with_multiple_files(self):
        """Test parsing flake8 output with multiple files."""
        parser = LintParser()
        output = """file1.py:10:5: E501 line too long
file2.py:20:10: W503 line break before binary operator
file1.py:15:1: F401 'os' imported but unused"""

        result = parser.parse_flake8_output(output)

        assert result.validator == "flake8"
        assert result.total_violations == 3
        assert result.files_scanned == 2
        assert result.errors == 2  # E501 and F401 are errors
        assert result.warnings == 1  # W503 is warning
        assert result.by_code["E501"] == 1
        assert result.by_code["W503"] == 1
        assert result.by_code["F401"] == 1

    def test_parse_flake8_output_with_project_root(self):
        """Test parsing with project_root makes paths relative."""
        parser = LintParser()
        project_root = Path("/home/user/project")
        output = "/home/user/project/src/file.py:10:5: E501 line too long"

        result = parser.parse_flake8_output(output, project_root=project_root)

        assert result.files_scanned == 1
        file_viol = result.file_violations[0]
        # Path separators differ on Windows vs Unix - check both components
        assert "src" in file_viol.file_path and "file.py" in file_viol.file_path

    def test_parse_flake8_output_with_empty_output(self):
        """Test parsing empty flake8 output."""
        parser = LintParser()
        output = ""

        result = parser.parse_flake8_output(output)

        assert result.validator == "flake8"
        assert result.total_violations == 0
        assert result.files_scanned == 0
        assert result.errors == 0
        assert result.warnings == 0
        assert result.info == 0
        assert len(result.file_violations) == 0

    def test_parse_flake8_output_with_whitespace_lines(self):
        """Test parsing flake8 output with blank lines."""
        parser = LintParser()
        output = """

file.py:10:5: E501 line too long

"""

        result = parser.parse_flake8_output(output)

        assert result.total_violations == 1
        assert result.files_scanned == 1

    def test_parse_flake8_output_with_various_severity_codes(self):
        """Test parsing different severity codes."""
        parser = LintParser()
        output = """file.py:1:1: E501 error
file.py:2:1: W503 warning
file.py:3:1: F401 error
file.py:4:1: C901 warning
file.py:5:1: N806 warning
file.py:6:1: D100 info
file.py:7:1: I001 info
file.py:8:1: B008 warning
file.py:9:1: S101 warning
file.py:10:1: T001 info"""

        result = parser.parse_flake8_output(output)

        assert result.total_violations == 10
        assert result.errors == 2  # E, F
        assert result.warnings == 5  # W, C, N, B, S
        assert result.info == 3  # D, I, T

    def test_parse_flake8_output_with_malformed_lines(self):
        """Test parsing flake8 output with malformed lines."""
        parser = LintParser()
        output = """file.py:10:5: E501 line too long
This is not a valid flake8 line
file.py:20:1: W503 warning"""

        result = parser.parse_flake8_output(output)

        # Only valid lines should be parsed
        assert result.total_violations == 2
        assert result.files_scanned == 1


class TestLintParserBlack:
    """Test parsing black output."""

    def test_parse_black_output_with_single_file(self):
        """Test parsing black output with one file needing reformatting."""
        parser = LintParser()
        output = "would reformat test.py"

        result = parser.parse_black_output(output)

        assert result.validator == "black"
        assert result.total_violations == 1
        assert result.files_scanned == 1
        assert result.errors == 0
        assert result.warnings == 1
        assert result.info == 0
        assert result.by_code["BLACK001"] == 1
        assert len(result.file_violations) == 1

        file_viol = result.file_violations[0]
        assert file_viol.file_path == "test.py"
        assert file_viol.validator == "black"
        assert len(file_viol.violations) == 1

        viol = file_viol.violations[0]
        assert viol["line_number"] == 1
        assert viol["column_number"] is None
        assert viol["severity"] == "WARNING"
        assert viol["code"] == "BLACK001"
        assert "would be reformatted" in viol["message"]

    def test_parse_black_output_with_multiple_files(self):
        """Test parsing black output with multiple files."""
        parser = LintParser()
        output = """would reformat file1.py
would reformat src/file2.py
would reformat tests/test_file.py"""

        result = parser.parse_black_output(output)

        assert result.validator == "black"
        assert result.total_violations == 3
        assert result.files_scanned == 3
        assert result.warnings == 3
        assert result.by_code["BLACK001"] == 3

    def test_parse_black_output_with_project_root(self):
        """Test parsing black output with project_root."""
        parser = LintParser()
        project_root = Path("/home/user/project")
        output = "would reformat /home/user/project/src/file.py"

        result = parser.parse_black_output(output, project_root=project_root)

        assert result.files_scanned == 1
        file_viol = result.file_violations[0]
        # Path separators may differ on Windows vs Unix
        assert file_viol.file_path in ("src/file.py", "src\\file.py")

    def test_parse_black_output_with_empty_output(self):
        """Test parsing empty black output."""
        parser = LintParser()
        output = ""

        result = parser.parse_black_output(output)

        assert result.validator == "black"
        assert result.total_violations == 0
        assert result.files_scanned == 0
        assert result.warnings == 0

    def test_parse_black_output_with_no_changes_needed(self):
        """Test parsing black output with no reformatting needed."""
        parser = LintParser()
        output = "All done! ✨ 🍰 ✨\n3 files would be left unchanged."

        result = parser.parse_black_output(output)

        assert result.total_violations == 0
        assert result.files_scanned == 0

    def test_parse_black_output_with_whitespace_lines(self):
        """Test parsing black output with blank lines."""
        parser = LintParser()
        output = """

would reformat file.py

"""

        result = parser.parse_black_output(output)

        assert result.total_violations == 1
        assert result.files_scanned == 1


class TestLintParserIsort:
    """Test parsing isort output."""

    def test_parse_isort_output_with_single_file(self):
        """Test parsing isort output with one file needing sorting."""
        parser = LintParser()
        output = "ERROR: test.py Imports are incorrectly sorted and/or formatted."

        result = parser.parse_isort_output(output)

        assert result.validator == "isort"
        assert result.total_violations == 1
        assert result.files_scanned == 1
        assert result.errors == 0
        assert result.warnings == 1
        assert result.info == 0
        assert result.by_code["ISORT001"] == 1
        assert len(result.file_violations) == 1

        file_viol = result.file_violations[0]
        assert file_viol.file_path == "test.py"
        assert file_viol.validator == "isort"
        assert len(file_viol.violations) == 1

        viol = file_viol.violations[0]
        assert viol["line_number"] == 1
        assert viol["column_number"] is None
        assert viol["severity"] == "WARNING"
        assert viol["code"] == "ISORT001"
        assert "Imports are incorrectly sorted" in viol["message"]

    def test_parse_isort_output_with_multiple_files(self):
        """Test parsing isort output with multiple files."""
        parser = LintParser()
        output = """ERROR: file1.py Imports are incorrectly sorted.
ERROR: src/file2.py Imports are incorrectly sorted and/or formatted.
ERROR: tests/test_file.py Imports need to be sorted."""

        result = parser.parse_isort_output(output)

        assert result.validator == "isort"
        assert result.total_violations == 3
        assert result.files_scanned == 3
        assert result.warnings == 3
        assert result.by_code["ISORT001"] == 3

    def test_parse_isort_output_with_project_root(self):
        """Test parsing isort output with project_root."""
        parser = LintParser()
        project_root = Path("/home/user/project")
        output = "ERROR: /home/user/project/src/file.py Imports are incorrectly sorted."

        result = parser.parse_isort_output(output, project_root=project_root)

        assert result.files_scanned == 1
        file_viol = result.file_violations[0]
        # Path separators may differ on Windows vs Unix
        assert file_viol.file_path in ("src/file.py", "src\\file.py")

    def test_parse_isort_output_with_empty_output(self):
        """Test parsing empty isort output."""
        parser = LintParser()
        output = ""

        result = parser.parse_isort_output(output)

        assert result.validator == "isort"
        assert result.total_violations == 0
        assert result.files_scanned == 0
        assert result.warnings == 0

    def test_parse_isort_output_with_non_error_lines(self):
        """Test parsing isort output with non-ERROR lines."""
        parser = LintParser()
        output = """Checking imports...
ERROR: file.py Imports are incorrectly sorted.
All done!"""

        result = parser.parse_isort_output(output)

        # Only ERROR lines should be parsed
        assert result.total_violations == 1
        assert result.files_scanned == 1

    def test_parse_isort_output_with_whitespace_lines(self):
        """Test parsing isort output with blank lines."""
        parser = LintParser()
        output = """

ERROR: file.py Imports are incorrectly sorted.

"""

        result = parser.parse_isort_output(output)

        assert result.total_violations == 1
        assert result.files_scanned == 1


class TestLintParserUtilityMethods:
    """Test LintParser utility methods."""

    def test_calculate_quality_score_perfect(self):
        """Test quality score calculation with no violations."""
        parser = LintParser()

        score = parser.calculate_quality_score(0, 100)

        assert score == 100.0

    def test_calculate_quality_score_with_violations(self):
        """Test quality score calculation with violations."""
        parser = LintParser()

        score = parser.calculate_quality_score(50, 100)

        assert score == 50.0

    def test_calculate_quality_score_zero_lines(self):
        """Test quality score with zero lines."""
        parser = LintParser()

        score = parser.calculate_quality_score(0, 0)

        assert score == 100.0

    def test_calculate_quality_score_capped_at_zero(self):
        """Test quality score is capped at 0."""
        parser = LintParser()

        score = parser.calculate_quality_score(200, 100)

        assert score == 0.0

    def test_aggregate_by_severity(self):
        """Test aggregating violations by severity."""
        parser = LintParser()
        violations = [
            {"severity": "ERROR", "code": "E501"},
            {"severity": "WARNING", "code": "W503"},
            {"severity": "ERROR", "code": "F401"},
            {"severity": "INFO", "code": "D100"},
        ]

        result = parser.aggregate_by_severity(violations)

        assert result["ERROR"] == 2
        assert result["WARNING"] == 1
        assert result["INFO"] == 1

    def test_aggregate_by_severity_empty_list(self):
        """Test aggregating empty violations list."""
        parser = LintParser()
        violations = []

        result = parser.aggregate_by_severity(violations)

        assert result == {}

    def test_find_most_common_violation(self):
        """Test finding most common violation code."""
        parser = LintParser()
        violations = [
            {"code": "E501"},
            {"code": "W503"},
            {"code": "E501"},
            {"code": "E501"},
            {"code": "F401"},
        ]

        result = parser.find_most_common_violation(violations)

        assert result == "E501"

    def test_find_most_common_violation_empty_list(self):
        """Test finding most common violation with empty list."""
        parser = LintParser()
        violations = []

        result = parser.find_most_common_violation(violations)

        assert result is None

    def test_find_most_common_violation_single_item(self):
        """Test finding most common violation with single item."""
        parser = LintParser()
        violations = [{"code": "E501"}]

        result = parser.find_most_common_violation(violations)

        assert result == "E501"

    def test_filter_by_severity_errors(self):
        """Test filtering violations by ERROR severity."""
        parser = LintParser()
        violations = [
            {"severity": "ERROR", "code": "E501"},
            {"severity": "WARNING", "code": "W503"},
            {"severity": "ERROR", "code": "F401"},
        ]

        result = parser.filter_by_severity(violations, "ERROR")

        assert len(result) == 2
        assert all(v["severity"] == "ERROR" for v in result)

    def test_filter_by_severity_warnings(self):
        """Test filtering violations by WARNING severity."""
        parser = LintParser()
        violations = [
            {"severity": "ERROR", "code": "E501"},
            {"severity": "WARNING", "code": "W503"},
            {"severity": "WARNING", "code": "B008"},
        ]

        result = parser.filter_by_severity(violations, "WARNING")

        assert len(result) == 2
        assert all(v["severity"] == "WARNING" for v in result)

    def test_filter_by_severity_info(self):
        """Test filtering violations by INFO severity."""
        parser = LintParser()
        violations = [
            {"severity": "ERROR", "code": "E501"},
            {"severity": "INFO", "code": "D100"},
        ]

        result = parser.filter_by_severity(violations, "INFO")

        assert len(result) == 1
        assert result[0]["severity"] == "INFO"

    def test_filter_by_severity_empty_result(self):
        """Test filtering when no violations match."""
        parser = LintParser()
        violations = [
            {"severity": "ERROR", "code": "E501"},
            {"severity": "WARNING", "code": "W503"},
        ]

        result = parser.filter_by_severity(violations, "INFO")

        assert len(result) == 0

    def test_filter_by_severity_empty_input(self):
        """Test filtering empty violations list."""
        parser = LintParser()
        violations = []

        result = parser.filter_by_severity(violations, "ERROR")

        assert len(result) == 0
