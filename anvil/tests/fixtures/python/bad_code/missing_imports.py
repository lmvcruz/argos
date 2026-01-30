"""
Python file with missing/wrong imports.

This fixture has logical errors related to imports.
"""


def use_undefined_module():
    """Use a module that was never imported."""
    # numpy is not imported
    array = numpy.array([1, 2, 3])  # noqa: F821
    return array.sum()


def use_undefined_function():
    """Use a function that doesn't exist."""
    # calculate_sum is not defined or imported
    result = calculate_sum([1, 2, 3])  # noqa: F821
    return result


def use_wrong_import():
    """Import statement has wrong module name."""
    from pathlibb import Path  # noqa: F401 # Typo: pathlibb instead of pathlib
    return Path("/tmp")


class UndefinedBase(NonExistentClass):  # noqa: F821
    """Inherit from undefined class."""

