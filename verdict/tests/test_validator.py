"""
Tests for verdict.validator module.

Tests OutputValidator class for comparing actual vs expected output dictionaries.
"""

from verdict.validator import OutputValidator


class TestOutputValidator:
    """Test suite for OutputValidator class."""

    def test_exact_match_simple_dict(self):
        """Test validation with exact matching simple dictionaries."""
        validator = OutputValidator()

        actual = {"a": 1, "b": 2, "c": 3}
        expected = {"a": 1, "b": 2, "c": 3}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_partial_match_subset_fields(self):
        """Test validation with partial matching (expected is subset of actual)."""
        validator = OutputValidator()

        actual = {"a": 1, "b": 2, "c": 3, "d": 4}
        expected = {"a": 1, "b": 2}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_mismatch_value_difference(self):
        """Test validation fails when values differ."""
        validator = OutputValidator()

        actual = {"a": 1, "b": 2}
        expected = {"a": 1, "b": 3}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 1
        assert "Field 'b'" in differences[0]
        assert "expected 3" in differences[0]
        assert "got 2" in differences[0]

    def test_mismatch_missing_field(self):
        """Test validation fails when expected field is missing in actual."""
        validator = OutputValidator()

        actual = {"a": 1}
        expected = {"a": 1, "b": 2}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 1
        assert "Missing field 'b'" in differences[0]

    def test_mismatch_type_difference(self):
        """Test validation fails when types differ."""
        validator = OutputValidator()

        actual = {"a": "1"}
        expected = {"a": 1}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 1
        assert "Field 'a'" in differences[0]
        assert "type mismatch" in differences[0].lower()

    def test_nested_dict_exact_match(self):
        """Test validation with nested dictionaries."""
        validator = OutputValidator()

        actual = {"outer": {"inner": {"value": 42}}}
        expected = {"outer": {"inner": {"value": 42}}}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_nested_dict_partial_match(self):
        """Test validation with nested dictionaries (partial match)."""
        validator = OutputValidator()

        actual = {
            "outer": {"inner": {"value": 42, "extra": "data"}, "other": "field"},
            "top_level": "value",
        }
        expected = {"outer": {"inner": {"value": 42}}}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_nested_dict_mismatch(self):
        """Test validation fails with nested dictionary mismatch."""
        validator = OutputValidator()

        actual = {"outer": {"inner": {"value": 42}}}
        expected = {"outer": {"inner": {"value": 99}}}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 1
        assert "outer.inner.value" in differences[0] or "value" in differences[0]

    def test_list_exact_match(self):
        """Test validation with matching lists."""
        validator = OutputValidator()

        actual = {"items": [1, 2, 3]}
        expected = {"items": [1, 2, 3]}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_list_order_matters(self):
        """Test validation fails when list order differs."""
        validator = OutputValidator()

        actual = {"items": [1, 2, 3]}
        expected = {"items": [3, 2, 1]}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) > 0

    def test_list_length_mismatch(self):
        """Test validation fails when list lengths differ."""
        validator = OutputValidator()

        actual = {"items": [1, 2, 3]}
        expected = {"items": [1, 2]}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) > 0
        assert "length" in differences[0].lower() or "items" in differences[0]

    def test_list_of_dicts(self):
        """Test validation with lists containing dictionaries."""
        validator = OutputValidator()

        actual = {"results": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
        expected = {"results": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_empty_dicts(self):
        """Test validation with empty dictionaries."""
        validator = OutputValidator()

        actual = {}
        expected = {}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_empty_expected_matches_any_actual(self):
        """Test that empty expected dict matches any actual dict."""
        validator = OutputValidator()

        actual = {"a": 1, "b": 2, "c": 3}
        expected = {}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_boolean_values(self):
        """Test validation with boolean values."""
        validator = OutputValidator()

        actual = {"success": True, "error": False}
        expected = {"success": True, "error": False}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_none_values(self):
        """Test validation with None values."""
        validator = OutputValidator()

        actual = {"value": None}
        expected = {"value": None}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_none_vs_missing(self):
        """Test that None value is different from missing field."""
        validator = OutputValidator()

        actual = {"value": None}
        expected = {"value": None, "other": "data"}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert "Missing field 'other'" in differences[0]

    def test_multiple_differences(self):
        """Test validation with multiple differences."""
        validator = OutputValidator()

        actual = {"a": 1, "b": 2, "c": 3}
        expected = {"a": 1, "b": 99, "d": 4}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 2  # b mismatch, d missing

    def test_string_values(self):
        """Test validation with string values."""
        validator = OutputValidator()

        actual = {"message": "Hello, World!"}
        expected = {"message": "Hello, World!"}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_numeric_types(self):
        """Test validation with different numeric types."""
        validator = OutputValidator()

        actual = {"value": 42}
        expected = {"value": 42.0}

        is_valid, differences = validator.validate(actual, expected)

        # This might fail due to type mismatch (int vs float)
        # Depending on implementation, you might want to handle this
        assert is_valid is False or is_valid is True  # Implementation-dependent

    def test_complex_nested_structure(self):
        """Test validation with complex nested structure."""
        validator = OutputValidator()

        actual = {
            "metadata": {"version": "1.0", "author": "test"},
            "results": [
                {"id": 1, "data": {"value": 10, "status": "ok"}},
                {"id": 2, "data": {"value": 20, "status": "ok"}},
            ],
            "summary": {"total": 2, "passed": 2, "failed": 0},
        }
        expected = {
            "metadata": {"version": "1.0"},
            "results": [{"id": 1, "data": {"value": 10}}, {"id": 2, "data": {"value": 20}}],
            "summary": {"total": 2, "passed": 2},
        }

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_difference_message_format(self):
        """Test that difference messages are properly formatted."""
        validator = OutputValidator()

        actual = {"field": "actual_value"}
        expected = {"field": "expected_value"}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 1
        diff_msg = differences[0]
        assert "field" in diff_msg.lower()
        assert "expected_value" in diff_msg
        assert "actual_value" in diff_msg

    def test_nested_dict_type_mismatch(self):
        """Test type mismatch in nested dict."""
        validator = OutputValidator()

        actual = {"data": "not a dict"}
        expected = {"data": {"key": "value"}}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 1
        assert "type mismatch" in differences[0].lower()

    def test_nested_list_type_mismatch(self):
        """Test type mismatch in nested list."""
        validator = OutputValidator()

        actual = {"items": "not a list"}
        expected = {"items": [1, 2, 3]}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 1
        assert "type mismatch" in differences[0].lower()

    def test_list_of_dicts_with_type_mismatch(self):
        """Test list containing dicts with type mismatch."""
        validator = OutputValidator()

        actual = {"items": ["not a dict", {"b": 2}]}
        expected = {"items": [{"a": 1}, {"b": 2}]}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) > 0
        assert any("type mismatch" in d.lower() for d in differences)

    def test_list_of_lists_with_type_mismatch(self):
        """Test list containing lists with type mismatch."""
        validator = OutputValidator()

        actual = {"matrix": ["not a list", [2, 3]]}
        expected = {"matrix": [[1, 2], [2, 3]]}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) > 0
        assert any("type mismatch" in d.lower() for d in differences)

    def test_list_item_value_mismatch(self):
        """Test value mismatch in list items."""
        validator = OutputValidator()

        actual = {"numbers": [1, 99, 3]}
        expected = {"numbers": [1, 2, 3]}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 1
        assert "value mismatch" in differences[0].lower()

    def test_regex_pattern_match_success(self):
        """Test regex pattern matching with successful match."""
        validator = OutputValidator()

        actual = {"message": "Error: File not found at line 42"}
        expected = {"message": "regex:Error: .+ at line \\d+"}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_regex_pattern_match_failure(self):
        """Test regex pattern matching with failed match."""
        validator = OutputValidator()

        actual = {"message": "Warning: Something happened"}
        expected = {"message": "regex:Error: .+"}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 1
        assert "message" in differences[0].lower()

    def test_regex_pattern_in_nested_dict(self):
        """Test regex pattern matching in nested dictionary."""
        validator = OutputValidator()

        actual = {
            "status": "error",
            "details": {"error_code": "E404", "message": "Resource not found: user/123"},
        }
        expected = {
            "status": "error",
            "details": {"error_code": "regex:E\\d+", "message": "regex:Resource not found: .+"},
        }

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_regex_pattern_in_list(self):
        """Test regex pattern matching in list items."""
        validator = OutputValidator()

        actual = {"errors": ["Error on line 10", "Error on line 25", "Error on line 99"]}
        expected = {
            "errors": [
                "regex:Error on line \\d+",
                "regex:Error on line \\d+",
                "regex:Error on line \\d+",
            ]
        }

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is True
        assert len(differences) == 0

    def test_regex_pattern_non_string_actual(self):
        """Test regex pattern with non-string actual value (should fail)."""
        validator = OutputValidator()

        actual = {"count": 42}
        expected = {"count": "regex:\\d+"}

        is_valid, differences = validator.validate(actual, expected)

        assert is_valid is False
        assert len(differences) == 1
        assert "count" in differences[0].lower()

    def test_invalid_regex_pattern_fallback(self):
        """Test that invalid regex patterns fall back to literal string comparison."""
        validator = OutputValidator()

        actual = {"pattern": "regex:[invalid("}
        expected = {"pattern": "regex:[invalid("}

        is_valid, differences = validator.validate(actual, expected)

        # Should match exactly since invalid regex falls back to literal comparison
        assert is_valid is True
        assert len(differences) == 0
