"""
Test suite for all validator implementations.

Tests all validator classes to ensure they properly implement the Validator
interface and integrate correctly with their parsers.
"""

import pytest

from anvil.validators.autoflake_validator import AutoflakeValidator
from anvil.validators.black_validator import BlackValidator
from anvil.validators.clang_format_validator import ClangFormatValidator
from anvil.validators.clang_tidy_validator import ClangTidyValidator
from anvil.validators.cppcheck_validator import CppcheckValidator
from anvil.validators.cpplint_validator import CpplintValidator
from anvil.validators.flake8_validator import Flake8Validator
from anvil.validators.gtest_validator import GTestValidator
from anvil.validators.isort_validator import IsortValidator
from anvil.validators.iwyu_validator import IWYUValidator
from anvil.validators.pylint_validator import PylintValidator
from anvil.validators.pytest_validator import PytestValidator
from anvil.validators.radon_validator import RadonValidator
from anvil.validators.vulture_validator import VultureValidator


class TestPythonValidators:
    """Test all Python validators."""

    def test_flake8_validator_properties(self):
        """Test Flake8Validator has correct properties."""
        validator = Flake8Validator()
        assert validator.name == "flake8"
        assert validator.language == "python"
        assert "PEP 8" in validator.description or "style" in validator.description

    def test_flake8_validator_is_available(self):
        """Test Flake8Validator availability check."""
        validator = Flake8Validator()
        # Should return bool
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_black_validator_properties(self):
        """Test BlackValidator has correct properties."""
        validator = BlackValidator()
        assert validator.name == "black"
        assert validator.language == "python"
        assert "format" in validator.description.lower()

    def test_black_validator_is_available(self):
        """Test BlackValidator availability check."""
        validator = BlackValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_isort_validator_properties(self):
        """Test IsortValidator has correct properties."""
        validator = IsortValidator()
        assert validator.name == "isort"
        assert validator.language == "python"
        assert "import" in validator.description.lower()

    def test_isort_validator_is_available(self):
        """Test IsortValidator availability check."""
        validator = IsortValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_autoflake_validator_properties(self):
        """Test AutoflakeValidator has correct properties."""
        validator = AutoflakeValidator()
        assert validator.name == "autoflake"
        assert validator.language == "python"
        assert "unused" in validator.description.lower()

    def test_autoflake_validator_is_available(self):
        """Test AutoflakeValidator availability check."""
        validator = AutoflakeValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_pylint_validator_properties(self):
        """Test PylintValidator has correct properties."""
        validator = PylintValidator()
        assert validator.name == "pylint"
        assert validator.language == "python"
        assert (
            "static analyzer" in validator.description.lower()
            or "analysis" in validator.description.lower()
        )

    def test_pylint_validator_is_available(self):
        """Test PylintValidator availability check."""
        validator = PylintValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_radon_validator_properties(self):
        """Test RadonValidator has correct properties."""
        validator = RadonValidator()
        assert validator.name == "radon"
        assert validator.language == "python"
        assert "complexity" in validator.description.lower()

    def test_radon_validator_is_available(self):
        """Test RadonValidator availability check."""
        validator = RadonValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_vulture_validator_properties(self):
        """Test VultureValidator has correct properties."""
        validator = VultureValidator()
        assert validator.name == "vulture"
        assert validator.language == "python"
        assert "dead code" in validator.description.lower()

    def test_vulture_validator_is_available(self):
        """Test VultureValidator availability check."""
        validator = VultureValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_pytest_validator_properties(self):
        """Test PytestValidator has correct properties."""
        validator = PytestValidator()
        assert validator.name == "pytest"
        assert validator.language == "python"
        assert "test" in validator.description.lower()

    def test_pytest_validator_is_available(self):
        """Test PytestValidator availability check."""
        validator = PytestValidator()
        result = validator.is_available()
        assert isinstance(result, bool)


class TestCppValidators:
    """Test all C++ validators."""

    def test_clang_tidy_validator_properties(self):
        """Test ClangTidyValidator has correct properties."""
        validator = ClangTidyValidator()
        assert validator.name == "clang-tidy"
        assert validator.language == "cpp"
        assert "C++" in validator.description

    def test_clang_tidy_validator_is_available(self):
        """Test ClangTidyValidator availability check."""
        validator = ClangTidyValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_cppcheck_validator_properties(self):
        """Test CppcheckValidator has correct properties."""
        validator = CppcheckValidator()
        assert validator.name == "cppcheck"
        assert validator.language == "cpp"
        assert "C++" in validator.description

    def test_cppcheck_validator_is_available(self):
        """Test CppcheckValidator availability check."""
        validator = CppcheckValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_cpplint_validator_properties(self):
        """Test CpplintValidator has correct properties."""
        validator = CpplintValidator()
        assert validator.name == "cpplint"
        assert validator.language == "cpp"
        assert "Google" in validator.description or "style" in validator.description.lower()

    def test_cpplint_validator_is_available(self):
        """Test CpplintValidator availability check."""
        validator = CpplintValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_clang_format_validator_properties(self):
        """Test ClangFormatValidator has correct properties."""
        validator = ClangFormatValidator()
        assert validator.name == "clang-format"
        assert validator.language == "cpp"
        assert "format" in validator.description.lower()

    def test_clang_format_validator_is_available(self):
        """Test ClangFormatValidator availability check."""
        validator = ClangFormatValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_iwyu_validator_properties(self):
        """Test IWYUValidator has correct properties."""
        validator = IWYUValidator()
        assert validator.name == "iwyu"
        assert validator.language == "cpp"
        assert "include" in validator.description.lower()

    def test_iwyu_validator_is_available(self):
        """Test IWYUValidator availability check."""
        validator = IWYUValidator()
        result = validator.is_available()
        assert isinstance(result, bool)

    def test_gtest_validator_properties(self):
        """Test GTestValidator has correct properties."""
        validator = GTestValidator()
        assert validator.name == "gtest"
        assert validator.language == "cpp"
        assert "test" in validator.description.lower()

    def test_gtest_validator_is_available(self):
        """Test GTestValidator availability check."""
        validator = GTestValidator()
        result = validator.is_available()
        assert isinstance(result, bool)


