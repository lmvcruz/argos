"""
CMakeParameterManager class for managing CMake parameters.

Responsible for building CMake command strings from ForgeArguments,
including configure and build commands with proper parameter formatting.
"""

import platform
import shutil
from typing import Dict, List, Optional

from forge.models.arguments import ForgeArguments


class CMakeParameterManager:
    """
    Manages CMake command generation from ForgeArguments.

    Takes a ForgeArguments object and generates properly formatted
    CMake commands for both configuration and build phases.

    Attributes:
        args: The ForgeArguments containing all build parameters
        _extra_parameters: Dictionary of programmatically added parameters
    """

    def __init__(self, args: ForgeArguments):
        """
        Initialize CMakeParameterManager.

        Args:
            args: ForgeArguments object with build configuration
        """
        self.args = args
        self._extra_parameters: Dict[str, str] = {}

    def add_parameter(self, name: str, value: str) -> None:
        """
        Add or override a CMake parameter.

        Parameters added with this method take precedence over those
        provided in cmake_args. The -D prefix is added automatically
        if not present in the name.

        Args:
            name: Parameter name (e.g., "CMAKE_BUILD_TYPE" or "MY_OPTION")
            value: Parameter value (e.g., "Release" or "ON")

        Example:
            manager.add_parameter("BUILD_TESTING", "ON")
            manager.add_parameter("CMAKE_BUILD_TYPE", "Release")
        """
        # Remove -D prefix if present in the name
        clean_name = name.lstrip("-D")
        self._extra_parameters[clean_name] = value

    def get_parameters(self) -> Dict[str, str]:
        """
        Get all CMake parameters as a dictionary.

        Returns a dictionary of all -D parameters from both cmake_args
        and programmatically added parameters. Programmatically added
        parameters override those from cmake_args.

        Returns:
            Dictionary mapping parameter names to values

        Example:
            {'CMAKE_BUILD_TYPE': 'Release', 'BUILD_TESTING': 'ON'}
        """
        params: Dict[str, str] = {}

        # Parse parameters from cmake_args
        if self.args.cmake_args:
            for arg in self.args.cmake_args:
                if arg.startswith("-D"):
                    # Remove -D prefix and split on first =
                    param_str = arg[2:]  # Remove -D
                    if "=" in param_str:
                        name, value = param_str.split("=", 1)
                        params[name] = value

        # Apply extra parameters (overriding any from cmake_args)
        params.update(self._extra_parameters)

        return params

    def detect_generator(self) -> str:
        """
        Detect the most appropriate CMake generator for the current platform.

        Tries to find the best available generator in this priority order:
        1. Ninja (cross-platform, fastest)
        2. Unix Makefiles (Linux/macOS fallback)
        3. Visual Studio (Windows fallback)

        Returns:
            Name of the detected CMake generator

        Example:
            'Ninja', 'Unix Makefiles', or 'Visual Studio 17 2022'
        """
        # Check for Ninja first (preferred on all platforms)
        if shutil.which("ninja"):
            return "Ninja"

        # Platform-specific fallbacks
        system = platform.system()

        if system in ("Linux", "Darwin"):
            return "Unix Makefiles"
        elif system == "Windows":
            # Try to detect Visual Studio version
            vs_version = self._detect_vs_version()
            if vs_version:
                return f"Visual Studio {vs_version}"
            # Ultimate fallback for Windows
            return "NMake Makefiles"
        else:
            # Unknown platform - use Unix Makefiles as safe default
            return "Unix Makefiles"

    def _detect_vs_version(self) -> Optional[str]:
        """
        Detect installed Visual Studio version on Windows.

        Returns:
            Version string (e.g., "17 2022" for VS 2022) or None if not found

        Note:
            This is a simple detection. Could be enhanced to check
            vswhere.exe or registry for more accurate detection.
        """
        # Common Visual Studio versions (newest first)
        vs_versions = [
            "17 2022",  # Visual Studio 2022
            "16 2019",  # Visual Studio 2019
            "15 2017",  # Visual Studio 2017
        ]

        # Simple heuristic: assume newest version
        # In production, you'd use vswhere.exe or check registry
        return vs_versions[0]

    def get_generator(self) -> str:
        """
        Get the CMake generator to use.

        Returns the explicitly specified generator from cmake_args if present,
        otherwise calls detect_generator() to auto-detect.

        Returns:
            Name of the CMake generator to use

        Raises:
            ValueError: If generator is explicitly specified but empty

        Example:
            'Ninja', 'Unix Makefiles', 'Visual Studio 17 2022'
        """
        # Check if generator is explicitly specified in cmake_args
        if self.args.cmake_args:
            for i, arg in enumerate(self.args.cmake_args):
                if arg.startswith("-G"):
                    if len(arg) > 2:
                        # -GNinja format
                        generator = arg[2:]
                    elif i + 1 < len(self.args.cmake_args):
                        # -G Ninja format (separate args)
                        generator = self.args.cmake_args[i + 1]
                    else:
                        raise ValueError("Empty generator name after -G flag")

                    if not generator:
                        raise ValueError("Empty generator name")
                    return generator

        # No explicit generator, auto-detect
        return self.detect_generator()

    def is_generator_available(self, generator: str) -> bool:
        """
        Check if a specific generator is available on the current system.

        Args:
            generator: Name of the generator to check (e.g., "Ninja")

        Returns:
            True if generator is available, False otherwise

        Example:
            if manager.is_generator_available("Ninja"):
                print("Ninja is available!")
        """
        generator_lower = generator.lower()

        # Check for Ninja
        if "ninja" in generator_lower:
            return shutil.which("ninja") is not None

        # Unix Makefiles is available on Unix-like systems
        if "unix makefiles" in generator_lower:
            return platform.system() in ("Linux", "Darwin")

        # Visual Studio is Windows-only
        if "visual studio" in generator_lower:
            if platform.system() != "Windows":
                return False
            # On Windows, check if VS is actually installed
            return self._detect_vs_version() is not None

        # NMake Makefiles is Windows-only
        if "nmake" in generator_lower:
            return platform.system() == "Windows"

        # Unknown generator - assume unavailable
        return False

    def validate_generator(self) -> None:
        """
        Validate that the current generator is valid and available.

        Raises:
            ValueError: If generator is invalid or unavailable

        Example:
            try:
                manager.validate_generator()
            except ValueError as e:
                print(f"Generator error: {e}")
        """
        generator = self.get_generator()

        # List of known valid CMake generators
        valid_generators = [
            "Ninja",
            "Ninja Multi-Config",
            "Unix Makefiles",
            "NMake Makefiles",
            "MinGW Makefiles",
            "MSYS Makefiles",
            "Borland Makefiles",
            "Watcom WMake",
            "Visual Studio 17 2022",
            "Visual Studio 16 2019",
            "Visual Studio 15 2017",
            "Visual Studio 14 2015",
            "Visual Studio 12 2013",
            "Visual Studio 11 2012",
            "Visual Studio 10 2010",
            "Visual Studio 9 2008",
            "Xcode",
            "Green Hills MULTI",
        ]

        # Check if generator is in the known list
        if generator not in valid_generators:
            raise ValueError(
                f"Invalid CMake generator: '{generator}'. "
                f"Must be one of: {', '.join(valid_generators[:5])}..."
            )

    def get_configure_command(self) -> List[str]:
        """
        Generate CMake configure command.

        Builds a command list for CMake configuration phase with all
        necessary parameters from cmake_args and programmatically
        added parameters. Automatically adds generator (-G) if not
        explicitly specified.

        Returns:
            List of command arguments suitable for subprocess.run()

        Example:
            ['cmake', '/path/to/source', '-B', '/path/to/build',
             '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release']
        """
        command = ["cmake"]

        # Check if generator is already specified in cmake_args
        has_generator = False
        if self.args.cmake_args:
            for arg in self.args.cmake_args:
                if arg.startswith("-G") or arg == "-G":
                    has_generator = True
                    break

        # Add generator if not explicitly specified
        if not has_generator:
            generator = self.detect_generator()
            command.extend(["-G", generator])

        # Add non-parameter args (like -G if explicitly specified) from cmake_args
        if self.args.cmake_args:
            for arg in self.args.cmake_args:
                if not arg.startswith("-D"):
                    command.append(arg)

        # Then add all parameters (from cmake_args + extra_parameters)
        params = self.get_parameters()
        for name, value in params.items():
            command.append(f"-D{name}={value}")

        # Add source directory
        if self.args.source_dir:
            command.append(str(self.args.source_dir.resolve()))

        # Add build directory with -B flag
        command.extend(["-B", str(self.args.build_dir.resolve())])

        return command

    def get_build_command(self) -> List[str]:
        """
        Generate CMake build command.

        Builds a command list for CMake build phase with all
        necessary parameters from build_args.

        Returns:
            List of command arguments suitable for subprocess.run()

        Example:
            ['cmake', '--build', '/path/to/build', '-j8',
             '--target', 'my_target']
        """
        command = ["cmake", "--build"]

        # Add build directory
        command.append(str(self.args.build_dir.resolve()))

        # Add any build arguments (e.g., -j, --target)
        if self.args.build_args:
            command.extend(self.args.build_args)

        return command
