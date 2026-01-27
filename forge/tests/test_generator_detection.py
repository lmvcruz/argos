"""
Test suite for CMake generator detection and selection.

This module tests the CMakeParameterManager's ability to:
- Detect available CMake generators on different platforms
- Select appropriate generator based on availability
- Honor explicit generator specification from user
- Validate generator availability
- Provide sensible fallbacks

Uses mocking for cross-platform testing.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from forge.cmake.parameter_manager import CMakeParameterManager
from forge.models.arguments import ForgeArguments


class TestNinjaDetection:
    """Test Ninja generator detection and selection."""

    def test_ninja_selected_when_available(self):
        """Test Ninja is preferred when available."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ninja"
            generator = manager.detect_generator()

        assert generator == "Ninja"
        mock_which.assert_called_with("ninja")

    def test_ninja_not_selected_when_unavailable(self):
        """Test Ninja is not selected when not in PATH."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with patch("platform.system") as mock_system:
                mock_system.return_value = "Linux"
                generator = manager.detect_generator()

        assert generator != "Ninja"

    def test_ninja_detection_case_insensitive(self):
        """Test Ninja detection works regardless of case."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ninja"
            generator = manager.detect_generator()

        assert generator.lower() == "ninja"


class TestUnixMakefilesFallback:
    """Test Unix Makefiles fallback on Linux/macOS."""

    def test_unix_makefiles_on_linux_without_ninja(self):
        """Test Unix Makefiles is used on Linux when Ninja unavailable."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None  # Ninja not available
            with patch("platform.system") as mock_system:
                mock_system.return_value = "Linux"
                generator = manager.detect_generator()

        assert generator == "Unix Makefiles"

    def test_unix_makefiles_on_macos_without_ninja(self):
        """Test Unix Makefiles is used on macOS when Ninja unavailable."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with patch("platform.system") as mock_system:
                mock_system.return_value = "Darwin"
                generator = manager.detect_generator()

        assert generator == "Unix Makefiles"

    def test_unix_makefiles_not_used_on_windows(self):
        """Test Unix Makefiles is not selected on Windows."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with patch("platform.system") as mock_system:
                mock_system.return_value = "Windows"
                generator = manager.detect_generator()

        assert generator != "Unix Makefiles"


class TestVisualStudioDetection:
    """Test Visual Studio generator detection on Windows."""

    def test_visual_studio_on_windows_without_ninja(self):
        """Test Visual Studio is used on Windows when Ninja unavailable."""
        args = ForgeArguments(
            source_dir=Path("C:/source"),
            build_dir=Path("C:/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with patch("platform.system") as mock_system:
                mock_system.return_value = "Windows"
                generator = manager.detect_generator()

        # Should be some version of Visual Studio
        assert "Visual Studio" in generator

    def test_visual_studio_version_detection(self):
        """Test Visual Studio version is detected correctly."""
        args = ForgeArguments(
            source_dir=Path("C:/source"),
            build_dir=Path("C:/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with patch("platform.system") as mock_system:
                mock_system.return_value = "Windows"
                with patch(
                    "forge.cmake.parameter_manager.CMakeParameterManager._detect_vs_version"
                ) as mock_vs:
                    mock_vs.return_value = "17 2022"
                    generator = manager.detect_generator()

        assert generator == "Visual Studio 17 2022"

    def test_visual_studio_not_used_on_unix(self):
        """Test Visual Studio is not selected on Unix systems."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with patch("platform.system") as mock_system:
                mock_system.return_value = "Linux"
                generator = manager.detect_generator()

        assert "Visual Studio" not in generator

    def test_nmake_fallback_when_vs_not_found(self):
        """Test NMake Makefiles is used when Visual Studio not detected."""
        args = ForgeArguments(
            source_dir=Path("C:/source"),
            build_dir=Path("C:/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            with patch("platform.system") as mock_system:
                mock_system.return_value = "Windows"
                with patch(
                    "forge.cmake.parameter_manager.CMakeParameterManager._detect_vs_version"
                ) as mock_vs:
                    mock_vs.return_value = None  # No VS found
                    generator = manager.detect_generator()

        assert generator == "NMake Makefiles"


class TestExplicitGeneratorSpecification:
    """Test explicit generator specification overrides detection."""

    def test_explicit_generator_overrides_detection(self):
        """Test -G argument in cmake_args overrides auto-detection."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-GNinja Multi-Config"],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        # Should not call detect_generator
        generator = manager.get_generator()
        assert generator == "Ninja Multi-Config"

    def test_explicit_generator_with_spaces(self):
        """Test -G with generator name containing spaces."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-GUnix Makefiles"],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        generator = manager.get_generator()
        assert generator == "Unix Makefiles"

    def test_explicit_generator_separate_arg(self):
        """Test -G and generator name as separate arguments."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-G", "Ninja"],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        generator = manager.get_generator()
        assert generator == "Ninja"

    def test_explicit_generator_not_overridden_by_detection(self):
        """Test explicit generator is not replaced by detected one."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-GMake"],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ninja"  # Ninja available
            generator = manager.get_generator()

        # Should still use explicit Make, not Ninja
        assert generator == "Make"


