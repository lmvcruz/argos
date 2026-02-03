"""
Pytest configuration and shared fixtures for Verdict tests.

This module provides reusable test fixtures for creating temporary
test configurations, test cases, and mock callables.
"""

import tempfile
from pathlib import Path
from typing import Callable, Dict

import pytest


@pytest.fixture
def temp_dir():
    """
    Create a temporary directory for test files.

    Yields:
        Path: Temporary directory path that is cleaned up after test

    Examples:
        >>> def test_something(temp_dir):
        ...     config_file = temp_dir / "config.yaml"
        ...     config_file.write_text("test: data")
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_config_dict() -> Dict:
    """
    Create a sample configuration dictionary.

    Returns:
        Dictionary with valid Verdict configuration structure

    Examples:
        >>> def test_config(sample_config_dict):
        ...     assert "targets" in sample_config_dict
        ...     assert "test_suites" in sample_config_dict
    """
    return {
        "targets": {
            "test_target": {
                "callable": "tests.conftest.dummy_callable"
            }
        },
        "test_suites": [
            {
                "name": "test_suite_1",
                "target": "test_target",
                "type": "single_file",
                "cases": ["case1.yaml", "case2.yaml"]
            }
        ],
        "settings": {
            "max_workers": 2
        }
    }


@pytest.fixture
def sample_test_case_dict() -> Dict:
    """
    Create a sample test case dictionary.

    Returns:
        Dictionary with valid test case structure

    Examples:
        >>> def test_case(sample_test_case_dict):
        ...     assert "name" in sample_test_case_dict
        ...     assert "input" in sample_test_case_dict
    """
    return {
        "name": "Sample test case",
        "description": "A sample test case for testing",
        "input": {
            "type": "text",
            "content": "test input"
        },
        "expected": {
            "result": "success",
            "value": 42
        }
    }


@pytest.fixture
def mock_callable() -> Callable[[str], Dict]:
    """
    Create a mock callable that follows Verdict's interface.

    Returns:
        Callable that accepts str and returns dict

    Examples:
        >>> def test_executor(mock_callable):
        ...     result = mock_callable("test")
        ...     assert isinstance(result, dict)
    """
    def callable_impl(input_text: str) -> dict:
        """Mock implementation of Verdict callable interface."""
        return {
            "input_length": len(input_text),
            "input_upper": input_text.upper(),
            "processed": True
        }
    return callable_impl


def dummy_callable(input_text: str) -> dict:
    """
    Dummy callable for testing imports.

    This function is referenced in sample_config_dict and used
    to test dynamic imports in TargetExecutor.

    Args:
        input_text: Input text to process

    Returns:
        Dictionary with dummy results
    """
    return {
        "text": input_text,
        "length": len(input_text),
        "dummy": True
    }


def bad_callable(input_text: str) -> str:
    """
    Callable that returns wrong type (for testing).

    Args:
        input_text: Input text

    Returns:
        String instead of dict (violates interface)
    """
    return "not a dict"


def failing_callable(input_text: str) -> dict:
    """
    Callable that raises an exception (for testing).

    Args:
        input_text: Input text

    Raises:
        ValueError: Always raised
    """
    raise ValueError("Something went wrong")
