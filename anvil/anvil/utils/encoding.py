"""
Encoding utilities for cross-platform Unicode support.

This module provides utilities to detect Unicode support and provide
ASCII fallbacks for characters that may not be supported on all platforms.
"""

import sys
from typing import Optional


def supports_unicode() -> bool:
    """
    Check if the current terminal/console supports Unicode output.

    Returns:
        True if Unicode is supported, False otherwise
    """
    # Check if stdout encoding can handle Unicode
    if not hasattr(sys.stdout, "encoding"):
        return False

    encoding = sys.stdout.encoding
    if encoding is None:
        return False

    # Common encodings that support Unicode
    unicode_encodings = ["utf-8", "utf8", "utf-16", "utf16"]

    # Windows cmd.exe typically uses cp1252, cp437, etc.
    # which don't support Unicode box-drawing characters
    if encoding.lower() in unicode_encodings:
        return True

    # Try to encode a test Unicode character
    try:
        "✓".encode(encoding)
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def configure_unicode_output():
    """
    Configure stdout and stderr to use UTF-8 encoding if possible.

    This is particularly important on Windows where the default encoding
    is often cp1252 or cp437.
    """
    try:
        # Try to reconfigure stdout and stderr to use UTF-8
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, Exception):
        # Reconfigure not available or failed, use fallback
        pass


class SafeChars:
    """
    Provides Unicode characters with ASCII fallbacks.

    Automatically detects if Unicode is supported and returns
    appropriate characters.
    """

    def __init__(self, force_ascii: Optional[bool] = None):
        """
        Initialize SafeChars.

        Args:
            force_ascii: Force ASCII mode (True) or Unicode mode (False).
                        If None, auto-detect based on terminal capability.
        """
        if force_ascii is None:
            self._use_unicode = supports_unicode()
        else:
            self._use_unicode = not force_ascii

    @property
    def check(self) -> str:
        """Checkmark character."""
        return "✓" if self._use_unicode else "[PASS]"

    @property
    def cross(self) -> str:
        """Cross/X character."""
        return "✗" if self._use_unicode else "[FAIL]"

    @property
    def box_h(self) -> str:
        """Horizontal box line."""
        return "─" if self._use_unicode else "-"

    @property
    def box_v(self) -> str:
        """Vertical box line."""
        return "│" if self._use_unicode else "|"

    @property
    def box_tl(self) -> str:
        """Box top-left corner."""
        return "┌" if self._use_unicode else "+"

    @property
    def box_tr(self) -> str:
        """Box top-right corner."""
        return "┐" if self._use_unicode else "+"

    @property
    def box_bl(self) -> str:
        """Box bottom-left corner."""
        return "└" if self._use_unicode else "+"

    @property
    def box_br(self) -> str:
        """Box bottom-right corner."""
        return "┘" if self._use_unicode else "+"

    @property
    def box_lt(self) -> str:
        """Box left T-junction."""
        return "├" if self._use_unicode else "+"

    @property
    def box_rt(self) -> str:
        """Box right T-junction."""
        return "┤" if self._use_unicode else "+"

    @property
    def box_tt(self) -> str:
        """Box top T-junction."""
        return "┬" if self._use_unicode else "+"

    @property
    def box_bt(self) -> str:
        """Box bottom T-junction."""
        return "┴" if self._use_unicode else "+"

    @property
    def box_cross(self) -> str:
        """Box cross/plus."""
        return "┼" if self._use_unicode else "+"


# Global instance for convenience
_default_chars: Optional[SafeChars] = None


def get_safe_chars(force_ascii: Optional[bool] = None) -> SafeChars:
    """
    Get a SafeChars instance.

    Args:
        force_ascii: Force ASCII mode. If None, use cached default instance.

    Returns:
        SafeChars instance
    """
    global _default_chars

    if force_ascii is None and _default_chars is not None:
        return _default_chars

    chars = SafeChars(force_ascii=force_ascii)

    if force_ascii is None:
        _default_chars = chars

    return chars
