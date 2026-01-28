"""
Tests for configuration output inspection.

Tests the BuildInspector's ability to extract metadata from CMake configure output.
"""

from pathlib import Path

import pytest

from forge.inspector.build_inspector import BuildInspector
from forge.models.metadata import ConfigureMetadata


# Helper to create inspector instance
def get_inspector():
    """Create a BuildInspector instance for testing."""
    return BuildInspector()


@pytest.fixture
def fixtures_dir():
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures" / "outputs"


@pytest.fixture
def linux_output(fixtures_dir):
    """Load Linux configure output fixture."""
    return (fixtures_dir / "configure_linux_ninja.txt").read_text()


@pytest.fixture
def windows_output(fixtures_dir):
    """Load Windows configure output fixture."""
    return (fixtures_dir / "configure_windows_msvc.txt").read_text()


@pytest.fixture
def macos_output(fixtures_dir):
    """Load macOS configure output fixture."""
    return (fixtures_dir / "configure_macos_clang.txt").read_text()


@pytest.fixture
def minimal_output(fixtures_dir):
    """Load minimal configure output fixture."""
    return (fixtures_dir / "configure_minimal.txt").read_text()


@pytest.fixture
def multiple_packages_output(fixtures_dir):
    """Load configure output with multiple packages."""
    return (fixtures_dir / "configure_multiple_packages.txt").read_text()


class TestCMakeVersionExtraction:
    """Test CMake version extraction from configure output."""

    def test_extract_cmake_version_from_linux_output(self, linux_output):
        """Test extraction of CMake version from Linux output."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(linux_output)

        assert metadata.cmake_version == "3.28.1"

    def test_extract_cmake_version_from_windows_output(self, windows_output):
        """Test extraction of CMake version from Windows output."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(windows_output)

        assert metadata.cmake_version == "3.27.0"

    def test_extract_cmake_version_from_macos_output(self, macos_output):
        """Test extraction of CMake version from macOS output."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(macos_output)

        assert metadata.cmake_version == "3.26.4"

    def test_cmake_version_none_when_missing(self, minimal_output):
        """Test that cmake_version is None when not found in output."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(minimal_output)

        assert metadata.cmake_version is None


class TestGeneratorDetection:
    """Test generator detection from configure output."""

    def test_detect_visual_studio_generator(self, windows_output):
        """Test detection of Visual Studio generator."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(windows_output)

        assert metadata.generator == "Visual Studio 17 2022"

    def test_generator_none_when_not_specified(self, linux_output):
        """Test that generator is None when not explicitly mentioned."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(linux_output)

        # Ninja or Unix Makefiles might be default but not printed
        assert metadata.generator is None or metadata.generator in [
            "Ninja",
            "Unix Makefiles",
        ]


class TestCompilerDetection:
    """Test compiler detection from configure output."""

    def test_detect_gccompiler_c(self, linux_output):
        """Test detection of GCC compiler."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(linux_output)

        assert metadata.compiler_c == "GNU"
        assert metadata.compiler_cxx == "GNU"

    def test_detect_msvcompiler_c(self, windows_output):
        """Test detection of MSVC compiler."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(windows_output)

        assert metadata.compiler_c == "MSVC"
        assert metadata.compiler_cxx == "MSVC"

    def test_detect_clang_compiler(self, macos_output):
        """Test detection of Clang compiler."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(macos_output)

        assert metadata.compiler_c == "AppleClang"
        assert metadata.compiler_cxx == "AppleClang"

    def test_compiler_none_when_missing(self):
        """Test that compiler is None when not found in output."""
        inspector = BuildInspector()
        output = "-- Configuring done\n-- Generating done"
        metadata = inspector.inspect_configure_output(output)

        assert metadata.compiler_c is None
        assert metadata.compiler_cxx is None


class TestSystemInfoExtraction:
    """Test system information extraction from configure output."""

    def test_extract_linux_system_info(self, linux_output):
        """Test extraction of Linux system information."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(linux_output)

        assert metadata.system_name == "Linux"
        assert metadata.system_processor == "x86_64"

    def test_extract_windows_system_info(self, windows_output):
        """Test extraction of Windows system information."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(windows_output)

        assert metadata.system_name == "Windows"
        assert metadata.system_processor == "AMD64"

    def test_extract_macos_system_info(self, macos_output):
        """Test extraction of macOS system information."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(macos_output)

        assert metadata.system_name == "Darwin"
        assert metadata.system_processor == "arm64"

    def test_system_info_none_when_missing(self):
        """Test that system info is None when not found in output."""
        inspector = BuildInspector()
        output = "-- Configuring done\n-- Generating done"
        metadata = inspector.inspect_configure_output(output)

        assert metadata.system_name is None
        assert metadata.system_processor is None


