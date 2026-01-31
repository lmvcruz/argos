"""
Utility modules for Anvil.

Provides common utilities for encoding, formatting, and other helpers.
"""

from anvil.utils.encoding import (
    SafeChars,
    configure_unicode_output,
    get_safe_chars,
    supports_unicode,
)

__all__ = [
    "SafeChars",
    "configure_unicode_output",
    "get_safe_chars",
    "supports_unicode",
]
