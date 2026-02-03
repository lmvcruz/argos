"""
Parsers for various code quality tools.

This package contains parsers that convert output from code quality tools
(flake8, black, pylint, etc.) into Anvil ValidationResult objects, and
parsers for coverage data (pytest-cov).
"""

from anvil.parsers.autoflake_parser import AutoflakeParser
from anvil.parsers.black_parser import BlackParser
from anvil.parsers.clang_tidy_parser import ClangTidyParser
from anvil.parsers.coverage_parser import CoverageParser
from anvil.parsers.cppcheck_parser import CppcheckParser
from anvil.parsers.flake8_parser import Flake8Parser
from anvil.parsers.isort_parser import IsortParser
from anvil.parsers.lint_parser import LintParser
from anvil.parsers.pylint_parser import PylintParser
from anvil.parsers.pytest_parser import PytestParser
from anvil.parsers.radon_parser import RadonParser
from anvil.parsers.vulture_parser import VultureParser

__all__ = [
    "Flake8Parser",
    "BlackParser",
    "IsortParser",
    "AutoflakeParser",
    "PylintParser",
    "PytestParser",
    "RadonParser",
    "VultureParser",
    "ClangTidyParser",
    "CppcheckParser",
    "CoverageParser",
    "LintParser",
]
