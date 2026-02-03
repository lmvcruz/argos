"""
Tests for verdict.executor module.

Tests TargetExecutor class for dynamic import and execution of target callables.
"""

import pytest

from verdict.executor import TargetExecutor


class TestTargetExecutor:
    """Test suite for TargetExecutor class."""

    def test_import_callable_from_module(self):
        """Test executing a callable from a module."""
        executor = TargetExecutor()

        # Execute using the test dummy callable
        result = executor.execute("tests.conftest.dummy_callable", "test")

        assert isinstance(result, dict)
        assert result["text"] == "test"
        assert result["dummy"] is True

    def test_import_callable_from_conftest(self):
        """Test importing the dummy_callable from conftest."""
        executor = TargetExecutor()

        result = executor.execute("tests.conftest.dummy_callable", "test")

        assert isinstance(result, dict)
        assert result["text"] == "test"
        assert result["length"] == 4
        assert result["dummy"] is True

    def test_import_callable_invalid_path(self):
        """Test importing from an invalid module path."""
        executor = TargetExecutor()

        with pytest.raises(ImportError):
            executor.execute("nonexistent.module.function", "test")

    def test_import_callable_missing_attribute(self):
        """Test importing a non-existent attribute from valid module."""
        executor = TargetExecutor()

        with pytest.raises(ImportError, match="has no attribute"):
            executor.execute("pathlib.NonExistentClass", "test")

    def test_import_callable_not_callable(self):
        """Test importing something that is not callable."""
        executor = TargetExecutor()

        with pytest.raises(TypeError, match="is not callable"):
            executor.execute("sys.version", "test")  # version is a string

    def test_callable_caching(self):
        """Test that callables are cached after first import."""
        executor = TargetExecutor()

        # First execution
        result1 = executor.execute("tests.conftest.dummy_callable", "test1")
        assert len(executor._callable_cache) == 1

        # Second execution (should use cache)
        result2 = executor.execute("tests.conftest.dummy_callable", "test2")
        assert len(executor._callable_cache) == 1

        # Results should be different (different input)
        assert result1["text"] == "test1"
        assert result2["text"] == "test2"

    def test_execute_callable_returns_dict(self):
        """Test executing a callable that returns a dict."""
        executor = TargetExecutor()

        result = executor.execute("tests.conftest.dummy_callable", "test input")

        assert isinstance(result, dict)
        assert result["text"] == "test input"
        assert result["length"] == 10
        assert result["dummy"] is True

    def test_execute_callable_non_dict_return(self):
        """Test executing a callable path that doesn't return a dict."""
        executor = TargetExecutor()

        with pytest.raises(TypeError, match="must return dict"):
            executor.execute("tests.conftest.bad_callable", "test")

    def test_execute_callable_with_exception(self):
        """Test executing a callable that raises an exception."""
        executor = TargetExecutor()

        with pytest.raises(Exception, match="Error executing callable"):
            executor.execute("tests.conftest.failing_callable", "test")

    def test_execute_callable_empty_input(self):
        """Test executing a callable with empty string input."""
        executor = TargetExecutor()

        result = executor.execute("tests.conftest.dummy_callable", "")

        assert isinstance(result, dict)
        assert result["length"] == 0
        assert result["text"] == ""

    def test_execute_callable_multiline_input(self):
        """Test executing a callable with multiline input."""
        executor = TargetExecutor()

        input_text = "line 1\nline 2\nline 3"
        result = executor.execute("tests.conftest.dummy_callable", input_text)

        assert isinstance(result, dict)
        assert result["length"] == len(input_text)
        assert result["text"] == input_text

    def test_import_and_execute_integration(self):
        """Test full workflow: import and execute a callable."""
        executor = TargetExecutor()

        # Execute the callable
        result = executor.execute("tests.conftest.dummy_callable", "integration test")

        assert isinstance(result, dict)
        assert result["text"] == "integration test"
        assert result["length"] == len("integration test")
        assert result["dummy"] is True

    def test_multiple_executors_share_no_cache(self):
        """Test that different executor instances have separate caches."""
        executor1 = TargetExecutor()
        executor2 = TargetExecutor()

        executor1.execute("tests.conftest.dummy_callable", "test1")
        executor2.execute("tests.conftest.dummy_callable", "test2")

        # Each executor has its own cache
        assert len(executor1._callable_cache) == 1
        assert len(executor2._callable_cache) == 1

    def test_clear_cache(self):
        """Test clearing the callable cache."""
        executor = TargetExecutor()

        # Execute and cache
        executor.execute("tests.conftest.dummy_callable", "test")
        assert len(executor._callable_cache) == 1

        # Clear cache
        executor._callable_cache.clear()
        assert len(executor._callable_cache) == 0

        # Execute again (should work and re-cache)
        result = executor.execute("tests.conftest.dummy_callable", "test2")
        assert result is not None
        assert len(executor._callable_cache) == 1

    def test_callable_with_complex_return(self):
        """Test callable that returns complex nested dictionary."""
        executor = TargetExecutor()

        # Use dummy_callable which returns a simple dict
        result = executor.execute("tests.conftest.dummy_callable", "test")

        assert isinstance(result, dict)
        assert "text" in result
        assert "length" in result
        assert "dummy" in result
