"""
Target callable execution and import management.

This module handles dynamic import of target callables and their execution
with input strings.
"""

import importlib
from typing import Any, Callable, Dict


class TargetExecutor:
    """
    Executes target callables with input strings.

    The executor dynamically imports target functions and executes them
    with the provided input, enforcing the (str) -> dict interface contract.
    """

    def __init__(self):
        """Initialize target executor."""
        self._callable_cache: Dict[str, Callable[[str], dict]] = {}

    def execute(self, callable_path: str, input_text: str) -> dict:
        """
        Execute target callable with input text.

        Args:
            callable_path: Dotted path to callable (e.g., "module.path.function")
            input_text: Input string to pass to callable

        Returns:
            Dictionary returned by the callable

        Raises:
            ImportError: If module or callable cannot be imported
            TypeError: If callable doesn't match (str) -> dict signature
            Exception: Any exception raised by the callable
        """
        # Get cached callable or import it
        if callable_path not in self._callable_cache:
            callable_func = self._import_callable(callable_path)
            self._callable_cache[callable_path] = callable_func
        else:
            callable_func = self._callable_cache[callable_path]

        # Execute callable
        try:
            result = callable_func(input_text)
        except Exception as e:
            raise Exception(
                f"Error executing callable '{callable_path}' with input: {e}"
            ) from e

        # Validate return type
        if not isinstance(result, dict):
            raise TypeError(
                f"Callable '{callable_path}' must return dict, got {type(result).__name__}"
            )

        return result

    def _import_callable(self, callable_path: str) -> Callable[[str], dict]:
        """
        Import callable from dotted path.

        Args:
            callable_path: Dotted path to callable (e.g., "module.path.function")

        Returns:
            Imported callable function

        Raises:
            ImportError: If module or callable cannot be imported
            TypeError: If imported object is not callable
        """
        # Split into module path and function name
        parts = callable_path.rsplit(".", 1)
        if len(parts) != 2:
            raise ImportError(
                f"Invalid callable path '{callable_path}'. "
                "Must be in format 'module.path.function'"
            )

        module_path, function_name = parts

        # Import module
        try:
            module = importlib.import_module(module_path)
        except ImportError as e:
            raise ImportError(
                f"Failed to import module '{module_path}' from callable path '{callable_path}': {e}"
            ) from e

        # Get function from module
        if not hasattr(module, function_name):
            raise ImportError(
                f"Module '{module_path}' has no attribute '{function_name}'"
            )

        callable_func = getattr(module, function_name)

        # Verify it's callable
        if not callable(callable_func):
            raise TypeError(
                f"Object '{callable_path}' is not callable (type: {type(callable_func).__name__})"
            )

        return callable_func

    def clear_cache(self) -> None:
        """Clear the callable cache."""
        self._callable_cache.clear()
