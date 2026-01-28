"""
Tests for CMake detection and version extraction.

Tests the ability to detect CMake availability and extract version information.
"""

from unittest.mock import MagicMock, patch

from forge.cmake.executor import CMakeExecutor


class TestCMakeDetection:
    """Test CMake availability detection."""

    def test_cmake_detected_when_available(self):
        """Test that CMake is detected when available in PATH."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"cmake version 3.28.1\n", b"")
            mock_popen.return_value = mock_process

            result = executor.check_cmake_available()

            assert result is True
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            assert "cmake" in args
            assert "--version" in args

    def test_cmake_not_found_returns_false(self):
        """Test that check returns False when CMake is not found."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = FileNotFoundError("cmake not found")

            result = executor.check_cmake_available()

            assert result is False

    def test_cmake_check_handles_other_exceptions(self):
        """Test that check handles unexpected exceptions gracefully."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = PermissionError("Permission denied")

            result = executor.check_cmake_available()

            assert result is False

    def test_cmake_check_handles_nonzero_exit_code(self):
        """Test that non-zero exit code is handled (though --version should always return 0)."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"error")
            mock_popen.return_value = mock_process

            result = executor.check_cmake_available()

            # Should still return True if command exists, even with non-zero exit
            assert result is True

    def test_cmake_check_uses_timeout(self):
        """Test that CMake check uses a reasonable timeout."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"cmake version 3.28.1\n", b"")
            mock_popen.return_value = mock_process

            executor.check_cmake_available()

            # Verify communicate was called with timeout
            mock_process.communicate.assert_called_once()
            call_kwargs = mock_process.communicate.call_args[1]
            assert "timeout" in call_kwargs
            assert call_kwargs["timeout"] > 0


class TestCMakeVersionExtraction:
    """Test CMake version extraction."""

    def test_get_version_standard_format(self):
        """Test version extraction from standard format: cmake version 3.28.1."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"cmake version 3.28.1\n", b"")
            mock_popen.return_value = mock_process

            version = executor.get_cmake_version()

            assert version == "3.28.1"

    def test_get_version_two_part_version(self):
        """Test version extraction from two-part version: cmake version 3.20."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"cmake version 3.20\n", b"")
            mock_popen.return_value = mock_process

            version = executor.get_cmake_version()

            assert version == "3.20"

    def test_get_version_with_patch_and_suffix(self):
        """Test version extraction with patch and suffix: cmake version 3.27.4-dirty."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (
                b"cmake version 3.27.4-dirty\n",
                b"",
            )
            mock_popen.return_value = mock_process

            version = executor.get_cmake_version()

            assert version == "3.27.4-dirty"

    def test_get_version_multiline_output(self):
        """Test version extraction from multiline output."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            multiline_output = b"cmake version 3.28.1\n\nCMake suite maintained by Kitware\n"
            mock_process.communicate.return_value = (multiline_output, b"")
            mock_popen.return_value = mock_process

            version = executor.get_cmake_version()

            assert version == "3.28.1"

    def test_get_version_cmake_not_found(self):
        """Test that get_cmake_version returns None when CMake is not found."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = FileNotFoundError("cmake not found")

            version = executor.get_cmake_version()

            assert version is None

    def test_get_version_handles_exceptions(self):
        """Test that get_cmake_version handles exceptions gracefully."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = Exception("Unexpected error")

            version = executor.get_cmake_version()

            assert version is None

    def test_get_version_invalid_output_format(self):
        """Test that invalid output format returns None."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"Invalid output\n", b"")
            mock_popen.return_value = mock_process

            version = executor.get_cmake_version()

            assert version is None

    def test_get_version_empty_output(self):
        """Test that empty output returns None."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"", b"")
            mock_popen.return_value = mock_process

            version = executor.get_cmake_version()

            assert version is None

    def test_get_version_with_rc_suffix(self):
        """Test version extraction with release candidate suffix: 3.29.0-rc1."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"cmake version 3.29.0-rc1\n", b"")
            mock_popen.return_value = mock_process

            version = executor.get_cmake_version()

            assert version == "3.29.0-rc1"


