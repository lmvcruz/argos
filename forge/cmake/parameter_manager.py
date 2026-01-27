"""
CMakeParameterManager class for managing CMake parameters.

Responsible for building CMake command strings from ForgeArguments,
including configure and build commands with proper parameter formatting.
"""

from typing import List

from forge.models.arguments import ForgeArguments


class CMakeParameterManager:
    """
    Manages CMake command generation from ForgeArguments.

    Takes a ForgeArguments object and generates properly formatted
    CMake commands for both configuration and build phases.

    Attributes:
        args: The ForgeArguments containing all build parameters
    """

    def __init__(self, args: ForgeArguments):
        """
        Initialize CMakeParameterManager.

        Args:
            args: ForgeArguments object with build configuration
        """
        self.args = args

    def get_configure_command(self) -> List[str]:
        """
        Generate CMake configure command.

        Builds a command list for CMake configuration phase with all
        necessary parameters from cmake_args.

        Returns:
            List of command arguments suitable for subprocess.run()

        Example:
            ['cmake', '/path/to/source', '-B', '/path/to/build',
             '-G', 'Ninja', '-DCMAKE_BUILD_TYPE=Release']
        """
        command = ["cmake"]

        # Add any CMake arguments (e.g., -G, -D options)
        if self.args.cmake_args:
            command.extend(self.args.cmake_args)

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
