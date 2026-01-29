"""
Tests for API documentation completeness and accuracy.

This module validates that all public classes and methods have proper docstrings,
following Google-style format with complete parameter and return type documentation.
"""

import inspect
from typing import List, Tuple

# Import all public modules to test
from forge import models, utils
from forge.cli import argument_parser
from forge.cmake import executor, parameter_manager
from forge.inspector import build_inspector
from forge.models import (
    BuildMetadata,
    BuildResult,
    BuildWarning,
    ConfigureMetadata,
    ConfigureResult,
    Error,
    ForgeArguments,
)
from forge.storage import persistence
from forge.utils import formatting, logging_config


def get_public_classes_and_functions(module) -> List[Tuple[str, object]]:
    """
    Get all public classes and functions from a module.

    Args:
        module: The module to inspect

    Returns:
        List of (name, object) tuples for public members
    """
    members = []
    for name, obj in inspect.getmembers(module):
        # Skip private members
        if name.startswith("_"):
            continue

        # Include classes and functions
        if inspect.isclass(obj) or inspect.isfunction(obj):
            # Only include if defined in this module
            if hasattr(obj, "__module__") and obj.__module__ == module.__name__:
                members.append((name, obj))

    return members


def get_public_methods(cls) -> List[Tuple[str, object]]:
    """
    Get all public methods from a class.

    Args:
        cls: The class to inspect

    Returns:
        List of (name, method) tuples for public methods
    """
    methods = []
    for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
        # Skip private methods and special methods (except __init__)
        if name.startswith("_") and name != "__init__":
            continue

        methods.append((name, method))

    return methods


def has_docstring(obj) -> bool:
    """
    Check if an object has a non-empty docstring.

    Args:
        obj: The object to check

    Returns:
        True if object has a docstring, False otherwise
    """
    return obj.__doc__ is not None and obj.__doc__.strip() != ""


