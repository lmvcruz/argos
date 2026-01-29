"""
Test suite for validator interface and base classes.

Tests the abstract Validator interface, ValidationResult dataclass,
and Issue dataclass according to Step 1.1 of the implementation plan.
"""

import pytest

from anvil.models.validator import Issue, ValidationResult, Validator


class TestValidationResult:
    """Test ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test ValidationResult dataclass creation and attributes."""
        result = ValidationResult(
            validator_name="test_validator",
            passed=True,
            errors=[],
            warnings=[],
            execution_time=1.5,
            files_checked=10,
        )

        assert result.validator_name == "test_validator"
        assert result.passed is True
        assert result.errors == []
        assert result.warnings == []
        assert result.execution_time == 1.5
        assert result.files_checked == 10

    def test_validation_result_with_errors(self):
        """Test ValidationResult with errors and warnings."""
        errors = [
            Issue(
                file_path="test.py",
                line_number=10,
                column_number=5,
                message="Error message",
                severity="error",
                rule_name="test-rule",
            )
        ]
        warnings = [
            Issue(
                file_path="test.py",
                line_number=20,
                column_number=1,
                message="Warning message",
                severity="warning",
                rule_name="test-warning",
            )
        ]

        result = ValidationResult(
            validator_name="test_validator",
            passed=False,
            errors=errors,
            warnings=warnings,
            execution_time=2.0,
            files_checked=5,
        )

        assert result.passed is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert result.errors[0].severity == "error"
        assert result.warnings[0].severity == "warning"

    def test_validation_result_to_dict(self):
        """Test ValidationResult serialization to dict."""
        result = ValidationResult(
            validator_name="test_validator",
            passed=True,
            errors=[],
            warnings=[],
            execution_time=1.5,
            files_checked=10,
        )

        result_dict = result.to_dict()

        assert isinstance(result_dict, dict)
        assert result_dict["validator_name"] == "test_validator"
        assert result_dict["passed"] is True
        assert result_dict["errors"] == []
        assert result_dict["warnings"] == []
        assert result_dict["execution_time"] == 1.5
        assert result_dict["files_checked"] == 10

    def test_validation_result_from_dict(self):
        """Test ValidationResult deserialization from dict."""
        data = {
            "validator_name": "test_validator",
            "passed": True,
            "errors": [],
            "warnings": [],
            "execution_time": 1.5,
            "files_checked": 10,
        }

        result = ValidationResult.from_dict(data)

        assert result.validator_name == "test_validator"
        assert result.passed is True
        assert result.execution_time == 1.5
        assert result.files_checked == 10

    def test_validation_result_equality(self):
        """Test ValidationResult equality comparison."""
        result1 = ValidationResult(
            validator_name="test_validator",
            passed=True,
            errors=[],
            warnings=[],
            execution_time=1.5,
            files_checked=10,
        )
        result2 = ValidationResult(
            validator_name="test_validator",
            passed=True,
            errors=[],
            warnings=[],
            execution_time=1.5,
            files_checked=10,
        )

        assert result1 == result2

    def test_validation_result_with_empty_lists(self):
        """Test ValidationResult with empty error/warning lists."""
        result = ValidationResult(
            validator_name="test_validator",
            passed=True,
            errors=[],
            warnings=[],
            execution_time=0.5,
            files_checked=0,
        )

        assert result.errors == []
        assert result.warnings == []
        assert result.passed is True


class TestIssue:
    """Test Issue dataclass."""

    def test_issue_creation_with_all_fields(self):
        """Test Issue dataclass creation with all fields."""
        issue = Issue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            message="Test error message",
            severity="error",
            rule_name="test-rule",
            error_code="E001",
        )

        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column_number == 5
        assert issue.message == "Test error message"
        assert issue.severity == "error"
        assert issue.rule_name == "test-rule"
        assert issue.error_code == "E001"

    def test_issue_creation_with_optional_fields(self):
        """Test Issue creation with optional fields as None."""
        issue = Issue(
            file_path="test.py",
            line_number=10,
            message="Test message",
            severity="warning",
        )

        assert issue.file_path == "test.py"
        assert issue.line_number == 10
        assert issue.column_number is None
        assert issue.rule_name is None
        assert issue.error_code is None

    def test_issue_severity_validation_error(self):
        """Test Issue severity validation (must be error/warning/info)."""
        # Valid severities
        for severity in ["error", "warning", "info"]:
            issue = Issue(
                file_path="test.py",
                line_number=1,
                message="Test",
                severity=severity,
            )
            assert issue.severity == severity

        # Invalid severity should raise ValueError
        with pytest.raises(ValueError, match="Severity must be one of"):
            Issue(
                file_path="test.py",
                line_number=1,
                message="Test",
                severity="invalid",
            )

    def test_issue_to_dict(self):
        """Test Issue serialization to dict."""
        issue = Issue(
            file_path="test.py",
            line_number=10,
            column_number=5,
            message="Test message",
            severity="error",
            rule_name="test-rule",
        )

        issue_dict = issue.to_dict()

        assert isinstance(issue_dict, dict)
        assert issue_dict["file_path"] == "test.py"
        assert issue_dict["line_number"] == 10
        assert issue_dict["severity"] == "error"


class TestValidator:
    """Test Validator abstract base class."""

    def test_validator_abstract_methods_raise_not_implemented(self):
        """Test Validator abstract methods raise NotImplementedError."""
        # Cannot instantiate abstract class directly
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            Validator()

    def test_validator_subclass_must_implement_methods(self):
        """Test that Validator subclass must implement all abstract methods."""

        class IncompleteValidator(Validator):
            """Incomplete validator missing implementations."""

        # Should not be able to instantiate without implementing abstract methods
        with pytest.raises(TypeError):
            IncompleteValidator()

    def test_validator_complete_subclass(self):
        """Test that complete Validator subclass can be instantiated."""

        class CompleteValidator(Validator):
            """Complete validator with all methods implemented."""

            def name(self):
                return "test_validator"

            def language(self):
                return "python"

            def validate(self, files, config):
                return ValidationResult(
                    validator_name="test_validator",
                    passed=True,
                    errors=[],
                    warnings=[],
                    execution_time=0.0,
                    files_checked=len(files),
                )

            def is_available(self):
                return True

        # Should be able to instantiate
        validator = CompleteValidator()
        assert validator.name() == "test_validator"
        assert validator.language() == "python"
        assert validator.is_available() is True

        # Should be able to call validate
        result = validator.validate(["test.py"], {})
        assert result.validator_name == "test_validator"
        assert result.passed is True
