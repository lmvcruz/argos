"""
Validator registration module.

This module provides functions to register all available validators
with the validator registry.
"""

from anvil.core.validator_registry import ValidatorRegistry

# Iteration 2: Python Linting/Formatting
from anvil.validators.autoflake_validator import AutoflakeValidator
from anvil.validators.black_validator import BlackValidator

# Iteration 6: C++ Formatting/Testing
from anvil.validators.clang_format_validator import ClangFormatValidator

# Iteration 5: C++ Static Analysis
from anvil.validators.clang_tidy_validator import ClangTidyValidator
from anvil.validators.cppcheck_validator import CppcheckValidator
from anvil.validators.cpplint_validator import CpplintValidator
from anvil.validators.flake8_validator import Flake8Validator
from anvil.validators.gtest_validator import GTestValidator
from anvil.validators.isort_validator import IsortValidator
from anvil.validators.iwyu_validator import IWYUValidator

# Iteration 3: Python Static Analysis
from anvil.validators.pylint_validator import PylintValidator

# Iteration 4: Python Testing
from anvil.validators.pytest_validator import PytestValidator
from anvil.validators.radon_validator import RadonValidator
from anvil.validators.vulture_validator import VultureValidator


def register_python_validators(registry: ValidatorRegistry) -> None:
    """
    Register all Python validators with the registry.

    Args:
        registry: The validator registry to register validators with
    """
    # Iteration 2: Linting/formatting validators
    registry.register(Flake8Validator())
    registry.register(BlackValidator())
    registry.register(IsortValidator())
    registry.register(AutoflakeValidator())

    # Iteration 3: Static analysis validators
    registry.register(PylintValidator())
    registry.register(RadonValidator())
    registry.register(VultureValidator())

    # Iteration 4: Testing validators
    registry.register(PytestValidator())


def register_cpp_validators(registry: ValidatorRegistry) -> None:
    """
    Register all C++ validators with the registry.

    Args:
        registry: The validator registry to register validators with
    """
    # Iteration 5: Static analysis validators
    registry.register(ClangTidyValidator())
    registry.register(CppcheckValidator())
    registry.register(CpplintValidator())

    # Iteration 6: Formatting/testing validators
    registry.register(ClangFormatValidator())
    registry.register(IWYUValidator())
    registry.register(GTestValidator())


def register_all_validators(registry: ValidatorRegistry) -> None:
    """
    Register all available validators with the registry.

    This function registers validators from all iterations:
    - Iteration 2: Python linting/formatting (flake8, black, isort, autoflake)
    - Iteration 3: Python static analysis (pylint, radon, vulture)
    - Iteration 4: Python testing (pytest)
    - Iteration 5: C++ static analysis (clang-tidy, cppcheck, cpplint)
    - Iteration 6: C++ formatting/testing (clang-format, iwyu, gtest)

    Args:
        registry: The validator registry to register validators with
    """
    # Register Python validators
    register_python_validators(registry)

    # Register C++ validators
    register_cpp_validators(registry)
