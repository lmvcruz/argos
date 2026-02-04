"""
Result comparison utilities for test validation.

Handles comparison of expected and actual test results with support for:
- Optional fields (like actual_code, expected_code)
- Extra fields in actual results (warning, not failure)
- Missing required fields in actual results (failure)
- Detailed diff reporting
"""

from typing import Any, Dict, List, Set, Tuple


def get_optional_fields() -> Set[str]:
    """
    Get the set of optional field names.

    These fields can be missing from actual results without causing failure.

    Returns:
        Set of optional field names
    """
    return {
        "actual_code",
        "expected_code",
        "actual_lines",
        "expected_lines",
    }


def compare_results(expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Compare expected and actual results.

    Handles comparison logic that:
    - Returns False if expected fields are missing from actual (except optional)
    - Returns True but warns if actual has extra fields
    - Returns True if all expected fields match (ignoring extra fields)
    - Treats fields in optional_fields set as truly optional

    Args:
        expected: Expected result dictionary
        actual: Actual result from validator

    Returns:
        Tuple of (passed: bool, warnings: List[str])
        - passed: True if expected fields match actual
        - warnings: List of warning/error messages
    """
    warnings: List[str] = []
    optional_fields = get_optional_fields()

    # Check for missing required fields
    for key, expected_value in expected.items():
        # If field is optional and missing from actual, skip it
        if key in optional_fields and key not in actual:
            continue

        if key not in actual:
            # Field is required but missing in actual
            warnings.append(f"Missing required field: '{key}' (expected: {expected_value!r})")
        else:
            # Field exists in actual, compare values
            actual_value = actual[key]

            if not _values_equal(expected_value, actual_value):
                warnings.append(
                    f"Field '{key}' mismatch: "
                    f"expected {expected_value!r}, "
                    f"got {actual_value!r}"
                )

    # Check for extra fields in actual
    extra_fields = set(actual.keys()) - set(expected.keys())
    if extra_fields:
        fields_str = ", ".join(sorted(extra_fields))
        warnings.append(
            f"Extra fields in actual result: {fields_str}. "
            f"These fields were not expected but may indicate parser enhancement."
        )

    # Passed only if no errors (warnings about extra fields don't fail)
    # But errors about missing/mismatched fields do fail
    has_errors = any(
        warning.startswith("Missing") or warning.startswith("Field") for warning in warnings
    )

    return (not has_errors, warnings)


def _values_equal(expected: Any, actual: Any) -> bool:
    """
    Compare two values for equality.

    Handles nested structures (dicts, lists) recursively.

    Args:
        expected: Expected value
        actual: Actual value

    Returns:
        True if values are equal, False otherwise
    """
    if isinstance(expected, dict) and isinstance(actual, dict):
        if set(expected.keys()) != set(actual.keys()):
            return False
        return all(_values_equal(expected[k], actual[k]) for k in expected.keys())

    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return False
        return all(_values_equal(e, a) for e, a in zip(expected, actual))

    return expected == actual
