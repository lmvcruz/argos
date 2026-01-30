"""
Issue grouping utilities for reports.

This module provides functions to group issues by file, validator, or severity.
"""

from collections import defaultdict
from typing import Dict, List

from anvil.models.validator import Issue, ValidationResult


def group_issues_by_file(
    results: List[ValidationResult],
) -> Dict[str, List[Issue]]:
    """
    Group all issues by file path.

    Args:
        results: List of validation results

    Returns:
        Dictionary mapping file paths to lists of issues
    """
    grouped = defaultdict(list)

    for result in results:
        for issue in result.errors + result.warnings:
            grouped[issue.file_path].append(issue)

    return dict(grouped)


def group_issues_by_validator(
    results: List[ValidationResult],
) -> Dict[str, List[Issue]]:
    """
    Group all issues by validator name.

    Args:
        results: List of validation results

    Returns:
        Dictionary mapping validator names to lists of issues
    """
    grouped = defaultdict(list)

    for result in results:
        for issue in result.errors + result.warnings:
            grouped[result.validator_name].append(issue)

    return dict(grouped)


def group_issues_by_severity(
    results: List[ValidationResult],
) -> Dict[str, List[Issue]]:
    """
    Group all issues by severity level.

    Args:
        results: List of validation results

    Returns:
        Dictionary mapping severity levels to lists of issues
    """
    grouped = defaultdict(list)

    for result in results:
        for issue in result.errors + result.warnings:
            grouped[issue.severity].append(issue)

    return dict(grouped)
