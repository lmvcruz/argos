"""
Tests for the Validator Registry.

This module tests the validator registration, discovery, and plugin system.
"""

import pytest

from anvil.core.validator_registry import ValidatorRegistry
from anvil.models.validator import ValidationResult, Validator


class MockValidator(Validator):
    """Mock validator for testing."""

    def __init__(self, name: str, language: str, description: str = "Mock validator"):
        """Initialize mock validator."""
        self._name = name
        self._language = language
        self._description = description

    @property
    def name(self) -> str:
        """Return validator name."""
        return self._name

    @property
    def language(self) -> str:
        """Return validator language."""
        return self._language

    @property
    def description(self) -> str:
        """Return validator description."""
        return self._description

    def validate(self, files: list, config: dict) -> ValidationResult:
        """Mock validation that always passes."""
        return ValidationResult(
            validator_name=self.name,
            passed=True,
            errors=[],
            warnings=[],
            files_checked=len(files),
        )

    def is_available(self) -> bool:
        """Mock availability check that always returns True."""
        return True


@pytest.fixture
def registry():
    """Create a fresh registry for each test."""
    return ValidatorRegistry()


@pytest.fixture
def python_validator():
    """Create a mock Python validator."""
    return MockValidator(name="flake8", language="python", description="Python linter")


@pytest.fixture
def cpp_validator():
    """Create a mock C++ validator."""
    return MockValidator(name="clang-tidy", language="cpp", description="C++ static analyzer")


@pytest.fixture
def another_python_validator():
    """Create another mock Python validator."""
    return MockValidator(name="black", language="python", description="Code formatter")


class TestValidatorRegistration:
    """Test validator registration functionality."""

    def test_register_validator_by_language(self, registry, python_validator):
        """Test registering a validator for a specific language."""
        registry.register(python_validator)

        validators = registry.get_validators_by_language("python")
        assert len(validators) == 1
        assert validators[0].name == "flake8"

    def test_register_multiple_validators_same_language(
        self, registry, python_validator, another_python_validator
    ):
        """Test registering multiple validators for the same language."""
        registry.register(python_validator)
        registry.register(another_python_validator)

        validators = registry.get_validators_by_language("python")
        assert len(validators) == 2
        names = [v.name for v in validators]
        assert "flake8" in names
        assert "black" in names

    def test_register_validators_different_languages(
        self, registry, python_validator, cpp_validator
    ):
        """Test registering validators for different languages."""
        registry.register(python_validator)
        registry.register(cpp_validator)

        python_validators = registry.get_validators_by_language("python")
        cpp_validators = registry.get_validators_by_language("cpp")

        assert len(python_validators) == 1
        assert len(cpp_validators) == 1
        assert python_validators[0].name == "flake8"
        assert cpp_validators[0].name == "clang-tidy"

    def test_register_duplicate_validator_raises_error(self, registry, python_validator):
        """Test that registering a duplicate validator raises an error."""
        registry.register(python_validator)

        duplicate = MockValidator(name="flake8", language="python", description="Duplicate")

        with pytest.raises(ValueError, match="already registered"):
            registry.register(duplicate)


class TestValidatorRetrieval:
    """Test validator retrieval functionality."""

    def test_get_validators_by_language(self, registry, python_validator, another_python_validator):
        """Test getting all validators for a specific language."""
        registry.register(python_validator)
        registry.register(another_python_validator)

        validators = registry.get_validators_by_language("python")
        assert len(validators) == 2

    def test_get_validators_by_nonexistent_language(self, registry):
        """Test getting validators for a language with no registered validators."""
        validators = registry.get_validators_by_language("rust")
        assert validators == []

    def test_get_validator_by_name(self, registry, python_validator):
        """Test getting a specific validator by name."""
        registry.register(python_validator)

        validator = registry.get_validator("flake8")
        assert validator is not None
        assert validator.name == "flake8"
        assert validator.language == "python"

    def test_get_nonexistent_validator_raises_error(self, registry):
        """Test that getting a nonexistent validator raises an error."""
        with pytest.raises(KeyError, match="not found"):
            registry.get_validator("nonexistent")

    def test_get_validator_case_sensitive(self, registry, python_validator):
        """Test that validator names are case-sensitive."""
        registry.register(python_validator)

        with pytest.raises(KeyError):
            registry.get_validator("Flake8")


class TestValidatorAvailability:
    """Test validator availability checking."""

    def test_validator_availability_check_exists(self, registry, python_validator):
        """Test checking if a validator is available."""
        registry.register(python_validator)

        assert registry.is_available("flake8") is True

    def test_validator_availability_check_not_exists(self, registry):
        """Test checking if a non-registered validator is available."""
        assert registry.is_available("nonexistent") is False


class TestValidatorListing:
    """Test validator listing functionality."""

    def test_list_all_registered_validators(self, registry, python_validator, cpp_validator):
        """Test listing all registered validators."""
        registry.register(python_validator)
        registry.register(cpp_validator)

        all_validators = registry.list_all()
        assert len(all_validators) == 2

        names = [v.name for v in all_validators]
        assert "flake8" in names
        assert "clang-tidy" in names

    def test_list_all_empty_registry(self, registry):
        """Test listing all validators when registry is empty."""
        all_validators = registry.list_all()
        assert all_validators == []

    def test_list_validators_for_specific_language(
        self, registry, python_validator, another_python_validator, cpp_validator
    ):
        """Test listing validators for a specific language."""
        registry.register(python_validator)
        registry.register(another_python_validator)
        registry.register(cpp_validator)

        python_validators = registry.get_validators_by_language("python")
        assert len(python_validators) == 2

        cpp_validators = registry.get_validators_by_language("cpp")
        assert len(cpp_validators) == 1


