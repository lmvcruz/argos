"""
Test suite for result comparison logic.

Tests the logic for comparing expected and actual test results,
including handling of optional fields, extra fields, and missing fields.
"""


class TestResultComparison:
    """Tests for comparing expected vs actual results."""

    def test_exact_match_all_fields(self):
        """Verify exact match when all fields are identical."""
        from anvil.testing.result_comparison import compare_results

        expected = {"validator": "black", "total_violations": 5, "errors": 0}
        actual = {"validator": "black", "total_violations": 5, "errors": 0}

        passed, warnings = compare_results(expected, actual)

        assert passed is True
        assert warnings == []

    def test_actual_missing_optional_field(self):
        """Verify pass when actual is missing optional fields (like actual_code)."""
        from anvil.testing.result_comparison import compare_results

        expected = {
            "validator": "black",
            "total_violations": 5,
            "actual_code": "def foo():\n    pass",
        }
        actual = {"validator": "black", "total_violations": 5}

        passed, warnings = compare_results(expected, actual)

        assert passed is True
        assert warnings == []

    def test_actual_has_extra_fields(self):
        """Verify warning when actual has more fields than expected."""
        from anvil.testing.result_comparison import compare_results

        expected = {"validator": "black", "total_violations": 5}
        actual = {
            "validator": "black",
            "total_violations": 5,
            "extra_field": "unexpected",
            "another_extra": 123,
        }

        passed, warnings = compare_results(expected, actual)

        assert passed is True  # Still passes, but with warning
        assert len(warnings) == 1
        assert "extra_field" in warnings[0]
        assert "another_extra" in warnings[0]

    def test_expected_has_field_actual_missing(self):
        """Verify failure when expected has field but actual doesn't."""
        from anvil.testing.result_comparison import compare_results

        expected = {"validator": "black", "total_violations": 5, "required_field": "value"}
        actual = {"validator": "black", "total_violations": 5}

        passed, warnings = compare_results(expected, actual)

        assert passed is False
        assert len(warnings) == 1
        assert "required_field" in warnings[0]

    def test_field_value_mismatch(self):
        """Verify failure when field values don't match."""
        from anvil.testing.result_comparison import compare_results

        expected = {"validator": "black", "total_violations": 5}
        actual = {"validator": "black", "total_violations": 6}

        passed, warnings = compare_results(expected, actual)

        assert passed is False
        assert len(warnings) == 1
        assert "total_violations" in warnings[0]

    def test_nested_dict_exact_match(self):
        """Verify nested dictionaries are compared correctly."""
        from anvil.testing.result_comparison import compare_results

        expected = {
            "validator": "black",
            "by_code": {"BLACK001": 5, "BLACK002": 2},
            "metadata": {"parser_version": "23.0"},
        }
        actual = {
            "validator": "black",
            "by_code": {"BLACK001": 5, "BLACK002": 2},
            "metadata": {"parser_version": "23.0"},
        }

        passed, warnings = compare_results(expected, actual)

        assert passed is True
        assert warnings == []

    def test_nested_dict_mismatch(self):
        """Verify nested dictionary mismatches are caught."""
        from anvil.testing.result_comparison import compare_results

        expected = {"validator": "black", "by_code": {"BLACK001": 5}}
        actual = {"validator": "black", "by_code": {"BLACK001": 6}}

        passed, warnings = compare_results(expected, actual)

        assert passed is False
        assert len(warnings) == 1
        assert "BLACK001" in warnings[0] or "by_code" in warnings[0]

    def test_list_exact_match(self):
        """Verify lists are compared correctly when identical."""
        from anvil.testing.result_comparison import compare_results

        expected = {
            "validator": "black",
            "file_violations": [
                {"file_path": "file1.py", "violations": [{"line": 1}]},
                {"file_path": "file2.py", "violations": [{"line": 2}]},
            ],
        }
        actual = {
            "validator": "black",
            "file_violations": [
                {"file_path": "file1.py", "violations": [{"line": 1}]},
                {"file_path": "file2.py", "violations": [{"line": 2}]},
            ],
        }

        passed, warnings = compare_results(expected, actual)

        assert passed is True
        assert warnings == []

    def test_list_length_mismatch(self):
        """Verify failure when list lengths don't match."""
        from anvil.testing.result_comparison import compare_results

        expected = {
            "validator": "black",
            "file_violations": [
                {"file_path": "file1.py"},
                {"file_path": "file2.py"},
            ],
        }
        actual = {
            "validator": "black",
            "file_violations": [{"file_path": "file1.py"}],
        }

        passed, warnings = compare_results(expected, actual)

        assert passed is False

    def test_optional_field_none_vs_missing(self):
        """Verify that optional fields can be missing without failure."""
        from anvil.testing.result_comparison import compare_results

        expected = {"validator": "black", "actual_code": None}
        actual = {"validator": "black"}

        passed, warnings = compare_results(expected, actual)

        # actual_code is optional, so it's ok if it's missing
        assert passed is True
        assert warnings == []

    def test_actual_code_and_expected_code_optional(self):
        """Verify actual_code and expected_code are optional fields."""
        from anvil.testing.result_comparison import compare_results  # noqa: F401
        from anvil.testing.result_comparison import (
            get_optional_fields,
        )

        optional = get_optional_fields()

        assert "actual_code" in optional
        assert "expected_code" in optional

    def test_comparison_with_all_optional_fields_present(self):
        """Verify comparison works when all optional fields are present."""
        from anvil.testing.result_comparison import compare_results

        expected = {
            "validator": "black",
            "total_violations": 1,
            "actual_code": "x=1",
            "expected_code": "x = 1",
        }
        actual = {
            "validator": "black",
            "total_violations": 1,
            "actual_code": "x=1",
            "expected_code": "x = 1",
        }

        passed, warnings = compare_results(expected, actual)

        assert passed is True
        assert warnings == []

    def test_comparison_with_some_optional_fields_missing(self):
        """Verify comparison passes when some optional fields are missing."""
        from anvil.testing.result_comparison import compare_results

        expected = {
            "validator": "black",
            "total_violations": 1,
            "actual_code": "x=1",
            # expected_code not in expected (optional)
        }
        actual = {
            "validator": "black",
            "total_violations": 1,
            # Both actual_code and expected_code missing from actual
        }

        passed, warnings = compare_results(expected, actual)

        assert passed is True
        assert warnings == []
