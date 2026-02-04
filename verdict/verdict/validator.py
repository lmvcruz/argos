"""
Output validation by comparing actual vs expected dictionaries.

This module handles comparison of actual outputs against expected results,
identifying differences and generating detailed validation reports.
"""

import re
from typing import Any, Dict, List, Tuple


class OutputValidator:
    """
    Validates actual output against expected output.

    Performs deep dictionary comparison and generates detailed difference reports.
    """

    def validate(self, actual: dict, expected: dict) -> Tuple[bool, List[str]]:
        """
        Validate actual output against expected output.

        Args:
            actual: Actual output dictionary from target callable
            expected: Expected output dictionary from test case

        Returns:
            Tuple of (is_valid, list_of_differences)
            - is_valid: True if actual matches expected exactly
            - list_of_differences: List of difference descriptions (empty if valid)
        """
        differences = []
        self._compare_dicts(actual, expected, "", differences)
        is_valid = len(differences) == 0
        return is_valid, differences

    def _compare_dicts(
        self,
        actual: Dict[str, Any],
        expected: Dict[str, Any],
        path: str,
        differences: List[str],
    ) -> None:
        """
        Recursively compare two dictionaries.

        Implements partial matching: only checks that expected fields exist in actual.
        Extra fields in actual are ignored (not considered errors).

        Args:
            actual: Actual dictionary
            expected: Expected dictionary
            path: Current path in nested structure (for error messages)
            differences: List to append differences to
        """
        # Check for missing keys in actual
        for key in expected:
            if key not in actual:
                diff_path = f"{path}.{key}" if path else key
                differences.append(f"Missing field '{diff_path}'")

        # PARTIAL MATCHING: Don't check for extra keys in actual
        # This allows actual output to have more fields than expected

        # Compare values for common keys
        for key in expected:
            if key not in actual:
                continue

            diff_path = f"{path}.{key}" if path else key
            actual_value = actual[key]
            expected_value = expected[key]

            # Recursively compare nested dicts
            if isinstance(expected_value, dict):
                if not isinstance(actual_value, dict):
                    differences.append(
                        f"Type mismatch at {diff_path}: "
                        f"expected dict, got {type(actual_value).__name__}"
                    )
                else:
                    self._compare_dicts(actual_value, expected_value, diff_path, differences)
            # Recursively compare lists
            elif isinstance(expected_value, list):
                if not isinstance(actual_value, list):
                    differences.append(
                        f"Type mismatch at {diff_path}: "
                        f"expected list, got {type(actual_value).__name__}"
                    )
                else:
                    self._compare_lists(actual_value, expected_value, diff_path, differences)
            # Compare primitive values
            else:
                if not self._values_match(actual_value, expected_value):
                    field_ref = f"Field '{diff_path}'"
                    # Check if type mismatch
                    if not isinstance(actual_value, type(expected_value)):
                        differences.append(
                            f"{field_ref}: type mismatch - "
                            f"expected {type(expected_value).__name__}, "
                            f"got {type(actual_value).__name__}"
                        )
                    else:
                        differences.append(
                            f"{field_ref}: expected {repr(expected_value)}, "
                            f"got {repr(actual_value)}"
                        )

    def _compare_lists(
        self,
        actual: List[Any],
        expected: List[Any],
        path: str,
        differences: List[str],
    ) -> None:
        """
        Compare two lists.

        Args:
            actual: Actual list
            expected: Expected list
            path: Current path in nested structure
            differences: List to append differences to
        """
        # Check length
        if len(actual) != len(expected):
            differences.append(
                f"List length mismatch at {path}: "
                f"expected {len(expected)} items, got {len(actual)} items"
            )
            # Compare up to the shorter length
            min_length = min(len(actual), len(expected))
        else:
            min_length = len(actual)

        # Compare items
        for i in range(min_length):
            item_path = f"{path}[{i}]"
            actual_item = actual[i]
            expected_item = expected[i]

            # Recursively compare nested dicts
            if isinstance(expected_item, dict):
                if not isinstance(actual_item, dict):
                    differences.append(
                        f"Type mismatch at {item_path}: "
                        f"expected dict, got {type(actual_item).__name__}"
                    )
                else:
                    self._compare_dicts(actual_item, expected_item, item_path, differences)
            # Recursively compare nested lists
            elif isinstance(expected_item, list):
                if not isinstance(actual_item, list):
                    differences.append(
                        f"Type mismatch at {item_path}: "
                        f"expected list, got {type(actual_item).__name__}"
                    )
                else:
                    self._compare_lists(actual_item, expected_item, item_path, differences)
            # Compare primitive values
            else:
                if not self._values_match(actual_item, expected_item):
                    differences.append(
                        f"Value mismatch at {item_path}: "
                        f"expected {repr(expected_item)}, got {repr(actual_item)}"
                    )

    def _values_match(self, actual: Any, expected: Any) -> bool:
        """
        Compare two values, supporting regex pattern matching.

        If expected is a string starting with "regex:", treat it as a regex pattern.
        Otherwise, perform exact equality comparison.

        Args:
            actual: Actual value
            expected: Expected value (may be regex pattern)

        Returns:
            True if values match, False otherwise
        """
        # Handle regex patterns
        if isinstance(expected, str) and expected.startswith("regex:"):
            pattern = expected[6:]  # Remove "regex:" prefix
            if not isinstance(actual, str):
                return False
            try:
                return bool(re.match(pattern, actual))
            except re.error:
                # Invalid regex pattern - treat as literal string
                return actual == expected

        # Exact equality
        return actual == expected