class TestValidatorRegistration:
    """Test that all validators can be registered and used."""

    @pytest.fixture
    def all_validators(self):
        """Create instances of all validators."""
        return [
            # Python validators
            Flake8Validator(),
            BlackValidator(),
            IsortValidator(),
            AutoflakeValidator(),
            PylintValidator(),
            RadonValidator(),
            VultureValidator(),
            PytestValidator(),
            # C++ validators
            ClangTidyValidator(),
            CppcheckValidator(),
            CpplintValidator(),
            ClangFormatValidator(),
            IWYUValidator(),
            GTestValidator(),
        ]

    def test_all_validators_have_unique_names(self, all_validators):
        """Test that all validators have unique names."""
        names = [v.name for v in all_validators]
        assert len(names) == len(set(names)), "Validator names must be unique"

    def test_all_validators_have_valid_languages(self, all_validators):
        """Test that all validators have valid language assignments."""
        for validator in all_validators:
            assert validator.language in [
                "python",
                "cpp",
            ], f"Validator {validator.name} has invalid language: {validator.language}"

    def test_all_validators_have_descriptions(self, all_validators):
        """Test that all validators have non-empty descriptions."""
        for validator in all_validators:
            assert validator.description, f"Validator {validator.name} has empty description"
            assert (
                len(validator.description) > 10
            ), f"Validator {validator.name} description is too short"

    def test_all_validators_implement_is_available(self, all_validators):
        """Test that all validators implement is_available correctly."""
        for validator in all_validators:
            # Should return a boolean
            result = validator.is_available()
            assert isinstance(
                result, bool
            ), f"Validator {validator.name}.is_available() must return bool"

    def test_python_validators_count(self, all_validators):
        """Test that we have 8 Python validators."""
        python_validators = [v for v in all_validators if v.language == "python"]
        assert len(python_validators) == 8, "Should have 8 Python validators"

    def test_cpp_validators_count(self, all_validators):
        """Test that we have 6 C++ validators."""
        cpp_validators = [v for v in all_validators if v.language == "cpp"]
        assert len(cpp_validators) == 6, "Should have 6 C++ validators"


class TestValidatorIntegration:
    """Test validators integrate correctly with registry."""

    def test_validators_can_be_imported_from_registration(self):
        """Test that validators can be imported through registration module."""
        from anvil.core.validator_registration import (
            register_all_validators,
            register_cpp_validators,
            register_python_validators,
        )
        from anvil.core.validator_registry import ValidatorRegistry

        # All registration functions should be callable
        assert callable(register_python_validators)
        assert callable(register_cpp_validators)
        assert callable(register_all_validators)

        # Test registration works
        registry = ValidatorRegistry()
        register_all_validators(registry)

        # Should have all 14 validators registered
        all_validators = registry.list_all()
        assert len(all_validators) == 14, "Should have 14 validators registered"

        # Check Python validators
        python_validators = registry.get_validators_by_language("python")
        assert len(python_validators) == 8, "Should have 8 Python validators"

        # Check C++ validators
        cpp_validators = registry.get_validators_by_language("cpp")
        assert len(cpp_validators) == 6, "Should have 6 C++ validators"

    def test_all_validators_registered_by_name(self):
        """Test all validators are accessible by name after registration."""
        from anvil.core.validator_registration import register_all_validators
        from anvil.core.validator_registry import ValidatorRegistry

        registry = ValidatorRegistry()
        register_all_validators(registry)

        expected_names = [
            # Python
            "flake8",
            "black",
            "isort",
            "autoflake",
            "pylint",
            "radon",
            "vulture",
            "pytest",
            # C++
            "clang-tidy",
            "cppcheck",
            "cpplint",
            "clang-format",
            "iwyu",
            "gtest",
        ]

        for name in expected_names:
            validator = registry.get_validator(name)
            assert validator is not None, f"Validator {name} not found in registry"
            assert validator.name == name, f"Validator name mismatch: {validator.name} != {name}"