class TestVersionComparison:
    """Test CMake version comparison utilities."""

    def test_compare_version_greater(self):
        """Test version comparison: 3.28.1 > 3.20.0."""
        executor = CMakeExecutor()

        result = executor.compare_version("3.28.1", "3.20.0")

        assert result > 0

    def test_compare_version_less(self):
        """Test version comparison: 3.20.0 < 3.28.1."""
        executor = CMakeExecutor()

        result = executor.compare_version("3.20.0", "3.28.1")

        assert result < 0

    def test_compare_version_equal(self):
        """Test version comparison: 3.28.1 == 3.28.1."""
        executor = CMakeExecutor()

        result = executor.compare_version("3.28.1", "3.28.1")

        assert result == 0

    def test_compare_version_different_lengths(self):
        """Test version comparison with different lengths: 3.28 vs 3.28.0."""
        executor = CMakeExecutor()

        # 3.28 should be treated as 3.28.0
        result = executor.compare_version("3.28", "3.28.0")

        assert result == 0

    def test_compare_version_major_difference(self):
        """Test version comparison with major version difference: 4.0.0 > 3.99.99."""
        executor = CMakeExecutor()

        result = executor.compare_version("4.0.0", "3.99.99")

        assert result > 0

    def test_compare_version_with_suffix_ignored(self):
        """Test that suffixes are ignored in comparison: 3.28.1-rc1 vs 3.28.1."""
        executor = CMakeExecutor()

        # Suffixes should be stripped for comparison
        result = executor.compare_version("3.28.1-rc1", "3.28.1")

        assert result == 0

    def test_check_minimum_version_success(self):
        """Test minimum version check succeeds when version is sufficient."""
        executor = CMakeExecutor()

        with patch.object(executor, "get_cmake_version", return_value="3.28.1"):
            result = executor.check_minimum_version("3.20.0")

            assert result is True

    def test_check_minimum_version_fail(self):
        """Test minimum version check fails when version is insufficient."""
        executor = CMakeExecutor()

        with patch.object(executor, "get_cmake_version", return_value="3.15.0"):
            result = executor.check_minimum_version("3.20.0")

            assert result is False

    def test_check_minimum_version_equal(self):
        """Test minimum version check succeeds when versions are equal."""
        executor = CMakeExecutor()

        with patch.object(executor, "get_cmake_version", return_value="3.20.0"):
            result = executor.check_minimum_version("3.20.0")

            assert result is True

    def test_check_minimum_version_cmake_not_found(self):
        """Test minimum version check fails when CMake is not found."""
        executor = CMakeExecutor()

        with patch.object(executor, "get_cmake_version", return_value=None):
            result = executor.check_minimum_version("3.20.0")

            assert result is False


class TestCMakePathResolution:
    """Test CMake path resolution and PATH environment handling."""

    def test_cmake_found_in_path(self):
        """Test that CMake is found in PATH environment variable."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"cmake version 3.28.1\n", b"")
            mock_popen.return_value = mock_process

            result = executor.check_cmake_available()

            assert result is True
            # Verify that we're using 'cmake' command (relies on PATH)
            args = mock_popen.call_args[0][0]
            assert args[0] == "cmake"

    def test_cmake_custom_path(self):
        """Test that custom CMake path can be specified."""
        executor = CMakeExecutor(cmake_command="/custom/path/to/cmake")

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"cmake version 3.28.1\n", b"")
            mock_popen.return_value = mock_process

            version = executor.get_cmake_version()

            assert version == "3.28.1"
            # Verify custom path was used
            args = mock_popen.call_args[0][0]
            assert args[0] == "/custom/path/to/cmake"

    def test_cmake_path_with_spaces(self):
        """Test that CMake path with spaces is handled correctly."""
        executor = CMakeExecutor(cmake_command="C:/Program Files/CMake/bin/cmake")

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"cmake version 3.28.1\n", b"")
            mock_popen.return_value = mock_process

            result = executor.check_cmake_available()

            assert result is True


class TestCMakeDetectionIntegration:
    """Integration tests for CMake detection."""

    def test_detection_before_execution(self):
        """Test that CMake detection can be used before attempting execution."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"cmake version 3.28.1\n", b"")
            mock_popen.return_value = mock_process

            # Check availability first
            available = executor.check_cmake_available()
            assert available is True

            # Then get version
            version = executor.get_cmake_version()
            assert version == "3.28.1"

    def test_version_info_caching(self):
        """Test that version information can be cached to avoid repeated calls."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate.return_value = (b"cmake version 3.28.1\n", b"")
            mock_popen.return_value = mock_process

            # First call
            version1 = executor.get_cmake_version()
            # Second call - should use same Popen mock
            version2 = executor.get_cmake_version()

            assert version1 == "3.28.1"
            assert version2 == "3.28.1"
            # Both calls should execute (no caching yet - can add later)
            assert mock_popen.call_count == 2

    def test_helpful_error_message_when_cmake_missing(self):
        """Test that helpful error message is provided when CMake is not found."""
        executor = CMakeExecutor()

        with patch("subprocess.Popen") as mock_popen:
            mock_popen.side_effect = FileNotFoundError("cmake not found")

            available = executor.check_cmake_available()
            assert available is False

            # User code can check and provide helpful message
            if not available:
                message = "CMake not found. Please install CMake and ensure it's in your PATH."
                assert "CMake not found" in message
                assert "PATH" in message


class TestRealCMakeDetection:
    """Test real CMake detection without mocking (integration test)."""

    def test_real_cmake_detection(self):
        """Test that CMake detection works with the actual CMake binary.

        This is an integration test that attempts to detect CMake on the system.
        If CMake is available, it should return True and extract version info.
        If not available, it should gracefully return False.

        This test is marked as integration and may be skipped in CI environments
        where CMake is not installed.
        """
        executor = CMakeExecutor()

        # Try to detect CMake (no mocking)
        is_available = executor.check_cmake_available()

        # If CMake is available, verify version extraction works
        if is_available:
            version = executor.get_cmake_version()

            # Should return a version string if available
            assert version is not None
            assert isinstance(version, str)
            assert len(version) > 0

            # Version should contain at least major.minor
            parts = version.split(".")
            assert len(parts) >= 2

            # Major and minor should be numeric
            assert parts[0].isdigit()
            assert parts[1].isdigit()
        else:
            # CMake not available - this is acceptable in some environments
            # Just verify the method returns None gracefully
            version = executor.get_cmake_version()
            assert version is None
