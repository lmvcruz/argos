"""
Test suite for adapters module.

Tests the Verdict adapter functions that integrate Anvil parsers
with the Verdict validation framework. Verifies proper conversion
of parsed output to dictionary format required by Verdict.
"""

from anvil.validators.adapters import (
    validate_black_parser,
    validate_flake8_parser,
    validate_isort_parser,
)


class TestValidateBlackParserAdapter:
    """Tests for validate_black_parser adapter function."""

    def test_validate_black_parser_with_empty_output(self):
        """Verify adapter returns correct structure for no violations."""
        input_text = ""
        result = validate_black_parser(input_text)

        assert isinstance(result, dict)
        assert result["validator"] == "black"
        assert result["total_violations"] == 0
        assert result["files_scanned"] == 0
        assert result["errors"] == 0
        assert result["warnings"] == 0
        assert result["info"] == 0
        assert "BLACK001" in result["by_code"]
        assert result["file_violations"] == []

    def test_validate_black_parser_with_single_file_violation(self):
        """Verify adapter processes single file violations correctly."""
        input_text = (
            "would reformat file.py\n"
            "--- file.py\n"
            "+++ file.py\n"
            "@@ -1,3 +1,4 @@\n"
            " x=1\n"
            "+x = 1\n"
        )
        result = validate_black_parser(input_text)

        assert result["validator"] == "black"
        assert result["total_violations"] == 1
        assert result["files_scanned"] == 1
        assert len(result["file_violations"]) == 1
        assert result["file_violations"][0]["file_path"] == "file.py"

    def test_validate_black_parser_with_multiple_files(self):
        """Verify adapter handles multiple files with violations."""
        input_text = (
            "would reformat file1.py\n"
            "--- file1.py\n"
            "+++ file1.py\n"
            "@@ -1,1 +1,2 @@\n"
            " x = 1\n"
            "would reformat file2.py\n"
            "--- file2.py\n"
            "+++ file2.py\n"
            "@@ -5,3 +5,2 @@\n"
            " y = 2\n"
        )
        result = validate_black_parser(input_text)

        assert result["validator"] == "black"
        assert result["total_violations"] == 2
        assert result["files_scanned"] == 2
        assert len(result["file_violations"]) == 2

    def test_validate_black_parser_returns_all_required_keys(self):
        """Verify all required keys are present in output."""
        input_text = ""
        result = validate_black_parser(input_text)

        required_keys = {
            "validator",
            "total_violations",
            "files_scanned",
            "errors",
            "warnings",
            "info",
            "by_code",
            "file_violations",
        }
        assert set(result.keys()) == required_keys

    def test_validate_black_parser_file_violations_structure(self):
        """Verify file_violations have correct structure."""
        input_text = (
            "would reformat test.py\n" "--- test.py\n" "+++ test.py\n" "@@ -2,2 +2,1 @@\n" " x=1\n"
        )
        result = validate_black_parser(input_text)

        assert len(result["file_violations"]) == 1
        fv = result["file_violations"][0]
        assert "file_path" in fv
        assert "violations" in fv
        assert "validator" in fv
        assert isinstance(fv["violations"], list)

    def test_validate_black_parser_with_multiple_hunks(self):
        """Verify adapter handles multiple hunks in same file."""
        input_text = (
            "would reformat test.py\n"
            "--- test.py\n"
            "+++ test.py\n"
            "@@ -1,3 +1,4 @@\n"
            " x=1\n"
            "@@ -10,2 +11,3 @@\n"
            " y=2\n"
        )
        result = validate_black_parser(input_text)

        assert result["total_violations"] >= 1
        assert len(result["file_violations"]) == 1
        assert result["files_scanned"] == 1