class TestFoundPackagesDetection:
    """Test detection of found packages from configure output."""

    def test_detect_single_package(self, linux_output):
        """Test detection of packages in Linux output."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(linux_output)

        assert "OpenSSL" in metadata.found_packages
        assert "ZLIB" in metadata.found_packages
        assert "Boost" in metadata.found_packages

    def test_detect_multiple_packages(self, multiple_packages_output):
        """Test detection of multiple packages."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(multiple_packages_output)

        expected_packages = [
            "PkgConfig",
            "OpenSSL",
            "ZLIB",
            "PNG",
            "JPEG",
            "Threads",
            "Boost",
            "GTest",
        ]

        for package in expected_packages:
            assert package in metadata.found_packages

    def test_package_order_preserved(self, multiple_packages_output):
        """Test that package order is preserved from output."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(multiple_packages_output)

        # Verify packages are in order
        pkg_indices = [
            metadata.found_packages.index("PkgConfig"),
            metadata.found_packages.index("OpenSSL"),
            metadata.found_packages.index("ZLIB"),
            metadata.found_packages.index("PNG"),
        ]

        assert pkg_indices == sorted(pkg_indices)

    def test_no_packages_when_none_found(self, minimal_output):
        """Test that found_packages is empty when no packages found."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(minimal_output)

        assert metadata.found_packages == []

    def test_python_package_detected(self, windows_output):
        """Test detection of Python package."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(windows_output)

        assert "Python3" in metadata.found_packages


class TestBuildTypeDetection:
    """Test build type detection from configure output."""

    def test_detect_release_build_type(self, linux_output):
        """Test detection of Release build type."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(linux_output)

        assert metadata.build_type == "Release"

    def test_detect_debug_build_type(self, windows_output):
        """Test detection of Debug build type."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(windows_output)

        assert metadata.build_type == "Debug"

    def test_detect_relwithdebinfo_build_type(self, macos_output):
        """Test detection of RelWithDebInfo build type."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(macos_output)

        assert metadata.build_type == "RelWithDebInfo"

    def test_build_type_none_when_missing(self):
        """Test that build_type is None when not found in output."""
        inspector = BuildInspector()
        output = "-- Configuring done\n-- Generating done"
        metadata = inspector.inspect_configure_output(output)

        assert metadata.build_type is None


class TestPartialInformation:
    """Test handling of partial or missing information."""

    def test_handle_minimal_output(self, minimal_output):
        """Test handling of minimal configure output."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(minimal_output)

        # Should still return a valid ConfigureMetadata object
        assert isinstance(metadata, ConfigureMetadata)

        # Should have at least compiler info
        assert metadata.compiler_c == "GNU"
        assert metadata.compiler_cxx == "GNU"

    def test_handle_empty_output(self):
        """Test handling of empty output."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output("")

        assert isinstance(metadata, ConfigureMetadata)
        assert metadata.cmake_version is None
        assert metadata.generator is None
        assert metadata.compiler_c is None
        assert metadata.compiler_cxx is None
        assert metadata.system_name is None
        assert metadata.system_processor is None
        assert metadata.found_packages == []
        assert metadata.build_type is None

    def test_handle_partial_compiler_info(self):
        """Test handling when only C compiler is found."""
        inspector = BuildInspector()
        output = "-- The C compiler identification is GNU 11.4.0\n"
        metadata = inspector.inspect_configure_output(output)

        assert metadata.compiler_c == "GNU"
        assert metadata.compiler_cxx is None


class TestCrossPlatformOutput:
    """Test inspection of outputs from different platforms."""

    def test_all_platforms_return_valid_metadata(self, linux_output, windows_output, macos_output):
        """Test that all platform outputs return valid metadata."""
        inspector = BuildInspector()

        linux_meta = inspector.inspect_configure_output(linux_output)
        windows_meta = inspector.inspect_configure_output(windows_output)
        macos_meta = inspector.inspect_configure_output(macos_output)

        assert isinstance(linux_meta, ConfigureMetadata)
        assert isinstance(windows_meta, ConfigureMetadata)
        assert isinstance(macos_meta, ConfigureMetadata)

    def test_platform_specificompiler_cs_detected(self, linux_output, windows_output, macos_output):
        """Test that platform-specific compilers are detected."""
        inspector = BuildInspector()

        linux_meta = inspector.inspect_configure_output(linux_output)
        assert linux_meta.compiler_c == "GNU"

        windows_meta = inspector.inspect_configure_output(windows_output)
        assert windows_meta.compiler_c == "MSVC"

        macos_meta = inspector.inspect_configure_output(macos_output)
        assert macos_meta.compiler_c == "AppleClang"


class TestMetadataIntegrity:
    """Test that metadata objects maintain data integrity."""

    def test_metadata_has_all_fields(self, linux_output):
        """Test that ConfigureMetadata has all expected fields."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(linux_output)

        # Verify all expected attributes exist
        assert hasattr(metadata, "cmake_version")
        assert hasattr(metadata, "generator")
        assert hasattr(metadata, "compiler_c")
        assert hasattr(metadata, "compiler_cxx")
        assert hasattr(metadata, "system_name")
        assert hasattr(metadata, "system_processor")
        assert hasattr(metadata, "found_packages")
        assert hasattr(metadata, "build_type")

    def test_found_packages_is_list(self, linux_output):
        """Test that found_packages is always a list."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(linux_output)

        assert isinstance(metadata.found_packages, list)

    def test_string_fields_are_strings_or_none(self, linux_output):
        """Test that string fields are strings or None."""
        inspector = BuildInspector()
        metadata = inspector.inspect_configure_output(linux_output)

        for field in [
            "cmake_version",
            "generator",
            "compiler_c",
            "compiler_cxx",
            "system_name",
            "system_processor",
            "build_type",
        ]:
            value = getattr(metadata, field)
            assert value is None or isinstance(value, str)
