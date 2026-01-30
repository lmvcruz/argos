"""
Parsers for various code quality tools.

This package contains parsers that convert output from code quality tools
(flake8, black, pylint, etc.) into Anvil ValidationResult objects.
"""

from anvil.parsers.flake8_parser import Flake8Parser

__all__ = ["Flake8Parser"]