class TestValidateFlake8ParserAdapter:
    """Tests for validate_flake8_parser adapter function."""

    def test_validate_flake8_parser_with_empty_output(self):
        """Verify adapter returns correct structure for no violations."""
        input_text = ""
        result = validate_flake8_parser(input_text)

        assert isinstance(result, dict)
        assert result["validator"] == "flake8"
        assert result["total_violations"] == 0
        assert result["files_scanned"] == 0
        assert result["errors"] == 0
        assert result["warnings"] == 0
        assert result["info"] == 0
        assert result["by_code"] == {}
        assert result["file_violations"] == []

    def test_validate_flake8_parser_with_single_violation(self):
        """Verify adapter processes single violation correctly."""
        input_text = "file.py:1:1: E302 expected 2 blank lines, found 0\n"
        result = validate_flake8_parser(input_text)

        assert result["validator"] == "flake8"
        assert result["total_violations"] == 1
        assert result["files_scanned"] == 1
        assert len(result["file_violations"]) == 1
        assert result["file_violations"][0]["file_path"] == "file.py"

    def test_validate_flake8_parser_with_multiple_violations_same_file(self):
        """Verify adapter handles multiple violations in same file."""
        input_text = (
            "test.py:1:1: E302 expected 2 blank lines, found 0\n"
            "test.py:5:10: W291 trailing whitespace\n"
            "test.py:8:1: E501 line too long (120 > 100 characters)\n"
        )
        result = validate_flake8_parser(input_text)

        assert result["validator"] == "flake8"
        assert result["total_violations"] == 3
        assert result["files_scanned"] == 1
        assert len(result["file_violations"]) == 1

    def test_validate_flake8_parser_with_multiple_files(self):
        """Verify adapter handles violations across multiple files."""
        input_text = (
            "file1.py:1:1: E302 expected 2 blank lines, found 0\n"
            "file2.py:5:10: W291 trailing whitespace\n"
            "file3.py:8:1: E501 line too long\n"
        )
        result = validate_flake8_parser(input_text)

        assert result["validator"] == "flake8"
        assert result["total_violations"] == 3
        assert result["files_scanned"] == 3
        assert len(result["file_violations"]) == 3

    def test_validate_flake8_parser_returns_all_required_keys(self):
        """Verify all required keys are present in output."""
        input_text = ""
        result = validate_flake8_parser(input_text)

        required_keys = {
            "validator",
            "total_violations",
            "files_scanned",
            "errors",
            "warnings",
            "info",
            "by_code",
            "file_violations",
        }
        assert set(result.keys()) == required_keys

    def test_validate_flake8_parser_file_violations_structure(self):
        """Verify file_violations have correct structure."""
        input_text = "test.py:10:5: E501 line too long\n"
        result = validate_flake8_parser(input_text)

        assert len(result["file_violations"]) == 1
        fv = result["file_violations"][0]
        assert "file_path" in fv
        assert "violations" in fv
        assert "validator" in fv

    def test_validate_flake8_parser_code_grouping(self):
        """Verify violations are grouped by code."""
        input_text = (
            "file.py:1:1: E302 expected 2 blank lines, found 0\n"
            "file.py:5:10: E302 expected 2 blank lines, found 0\n"
            "file.py:8:1: W291 trailing whitespace\n"
        )
        result = validate_flake8_parser(input_text)

        assert "E302" in result["by_code"]
        assert "W291" in result["by_code"]


class TestValidateIsortParserAdapter:
    """Tests for validate_isort_parser adapter function."""

    def test_validate_isort_parser_with_empty_output(self):
        """Verify adapter returns correct structure for no violations."""
        input_text = ""
        result = validate_isort_parser(input_text)

        assert isinstance(result, dict)
        assert result["validator"] == "isort"
        assert result["total_violations"] == 0
        assert result["files_scanned"] == 0
        assert result["errors"] == 0
        assert result["warnings"] == 0
        assert result["info"] == 0
        assert "ISORT001" in result["by_code"]
        assert result["file_violations"] == []

    def test_validate_isort_parser_with_single_file_violation(self):
        """Verify adapter processes single file violation correctly."""
        input_text = "ERROR: D:\\project\\file.py (import)\\n"
        result = validate_isort_parser(input_text)

        assert result["validator"] == "isort"
        assert result["total_violations"] == 1
        assert result["files_scanned"] == 1
        assert len(result["file_violations"]) == 1

    def test_validate_isort_parser_with_multiple_files(self):
        """Verify adapter handles multiple files with violations."""
        input_text = (
            "ERROR: file1.py (import)\\n"
            "ERROR: file2.py (import)\\n"
            "ERROR: file3.py (import)\\n"
        )
        result = validate_isort_parser(input_text)

        assert result["validator"] == "isort"
        assert result["total_violations"] >= 1

    def test_validate_isort_parser_returns_all_required_keys(self):
        """Verify all required keys are present in output."""
        input_text = ""
        result = validate_isort_parser(input_text)

        required_keys = {
            "validator",
            "total_violations",
            "files_scanned",
            "errors",
            "warnings",
            "info",
            "by_code",
            "file_violations",
        }
        assert set(result.keys()) == required_keys

    def test_validate_isort_parser_file_violations_structure(self):
        """Verify file_violations have correct structure."""
        input_text = "ERROR: test.py (import)\\n"
        result = validate_isort_parser(input_text)

        fv_list = result["file_violations"]
        if len(fv_list) > 0:
            fv = fv_list[0]
            assert "file_path" in fv
            assert "violations" in fv
            assert "validator" in fv


class TestAdaptersIntegration:
    """Integration tests verifying adapters work together correctly."""

    def test_all_adapters_return_consistent_structure(self):
        """Verify all adapters return same top-level structure."""
        adapters = [
            validate_black_parser,
            validate_flake8_parser,
            validate_isort_parser,
        ]
        expected_keys = {
            "validator",
            "total_violations",
            "files_scanned",
            "errors",
            "warnings",
            "info",
            "by_code",
            "file_violations",
        }

        for adapter in adapters:
            result = adapter("")
            assert set(result.keys()) == expected_keys

    def test_all_adapters_handle_empty_input(self):
        """Verify all adapters handle empty input gracefully."""
        adapters = [
            validate_black_parser,
            validate_flake8_parser,
            validate_isort_parser,
        ]

        for adapter in adapters:
            result = adapter("")
            assert result["total_violations"] == 0
            assert result["file_violations"] == []

    def test_adapter_output_serializable(self):
        """Verify adapter output is JSON serializable."""
        import json

        adapters = [
            validate_black_parser,
            validate_flake8_parser,
            validate_isort_parser,
        ]

        for adapter in adapters:
            result = adapter("")
            # Should not raise exception
            json.dumps(result)
