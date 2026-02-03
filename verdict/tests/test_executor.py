"""
Tests for verdict.executor module.

Tests TargetExecutor class for dynamic import and execution of target callables.
"""

import sys
from unittest.mock import MagicMock

import pytest

from verdict.executor import TargetExecutor


class TestTargetExecutor:
    """Test suite for TargetExecutor class."""

    def test_import_callable_from_module(self):
        """Test importing a callable from a standard library module."""
        executor = TargetExecutor()

        # Import a known function from pathlib
        callable_func = executor.import_callable("pathlib.Path")

        assert callable_func is not None
        assert callable(callable_func)

    def test_import_callable_from_conftest(self):
        """Test importing the dummy_callable from conftest."""
        executor = TargetExecutor()

        callable_func = executor.import_callable("tests.conftest.dummy_callable")

        assert callable_func is not None
        assert callable(callable_func)

        # Test it works
        result = callable_func("test")
        assert isinstance(result, dict)
        assert result["text"] == "test"
        assert result["dummy"] is True

    def test_import_callable_invalid_path(self):
        """Test importing from an invalid module path."""
        executor = TargetExecutor()

        with pytest.raises(ImportError, match="Could not import module"):
            executor.import_callable("nonexistent.module.function")

    def test_import_callable_missing_attribute(self):
        """Test importing a non-existent attribute from valid module."""
        executor = TargetExecutor()

        with pytest.raises(AttributeError, match="has no attribute"):
            executor.import_callable("pathlib.NonExistentClass")

    def test_import_callable_not_callable(self):
        """Test importing something that is not callable."""
        executor = TargetExecutor()

        with pytest.raises(TypeError, match="is not callable"):
            executor.import_callable("sys.version")  # version is a string

    def test_callable_caching(self):
        """Test that callables are cached after first import."""
        executor = TargetExecutor()

        # First import
        callable1 = executor.import_callable("tests.conftest.dummy_callable")

        # Second import (should use cache)
        callable2 = executor.import_callable("tests.conftest.dummy_callable")

        # Should be the same object
        assert callable1 is callable2

    def test_execute_callable_returns_dict(self, mock_callable):
        """Test executing a callable that returns a dict."""
        executor = TargetExecutor()

        result = executor.execute_callable(mock_callable, "test input")

        assert isinstance(result, dict)
        assert result["input_length"] == 10
        assert result["input_upper"] == "TEST INPUT"
        assert result["processed"] is True

    def test_execute_callable_non_dict_return(self):
        """Test executing a callable that doesn't return a dict."""
        def bad_callable(input_text: str) -> str:
            return "not a dict"

        executor = TargetExecutor()

        with pytest.raises(TypeError, match="must return a dict"):
            executor.execute_callable(bad_callable, "test")

    def test_execute_callable_with_exception(self):
        """Test executing a callable that raises an exception."""
        def failing_callable(input_text: str) -> dict:
            raise ValueError("Something went wrong")

        executor = TargetExecutor()

        with pytest.raises(ValueError, match="Something went wrong"):
            executor.execute_callable(failing_callable, "test")

    def test_execute_callable_empty_input(self, mock_callable):
        """Test executing a callable with empty string input."""
        executor = TargetExecutor()

        result = executor.execute_callable(mock_callable, "")

        assert isinstance(result, dict)
        assert result["input_length"] == 0
        assert result["input_upper"] == ""

    def test_execute_callable_multiline_input(self, mock_callable):
        """Test executing a callable with multiline input."""
        executor = TargetExecutor()

        input_text = "line 1\nline 2\nline 3"
        result = executor.execute_callable(mock_callable, input_text)

        assert isinstance(result, dict)
        assert result["input_length"] == len(input_text)

    def test_import_and_execute_integration(self):
        """Test full workflow: import and execute a callable."""
        executor = TargetExecutor()

        # Import the callable
        callable_func = executor.import_callable("tests.conftest.dummy_callable")

        # Execute it
        result = executor.execute_callable(callable_func, "integration test")

        assert isinstance(result, dict)
        assert result["text"] == "integration test"
        assert result["length"] == len("integration test")
        assert result["dummy"] is True

    def test_multiple_executors_share_no_cache(self):
        """Test that different executor instances have separate caches."""
        executor1 = TargetExecutor()
        executor2 = TargetExecutor()

        callable1 = executor1.import_callable("tests.conftest.dummy_callable")
        callable2 = executor2.import_callable("tests.conftest.dummy_callable")

        # Should be different instances (different cache)
        # Note: In actual implementation, they might be the same function object
        # but from different cache dictionaries
        assert executor1._callable_cache != executor2._callable_cache or len(executor1._callable_cache) == 0

    def test_clear_cache(self):
        """Test clearing the callable cache."""
        executor = TargetExecutor()

        # Import and cache
        callable1 = executor.import_callable("tests.conftest.dummy_callable")
        assert len(executor._callable_cache) > 0

        # Clear cache
        executor.clear_cache()
        assert len(executor._callable_cache) == 0

        # Import again (should work)
        callable2 = executor.import_callable("tests.conftest.dummy_callable")
        assert callable2 is not None

    def test_callable_with_complex_return(self):
        """Test callable that returns complex nested dictionary."""
        def complex_callable(input_text: str) -> dict:
            return {
                "metadata": {
                    "length": len(input_text),
                    "type": "test"
                },
                "results": [
                    {"id": 1, "value": "a"},
                    {"id": 2, "value": "b"}
                ],
                "summary": {
                    "total": 2,
                    "success": True
                }
            }

        executor = TargetExecutor()
        result = executor.execute_callable(complex_callable, "test")

        assert isinstance(result, dict)
        assert "metadata" in result
        assert "results" in result
        assert len(result["results"]) == 2
        assert result["summary"]["success"] is True