class TestGeneratorValidation:
    """Test generator validation and error handling."""

    def test_invalid_generator_raises_error(self):
        """Test invalid generator name raises ValueError."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-GInvalidGenerator"],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with pytest.raises(ValueError, match="Invalid CMake generator"):
            manager.validate_generator()

    def test_valid_generator_passes_validation(self):
        """Test valid generator passes validation."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-GNinja"],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        # Should not raise
        manager.validate_generator()

    def test_empty_generator_name_raises_error(self):
        """Test empty generator name raises error."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-G"],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with pytest.raises(ValueError, match="Empty generator"):
            manager.get_generator()

    def test_empty_generator_after_g_flag(self):
        """Test -G with no following argument raises error."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-G"],  # -G with nothing after
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with pytest.raises(ValueError, match="Empty generator name after -G flag"):
            manager.get_generator()

    def test_empty_generator_string_after_g(self):
        """Test -G with empty string raises error."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-G", ""],  # Empty string after -G
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with pytest.raises(ValueError, match="Empty generator name"):
            manager.get_generator()


class TestGeneratorAvailability:
    """Test generator availability checking."""

    def test_check_generator_available_with_ninja(self):
        """Test is_generator_available returns True for Ninja when installed."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ninja"
            available = manager.is_generator_available("Ninja")

        assert available is True

    def test_check_generator_unavailable(self):
        """Test is_generator_available returns False when not installed."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            available = manager.is_generator_available("Ninja")

        assert available is False

    def test_unix_makefiles_always_available_on_unix(self):
        """Test Unix Makefiles is considered available on Unix systems."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Linux"
            available = manager.is_generator_available("Unix Makefiles")

        assert available is True

    def test_visual_studio_availability_on_windows(self):
        """Test Visual Studio availability check on Windows."""
        args = ForgeArguments(
            source_dir=Path("C:/source"),
            build_dir=Path("C:/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Windows"
            with patch(
                "forge.cmake.parameter_manager.CMakeParameterManager._detect_vs_version"
            ) as mock_vs:
                mock_vs.return_value = "17 2022"
                available = manager.is_generator_available("Visual Studio 17 2022")

        assert available is True

    def test_visual_studio_not_available_on_unix(self):
        """Test Visual Studio is not available on Unix systems."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Linux"
            available = manager.is_generator_available("Visual Studio 17 2022")

        assert available is False

    def test_nmake_available_on_windows(self):
        """Test NMake Makefiles is available on Windows."""
        args = ForgeArguments(
            source_dir=Path("C:/source"),
            build_dir=Path("C:/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Windows"
            available = manager.is_generator_available("NMake Makefiles")

        assert available is True

    def test_nmake_not_available_on_unix(self):
        """Test NMake Makefiles is not available on Unix systems."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Linux"
            available = manager.is_generator_available("NMake Makefiles")

        assert available is False

    def test_unknown_generator_unavailable(self):
        """Test unknown generator is considered unavailable."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        available = manager.is_generator_available("UnknownGenerator")
        assert available is False


class TestPlatformSpecificBehavior:
    """Test platform-specific generator selection logic."""

    def test_generator_priority_on_linux(self):
        """Test generator priority: Ninja > Unix Makefiles on Linux."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Linux"

            # First with Ninja available
            with patch("shutil.which") as mock_which:
                mock_which.return_value = "/usr/bin/ninja"
                generator = manager.detect_generator()
                assert generator == "Ninja"

            # Then without Ninja
            with patch("shutil.which") as mock_which:
                mock_which.return_value = None
                generator = manager.detect_generator()
                assert generator == "Unix Makefiles"

    def test_generator_priority_on_windows(self):
        """Test generator priority: Ninja > Visual Studio on Windows."""
        args = ForgeArguments(
            source_dir=Path("C:/source"),
            build_dir=Path("C:/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "Windows"

            # First with Ninja available
            with patch("shutil.which") as mock_which:
                mock_which.return_value = "C:/ninja.exe"
                generator = manager.detect_generator()
                assert generator == "Ninja"

            # Then without Ninja
            with patch("shutil.which") as mock_which:
                mock_which.return_value = None
                with patch(
                    "forge.cmake.parameter_manager.CMakeParameterManager._detect_vs_version"
                ) as mock_vs:
                    mock_vs.return_value = "17 2022"
                    generator = manager.detect_generator()
                    assert generator == "Visual Studio 17 2022"

    def test_unsupported_platform_fallback(self):
        """Test fallback behavior on unsupported platforms."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("platform.system") as mock_system:
            mock_system.return_value = "FreeBSD"
            with patch("shutil.which") as mock_which:
                mock_which.return_value = None
                generator = manager.detect_generator()

        # Should fallback to Unix Makefiles for unknown Unix-like systems
        assert generator == "Unix Makefiles"


class TestGeneratorInCommandGeneration:
    """Test generator integration with command generation."""

    def test_detected_generator_in_configure_command(self):
        """Test detected generator is added to configure command."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=[],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/usr/bin/ninja"
            command = manager.get_configure_command()

        assert "-G" in command
        ninja_index = command.index("-G")
        assert command[ninja_index + 1] == "Ninja"

    def test_explicit_generator_preserved_in_command(self):
        """Test explicit -G argument is preserved in command."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-G", "Unix Makefiles"],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        command = manager.get_configure_command()

        assert "-G" in command
        g_index = command.index("-G")
        assert command[g_index + 1] == "Unix Makefiles"

    def test_generator_not_duplicated_in_command(self):
        """Test generator -G flag is not duplicated."""
        args = ForgeArguments(
            source_dir=Path("/source"),
            build_dir=Path("/build"),
            cmake_args=["-GNinja"],
            build_args=[],
        )
        manager = CMakeParameterManager(args)

        command = manager.get_configure_command()

        # Count -G occurrences
        g_count = sum(1 for arg in command if arg.startswith("-G") or arg == "-G")
        assert g_count == 1