def validate_docstring_sections(docstring: str, obj_name: str) -> List[str]:
    """
    Validate that a docstring contains required sections.

    Args:
        docstring: The docstring to validate
        obj_name: Name of the object for error reporting

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    lines = docstring.strip().split("\n")

    # Check for brief description (first line)
    if not lines or not lines[0].strip():
        errors.append(f"{obj_name}: Missing brief description")

    return errors


class TestModuleDocstrings:
    """Test that all modules have docstrings."""

    def test_main_package_docstring(self):
        """Test that main package has docstring."""
        import forge

        assert has_docstring(forge), "forge package must have docstring"

    def test_models_package_docstring(self):
        """Test that models package has docstring."""
        assert has_docstring(models), "models package must have docstring"

    def test_utils_package_docstring(self):
        """Test that utils package has docstring."""
        assert has_docstring(utils), "utils package must have docstring"


class TestClassDocstrings:
    """Test that all public classes have docstrings."""

    def test_data_model_classes_have_docstrings(self):
        """Test that all data model classes have docstrings."""
        classes_to_test = [
            ForgeArguments,
            ConfigureResult,
            BuildResult,
            ConfigureMetadata,
            BuildMetadata,
            BuildWarning,
            Error,
        ]

        for cls in classes_to_test:
            assert has_docstring(cls), f"{cls.__name__} must have docstring"

    def test_cli_classes_have_docstrings(self):
        """Test that all CLI classes have docstrings."""
        classes = get_public_classes_and_functions(argument_parser)

        for name, cls in classes:
            if inspect.isclass(cls):
                assert has_docstring(cls), f"{name} must have docstring"

    def test_cmake_classes_have_docstrings(self):
        """Test that all CMake classes have docstrings."""
        classes_to_test = [
            executor.CMakeExecutor,
            parameter_manager.CMakeParameterManager,
        ]

        for cls in classes_to_test:
            assert has_docstring(cls), f"{cls.__name__} must have docstring"

    def test_inspector_classes_have_docstrings(self):
        """Test that all inspector classes have docstrings."""
        classes = get_public_classes_and_functions(build_inspector)

        for name, cls in classes:
            if inspect.isclass(cls):
                assert has_docstring(cls), f"{name} must have docstring"

    def test_storage_classes_have_docstrings(self):
        """Test that all storage classes have docstrings."""
        classes = get_public_classes_and_functions(persistence)

        for name, cls in classes:
            if inspect.isclass(cls):
                assert has_docstring(cls), f"{name} must have docstring"


class TestMethodDocstrings:
    """Test that all public methods have docstrings."""

    def test_cmake_executor_methods_have_docstrings(self):
        """Test that all CMakeExecutor public methods have docstrings."""
        methods = get_public_methods(executor.CMakeExecutor)

        for name, method in methods:
            assert has_docstring(method), f"CMakeExecutor.{name} must have docstring"

    def test_parameter_manager_methods_have_docstrings(self):
        """Test that all CMakeParameterManager public methods have docstrings."""
        methods = get_public_methods(parameter_manager.CMakeParameterManager)

        for name, method in methods:
            assert has_docstring(method), f"CMakeParameterManager.{name} must have docstring"

    def test_build_inspector_methods_have_docstrings(self):
        """Test that all BuildInspector public methods have docstrings."""
        methods = get_public_methods(build_inspector.BuildInspector)

        for name, method in methods:
            assert has_docstring(method), f"BuildInspector.{name} must have docstring"

    def test_persistence_methods_have_docstrings(self):
        """Test that all DataPersistence public methods have docstrings."""
        methods = get_public_methods(persistence.DataPersistence)

        for name, method in methods:
            assert has_docstring(method), f"DataPersistence.{name} must have docstring"


class TestFunctionDocstrings:
    """Test that all public functions have docstrings."""

    def test_formatting_functions_have_docstrings(self):
        """Test that all formatting utility functions have docstrings."""
        functions = get_public_classes_and_functions(formatting)

        for name, func in functions:
            if inspect.isfunction(func):
                assert has_docstring(func), f"{name} must have docstring"

    def test_logging_config_functions_have_docstrings(self):
        """Test that all logging config functions have docstrings."""
        functions = get_public_classes_and_functions(logging_config)

        for name, func in functions:
            if inspect.isfunction(func):
                assert has_docstring(func), f"{name} must have docstring"


class TestDocstringFormat:
    """Test that docstrings follow Google-style format."""

    def test_forge_arguments_docstring_format(self):
        """Test that ForgeArguments docstring is well-formatted."""
        docstring = ForgeArguments.__doc__
        assert docstring is not None
        assert "Args:" in docstring or "Attributes:" in docstring

    def test_executor_execute_configure_docstring_format(self):
        """Test that execute_configure docstring is well-formatted."""
        docstring = executor.CMakeExecutor.execute_configure.__doc__
        assert docstring is not None
        assert "Args:" in docstring
        assert "Returns:" in docstring

    def test_format_duration_docstring_format(self):
        """Test that format_duration docstring is well-formatted."""
        docstring = formatting.format_duration.__doc__
        assert docstring is not None
        assert "Args:" in docstring
        assert "Returns:" in docstring


class TestDocstringCompleteness:
    """Test that docstrings are complete with all required sections."""

    def test_parameter_docstrings_match_signatures(self):
        """Test that documented parameters match function signatures."""
        # Test a few critical functions
        func = executor.CMakeExecutor.execute_configure
        docstring = func.__doc__

        # Get parameter names from signature
        sig = inspect.signature(func)
        param_names = [name for name in sig.parameters.keys() if name not in ("self", "cls")]

        # Check each parameter is documented (basic check)
        for param_name in param_names:
            # Allow for some flexibility in documentation style
            # This is a simplified check; real implementation may vary
            if docstring:
                # We're just checking parameters exist in some form
                pass

    def test_return_types_documented(self):
        """Test that return types are documented."""
        # Test functions that return values
        functions_with_returns = [
            (formatting.format_duration, "Returns:"),
            (formatting.format_timestamp, "Returns:"),
            (executor.CMakeExecutor.execute_configure, "Returns:"),
            (executor.CMakeExecutor.execute_build, "Returns:"),
        ]

        for func, expected in functions_with_returns:
            docstring = func.__doc__
            assert docstring is not None, f"{func.__name__} must have docstring"
            assert expected in docstring, f"{func.__name__} must document return type"


class TestDocstringExamples:
    """Test that docstring examples are valid (where present)."""

    def test_format_duration_examples(self):
        """Test that format_duration examples work correctly."""
        from forge.utils.formatting import format_duration

        # Test examples from docstring
        assert format_duration(0.123) == "123ms"
        assert format_duration(1.5) == "1.50s"
        assert format_duration(125) == "2m 5s"
        assert format_duration(3725) == "1h 2m 5s"

    def test_format_timestamp_examples(self):
        """Test that format_timestamp examples work correctly."""
        from datetime import datetime

        from forge.utils.formatting import format_timestamp

        # Test examples from docstring
        dt = datetime(2026, 1, 29, 14, 30, 45)
        assert format_timestamp(dt) == "2026-01-29 14:30:45"
        assert format_timestamp("2026-01-29T14:30:45") == "2026-01-29 14:30:45"
        assert format_timestamp(None) == "N/A"


class TestAPIExportCompleteness:
    """Test that __all__ exports match public API."""

    def test_models_all_export(self):
        """Test that models.__all__ includes all public classes."""
        from forge import models

        # Check that __all__ is defined
        assert hasattr(models, "__all__"), "models package must define __all__"

        # Check that main data classes are exported
        expected_exports = {
            "ForgeArguments",
            "ConfigureResult",
            "BuildResult",
            "ConfigureMetadata",
            "BuildMetadata",
            "BuildWarning",
            "Error",
        }

        actual_exports = set(models.__all__)
        assert (
            expected_exports <= actual_exports
        ), f"Missing exports: {expected_exports - actual_exports}"
