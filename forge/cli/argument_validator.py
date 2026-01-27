"""
Argument validation for Forge CLI.

Validates command-line arguments for logical consistency, path validity,
and mutually exclusive options before execution.
"""

from pathlib import Path

from forge.models.arguments import ForgeArguments


class ValidationError(Exception):
    """
    Exception raised when argument validation fails.

    This exception is raised when command-line arguments are invalid,
    inconsistent, or point to non-existent resources.
    """

    pass


class ArgumentValidator:
    """
    Validates command-line arguments for logical consistency.

    Checks that:
    - Required directories exist or can be created
    - Source directories contain CMakeLists.txt
    - Build directories have necessary configuration for build-only mode
    - Database paths are valid
    - Mutually exclusive options are not used together
    """

    def validate_arguments(self, args: ForgeArguments) -> None:
        """
        Validate command-line arguments for consistency and correctness.

        Args:
            args: Parsed command-line arguments to validate

        Raises:
            ValidationError: If arguments are invalid or inconsistent

        Validation Rules:
        1. If source_dir is provided, it must exist and contain CMakeLists.txt
        2. If source_dir is not provided, build_dir must exist with CMakeCache.txt
        3. Database path (if provided) must not be a directory
        4. --no-configure requires existing build with CMakeCache.txt
        5. --clean-build and --no-configure are mutually exclusive
        """
        # Check mutually exclusive options first
        self._validate_mutually_exclusive_options(args)

        # Validate source directory if provided
        if args.source_dir is not None:
            self._validate_source_directory(args.source_dir)

        # Validate build directory
        self._validate_build_directory(args)

        # Validate database path if provided
        if args.database_path is not None:
            self._validate_database_path(args.database_path)

    def _validate_mutually_exclusive_options(self, args: ForgeArguments) -> None:
        """
        Validate that mutually exclusive options are not used together.

        Args:
            args: Parsed arguments to validate

        Raises:
            ValidationError: If mutually exclusive options are used together
        """
        # --clean-build and --no-configure are mutually exclusive
        if args.clean_build and not args.configure:
            raise ValidationError(
                "Options --clean-build and --no-configure are mutually exclusive. "
                "--clean-build requires running the configure step to set up a clean build directory."
            )

    def _validate_source_directory(self, source_dir: Path) -> None:
        """
        Validate source directory exists and contains CMakeLists.txt.

        Args:
            source_dir: Path to source directory

        Raises:
            ValidationError: If source directory is invalid
        """
        # Check if path exists
        if not source_dir.exists():
            raise ValidationError(
                f"Source directory does not exist: {source_dir}\n"
                f"Please provide a valid source directory path."
            )

        # Check if it's actually a directory
        if not source_dir.is_dir():
            raise ValidationError(
                f"Source path is not a directory: {source_dir}\n"
                f"Please provide a path to a directory containing CMakeLists.txt."
            )

        # Check for CMakeLists.txt
        cmakelists = source_dir / "CMakeLists.txt"
        if not cmakelists.exists():
            raise ValidationError(
                f"Source directory does not contain CMakeLists.txt: {source_dir}\n"
                f"Please provide a directory with a valid CMake project."
            )

    def _validate_build_directory(self, args: ForgeArguments) -> None:
        """
        Validate build directory based on configuration mode.

        Args:
            args: Parsed arguments to validate

        Raises:
            ValidationError: If build directory configuration is invalid
        """
        build_dir = args.build_dir

        # If --no-configure is set, build directory must exist with CMakeCache.txt
        if not args.configure:
            if not build_dir.exists():
                raise ValidationError(
                    f"Build directory does not exist: {build_dir}\n"
                    f"When using --no-configure, the build directory must already exist "
                    f"with a previous CMake configuration."
                )

            cmake_cache = build_dir / "CMakeCache.txt"
            if not cmake_cache.exists():
                raise ValidationError(
                    f"Build directory does not contain CMakeCache.txt: {build_dir}\n"
                    f"When using --no-configure, the build directory must have been "
                    f"previously configured with CMake."
                )

        # If source_dir is not provided, build_dir must exist with CMakeCache.txt
        elif args.source_dir is None:
            if not build_dir.exists():
                raise ValidationError(
                    f"Build directory does not exist: {build_dir}\n"
                    f"When --source-dir is not provided, the build directory must already exist.\n"
                    f"Either:\n"
                    f"  1. Provide --source-dir to create a new build\n"
                    f"  2. Use an existing build directory with CMakeCache.txt"
                )

            cmake_cache = build_dir / "CMakeCache.txt"
            if not cmake_cache.exists():
                raise ValidationError(
                    f"Build directory exists but does not contain CMakeCache.txt: {build_dir}\n"
                    f"When --source-dir is not provided, the build directory must have been "
                    f"previously configured.\n"
                    f"Either:\n"
                    f"  1. Provide --source-dir to configure this build directory\n"
                    f"  2. Use a build directory that was previously configured"
                )

        # If source_dir is provided, build_dir will be created if it doesn't exist
        # (this is valid - configure will create it)

    def _validate_database_path(self, database_path: Path) -> None:
        """
        Validate database path is appropriate for a database file.

        Args:
            database_path: Path to database file

        Raises:
            ValidationError: If database path is invalid
        """
        # Check if path points to an existing directory
        if database_path.exists() and database_path.is_dir():
            raise ValidationError(
                f"Database path is a directory: {database_path}\n"
                f"Please provide a path to a database file, not a directory."
            )

        # Check if parent directory exists
        parent_dir = database_path.parent
        if not parent_dir.exists():
            raise ValidationError(
                f"Database parent directory does not exist: {parent_dir}\n"
                f"Please ensure the parent directory exists before specifying a database path."
            )
