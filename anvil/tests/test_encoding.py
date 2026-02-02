"""
Tests for encoding utilities.

This module tests Unicode detection, UTF-8 configuration, and safe character
handling across different terminal environments.
"""

from io import StringIO
from unittest.mock import MagicMock, patch

from anvil.utils.encoding import (
    SafeChars,
    configure_unicode_output,
    get_safe_chars,
    supports_unicode,
)


class TestSupportsUnicode:
    """Test Unicode support detection."""

    def test_supports_unicode_with_utf8_encoding(self):
        """Test Unicode support detection with UTF-8 encoding."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "utf-8"
            assert supports_unicode() is True

    def test_supports_unicode_with_utf16_encoding(self):
        """Test Unicode support detection with UTF-16 encoding."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "utf-16"
            assert supports_unicode() is True

    def test_supports_unicode_with_cp1252_encoding(self):
        """Test Unicode support detection with cp1252 (Windows) encoding."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "cp1252"
            # cp1252 cannot encode checkmark character
            assert supports_unicode() is False

    def test_supports_unicode_with_no_encoding_attribute(self):
        """Test Unicode support detection when stdout has no encoding."""
        mock_stdout = MagicMock(spec=[])  # No encoding attribute
        with patch("sys.stdout", mock_stdout):
            assert supports_unicode() is False

    def test_supports_unicode_with_none_encoding(self):
        """Test Unicode support detection when encoding is None."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = None
            assert supports_unicode() is False

    def test_supports_unicode_case_insensitive(self):
        """Test Unicode support detection is case-insensitive."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "UTF-8"  # Uppercase
            assert supports_unicode() is True


class TestConfigureUnicodeOutput:
    """Test UTF-8 output configuration."""

    def test_configure_unicode_output_with_reconfigure(self):
        """Test configure_unicode_output when reconfigure is available."""
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()

        with patch("sys.stdout", mock_stdout), patch("sys.stderr", mock_stderr):
            configure_unicode_output()

            # Verify reconfigure was called with correct arguments
            mock_stdout.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")
            mock_stderr.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")

    def test_configure_unicode_output_without_reconfigure(self):
        """Test configure_unicode_output when reconfigure is not available."""
        # Create mock without reconfigure method
        mock_stdout = MagicMock(spec=["write", "flush"])
        mock_stderr = MagicMock(spec=["write", "flush"])

        with patch("sys.stdout", mock_stdout), patch("sys.stderr", mock_stderr):
            # Should not raise AttributeError
            configure_unicode_output()

            # Verify no errors raised (function handles gracefully)
            assert True  # If we got here, no exception was raised

    def test_configure_unicode_output_with_attribute_error(self):
        """Test configure_unicode_output handles AttributeError gracefully."""
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.reconfigure.side_effect = AttributeError("Not available")
        mock_stderr.reconfigure.side_effect = AttributeError("Not available")

        with patch("sys.stdout", mock_stdout), patch("sys.stderr", mock_stderr):
            # Should not raise exception
            configure_unicode_output()
            assert True

    def test_configure_unicode_output_with_type_error(self):
        """Test configure_unicode_output handles TypeError gracefully."""
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.reconfigure.side_effect = TypeError("Invalid arguments")
        mock_stderr.reconfigure.side_effect = TypeError("Invalid arguments")

        with patch("sys.stdout", mock_stdout), patch("sys.stderr", mock_stderr):
            # Should not raise exception
            configure_unicode_output()
            assert True

    def test_configure_unicode_output_with_value_error(self):
        """Test configure_unicode_output handles ValueError gracefully."""
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stdout.reconfigure.side_effect = ValueError("Invalid encoding")
        mock_stderr.reconfigure.side_effect = ValueError("Invalid encoding")

        with patch("sys.stdout", mock_stdout), patch("sys.stderr", mock_stderr):
            # Should not raise exception
            configure_unicode_output()
            assert True

    def test_configure_unicode_output_stdout_succeeds_stderr_fails(self):
        """Test configure_unicode_output when stdout works but stderr fails."""
        mock_stdout = MagicMock()
        mock_stderr = MagicMock()
        mock_stderr.reconfigure.side_effect = AttributeError("Not available")

        with patch("sys.stdout", mock_stdout), patch("sys.stderr", mock_stderr):
            configure_unicode_output()

            # Verify stdout was configured
            mock_stdout.reconfigure.assert_called_once_with(encoding="utf-8", errors="replace")
            # stderr attempted but failed (caught internally)
            mock_stderr.reconfigure.assert_called_once()

    def test_configure_unicode_output_with_stringio(self):
        """Test configure_unicode_output with StringIO (pytest capture)."""
        mock_stdout = StringIO()
        mock_stderr = StringIO()

        with patch("sys.stdout", mock_stdout), patch("sys.stderr", mock_stderr):
            # StringIO doesn't have reconfigure, should handle gracefully
            configure_unicode_output()
            assert True


class TestSafeChars:
    """Test SafeChars class."""

    def test_safe_chars_unicode_mode(self):
        """Test SafeChars in Unicode mode."""
        chars = SafeChars(force_ascii=False)

        assert chars.check == "✓"
        assert chars.cross == "✗"
        assert chars.box_h == "─"
        assert chars.box_v == "│"
        assert chars.box_tl == "┌"
        assert chars.box_tr == "┐"
        assert chars.box_bl == "└"
        assert chars.box_br == "┘"
        assert chars.box_lt == "├"
        assert chars.box_rt == "┤"
        assert chars.box_tt == "┬"
        assert chars.box_bt == "┴"
        assert chars.box_cross == "┼"

    def test_safe_chars_ascii_mode(self):
        """Test SafeChars in ASCII mode."""
        chars = SafeChars(force_ascii=True)

        assert chars.check == "[PASS]"
        assert chars.cross == "[FAIL]"
        assert chars.box_h == "-"
        assert chars.box_v == "|"
        assert chars.box_tl == "+"
        assert chars.box_tr == "+"
        assert chars.box_bl == "+"
        assert chars.box_br == "+"
        assert chars.box_lt == "+"
        assert chars.box_rt == "+"
        assert chars.box_tt == "+"
        assert chars.box_bt == "+"
        assert chars.box_cross == "+"

    def test_safe_chars_auto_detect_unicode(self):
        """Test SafeChars auto-detection with Unicode support."""
        with patch("anvil.utils.encoding.supports_unicode", return_value=True):
            chars = SafeChars()
            assert chars.check == "✓"
            assert chars.box_h == "─"

    def test_safe_chars_auto_detect_no_unicode(self):
        """Test SafeChars auto-detection without Unicode support."""
        with patch("anvil.utils.encoding.supports_unicode", return_value=False):
            chars = SafeChars()
            assert chars.check == "[PASS]"
            assert chars.box_h == "-"

    def test_safe_chars_force_ascii_overrides_detection(self):
        """Test that force_ascii parameter overrides auto-detection."""
        with patch("anvil.utils.encoding.supports_unicode", return_value=True):
            chars = SafeChars(force_ascii=True)
            assert chars.check == "[PASS]"  # ASCII despite Unicode support

    def test_safe_chars_force_unicode_overrides_detection(self):
        """Test that force_ascii=False overrides auto-detection."""
        with patch("anvil.utils.encoding.supports_unicode", return_value=False):
            chars = SafeChars(force_ascii=False)
            assert chars.check == "✓"  # Unicode despite no support detected


class TestGetSafeChars:
    """Test get_safe_chars function."""

    def test_get_safe_chars_default(self):
        """Test get_safe_chars with default parameters."""
        chars = get_safe_chars()
        assert isinstance(chars, SafeChars)

    def test_get_safe_chars_caching(self):
        """Test that get_safe_chars returns cached instance."""
        # Clear any cached instance first
        import anvil.utils.encoding

        anvil.utils.encoding._default_chars = None

        chars1 = get_safe_chars()
        chars2 = get_safe_chars()
        assert chars1 is chars2  # Same instance

    def test_get_safe_chars_force_ascii_no_caching(self):
        """Test that force_ascii parameter bypasses cache."""
        chars1 = get_safe_chars(force_ascii=True)
        chars2 = get_safe_chars(force_ascii=True)
        assert chars1 is not chars2  # Different instances

    def test_get_safe_chars_force_ascii_true(self):
        """Test get_safe_chars with force_ascii=True."""
        chars = get_safe_chars(force_ascii=True)
        assert chars.check == "[PASS]"

    def test_get_safe_chars_force_ascii_false(self):
        """Test get_safe_chars with force_ascii=False."""
        chars = get_safe_chars(force_ascii=False)
        assert chars.check == "✓"


class TestEncodingIntegration:
    """Integration tests for encoding utilities."""

    def test_full_workflow_unicode_environment(self):
        """Test full workflow in a Unicode-capable environment."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "utf-8"

            # Configure output
            configure_unicode_output()
            mock_stdout.reconfigure.assert_called_once()

            # Get safe chars (should detect Unicode support)
            with patch("anvil.utils.encoding.supports_unicode", return_value=True):
                chars = SafeChars()
                assert chars.check == "✓"

    def test_full_workflow_ascii_environment(self):
        """Test full workflow in an ASCII-only environment."""
        with patch("sys.stdout") as mock_stdout:
            mock_stdout.encoding = "ascii"

            # Configure output (should handle gracefully)
            configure_unicode_output()

            # Get safe chars (should detect no Unicode support)
            with patch("anvil.utils.encoding.supports_unicode", return_value=False):
                chars = SafeChars()
                assert chars.check == "[PASS]"

    def test_pytest_capture_compatibility(self):
        """Test compatibility with pytest's output capture."""
        # Simulate pytest's capture
        mock_capture = StringIO()

        with patch("sys.stdout", mock_capture):
            # Should not raise errors
            configure_unicode_output()

            # Should gracefully fall back
            with patch("anvil.utils.encoding.supports_unicode", return_value=False):
                chars = SafeChars()
                assert chars.check == "[PASS]"
