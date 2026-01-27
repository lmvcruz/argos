"""
CMakeParameterManager class for managing CMake parameters.

Responsible for building CMake command strings from ForgeArguments,
including configure and build commands with proper parameter formatting.
"""

from typing import Dict, List

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

    def get_configure_command(self) -> List[str]:
        """
        Generate CMake configure command.

        Builds a command list for CMake configuration phase with all
        necessary parameters from cmake_args and programmatically
        added parameters.

        Returns:
            List of command arguments suitable for subprocess.run()

        Example:
            ['cmake', '/path/to/source', '-B', '/path/to/build',
             '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release']
        """
        command = ["cmake"]

        # First, add non-parameter args (like -G) from cmake_args
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
