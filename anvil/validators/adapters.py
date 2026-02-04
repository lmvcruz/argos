"""
Verdict adapters for Anvil validators.

This module provides adapter functions that implement the Verdict interface
(str -> dict) for testing Anvil's parser components.

Each adapter:
1. Takes raw tool output as input (string)
2. Calls the appropriate Anvil parser
3. Converts the LintData result to a dictionary
4. Returns the dictionary for Verdict validation

Interface Contract:
    All adapters must follow: def adapter(input_text: str) -> dict
"""

from pathlib import Path

from anvil.parsers.lint_parser import LintParser


def validate_black_parser(input_text: str) -> dict:
    """
    Adapter for black parser validation.

    Args:
        input_text: Raw black --check output

    Returns:
        Dictionary with parsed lint data for validation
    """
    parser = LintParser()
    lint_data = parser.parse_black_output(input_text, Path("."))

    return {
        "validator": lint_data.validator,
        "total_violations": lint_data.total_violations,
        "files_scanned": lint_data.files_scanned,
        "errors": lint_data.errors,
        "warnings": lint_data.warnings,
        "info": lint_data.info,
        "by_code": lint_data.by_code,
        "file_violations": [
            {
                "file_path": fv.file_path,
                "violations": fv.violations,
                "validator": fv.validator,
            }
            for fv in lint_data.file_violations
        ],
    }


def validate_flake8_parser(input_text: str) -> dict:
    """
    Adapter for flake8 parser validation.

    Args:
        input_text: Raw flake8 output

    Returns:
        Dictionary with parsed lint data for validation
    """
    parser = LintParser()
    lint_data = parser.parse_flake8_output(input_text, Path("."))

    return {
        "validator": lint_data.validator,
        "total_violations": lint_data.total_violations,
        "files_scanned": lint_data.files_scanned,
        "errors": lint_data.errors,
        "warnings": lint_data.warnings,
        "info": lint_data.info,
        "by_code": lint_data.by_code,
        "file_violations": [
            {
                "file_path": fv.file_path,
                "violations": fv.violations,
                "validator": fv.validator,
            }
            for fv in lint_data.file_violations
        ],
    }


def validate_isort_parser(input_text: str) -> dict:
    """
    Adapter for isort parser validation.

    Args:
        input_text: Raw isort --check-only output

    Returns:
        Dictionary with parsed lint data for validation
    """
    parser = LintParser()
    lint_data = parser.parse_isort_output(input_text, Path("."))

    return {
        "validator": lint_data.validator,
        "total_violations": lint_data.total_violations,
        "files_scanned": lint_data.files_scanned,
        "errors": lint_data.errors,
        "warnings": lint_data.warnings,
        "info": lint_data.info,
        "by_code": lint_data.by_code,
        "file_violations": [
            {
                "file_path": fv.file_path,
                "violations": fv.violations,
                "validator": fv.validator,
            }
            for fv in lint_data.file_violations
        ],
    }