class TestValidatorOrdering:
    """Test that validator ordering is deterministic."""

    def test_validator_ordering_deterministic(self, registry):
        """Test that validators are returned in a deterministic order."""
        # Register validators in specific order
        validators_to_register = [
            MockValidator("zebra", "python", "Last alphabetically"),
            MockValidator("alpha", "python", "First alphabetically"),
            MockValidator("beta", "python", "Second alphabetically"),
        ]

        for validator in validators_to_register:
            registry.register(validator)

        # Get validators multiple times
        result1 = registry.get_validators_by_language("python")
        result2 = registry.get_validators_by_language("python")

        # Should be same order both times
        names1 = [v.name for v in result1]
        names2 = [v.name for v in result2]
        assert names1 == names2

        # Should be alphabetically sorted
        assert names1 == ["alpha", "beta", "zebra"]


class TestValidatorMetadata:
    """Test validator metadata functionality."""

    def test_get_validator_metadata(self, registry, python_validator):
        """Test getting metadata for a registered validator."""
        registry.register(python_validator)

        metadata = registry.get_metadata("flake8")
        assert metadata is not None
        assert metadata.name == "flake8"
        assert metadata.language == "python"
        assert metadata.description == "Python linter"

    def test_get_metadata_for_nonexistent_validator(self, registry):
        """Test getting metadata for a validator that doesn't exist."""
        with pytest.raises(KeyError):
            registry.get_metadata("nonexistent")

    def test_list_all_metadata(self, registry, python_validator, another_python_validator):
        """Test listing metadata for all registered validators."""
        registry.register(python_validator)
        registry.register(another_python_validator)

        all_metadata = registry.list_all_metadata()
        assert len(all_metadata) == 2

        names = [m.name for m in all_metadata]
        assert "flake8" in names
        assert "black" in names

        descriptions = [m.description for m in all_metadata]
        assert "Python linter" in descriptions
        assert "Code formatter" in descriptions


class TestValidatorFiltering:
    """Test filtering validators based on configuration."""

    def test_filter_validators_by_enabled_status(self, registry):
        """Test filtering validators by their enabled status from config."""
        # Register multiple validators
        validators_to_register = [
            MockValidator("flake8", "python", "Linter"),
            MockValidator("black", "python", "Formatter"),
            MockValidator("pylint", "python", "Static analyzer"),
        ]

        for validator in validators_to_register:
            registry.register(validator)

        # Simulate config that only enables flake8 and black
        enabled_names = ["flake8", "black"]

        enabled_validators = registry.filter_by_names(enabled_names)
        assert len(enabled_validators) == 2

        names = [v.name for v in enabled_validators]
        assert "flake8" in names
        assert "black" in names
        assert "pylint" not in names

    def test_filter_by_language_and_names(self, registry):
        """Test filtering by both language and specific validator names."""
        # Register validators for different languages
        registry.register(MockValidator("flake8", "python", "Python linter"))
        registry.register(MockValidator("black", "python", "Python formatter"))
        registry.register(MockValidator("clang-tidy", "cpp", "C++ analyzer"))

        # Filter for Python validators, but only flake8
        enabled_names = ["flake8", "clang-tidy"]
        python_validators = registry.get_validators_by_language("python")
        filtered = [v for v in python_validators if v.name in enabled_names]

        assert len(filtered) == 1
        assert filtered[0].name == "flake8"


class TestRegistrySingleton:
    """Test that registry can be used as a singleton if needed."""

    def test_multiple_registry_instances_independent(self):
        """Test that multiple registry instances are independent."""
        registry1 = ValidatorRegistry()
        registry2 = ValidatorRegistry()

        validator1 = MockValidator("flake8", "python", "Linter")
        registry1.register(validator1)

        # registry2 should be empty
        assert len(registry2.list_all()) == 0
        # registry1 should have one validator
        assert len(registry1.list_all()) == 1


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_get_validators_with_empty_language_string(self, registry):
        """Test getting validators with empty language string."""
        validators = registry.get_validators_by_language("")
        assert validators == []

    def test_register_validator_with_empty_name_raises_error(self, registry):
        """Test that registering a validator with empty name raises an error."""
        invalid_validator = MockValidator("", "python", "Invalid")

        with pytest.raises(ValueError, match="name cannot be empty"):
            registry.register(invalid_validator)

    def test_register_validator_with_empty_language_raises_error(self, registry):
        """Test that registering a validator with empty language raises an error."""
        invalid_validator = MockValidator("test", "", "Invalid")

        with pytest.raises(ValueError, match="language cannot be empty"):
            registry.register(invalid_validator)

    def test_unregister_validator(self, registry, python_validator):
        """Test unregistering a validator."""
        registry.register(python_validator)
        assert registry.is_available("flake8") is True

        registry.unregister("flake8")
        assert registry.is_available("flake8") is False

    def test_unregister_nonexistent_validator_raises_error(self, registry):
        """Test that unregistering a nonexistent validator raises an error."""
        with pytest.raises(KeyError, match="not found"):
            registry.unregister("nonexistent")

    def test_clear_registry(self, registry, python_validator, cpp_validator):
        """Test clearing all validators from the registry."""
        registry.register(python_validator)
        registry.register(cpp_validator)

        assert len(registry.list_all()) == 2

        registry.clear()

        assert len(registry.list_all()) == 0
