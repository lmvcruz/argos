"""
Main entry point for Forge application.

Orchestrates the complete workflow: argument parsing, CMake execution,
output inspection, and data persistence.
"""

import logging
import sys
from pathlib import Path
from typing import List, Optional

from forge.cli.argument_errors import ArgumentError
from forge.cli.argument_parser import ArgumentParser
from forge.cli.argument_validator import ArgumentValidator, ValidationError
from forge.cmake.executor import CMakeExecutor
from forge.cmake.parameter_manager import CMakeParameterManager
from forge.inspector.build_inspector import BuildInspector
from forge.storage.data_persistence import DataPersistence


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for forge application.

    Orchestrates the complete workflow from argument parsing through
    CMake execution to data persistence.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:] if None)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    # Use sys.argv if no arguments provided
    if argv is None:
        argv = sys.argv[1:]

    try:
        # Step 1: Parse and validate arguments
        parser = ArgumentParser()
        try:
            args = parser.parse(argv)
        except SystemExit as e:
            # ArgumentParser raises SystemExit on error or --help
            return e.code if e.code is not None else 1

        validator = ArgumentValidator()
        try:
            validator.validate_arguments(args)
        except (ArgumentError, ValidationError) as e:
            print(f"Error: {e}", file=sys.stderr)
            return 2

        # Step 2: Configure logging
        log_level = logging.DEBUG if args.verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(levelname)s: %(message)s",
        )
        logger = logging.getLogger(__name__)

        # Step 3: Initialize components
        logger.debug("Initializing components...")

        # Initialize parameter manager
        param_manager = CMakeParameterManager(args)

        # Initialize executor
        executor = CMakeExecutor(param_manager)

        # Check CMake availability
        if not executor.check_cmake_available():
            print("Error: CMake not found. Please install CMake and ensure it's in your PATH.", file=sys.stderr)
            return 127  # Command not found

        # Initialize build inspector
        inspector = BuildInspector()

        # Initialize data persistence
        db_path = args.database_path if args.database_path else None
        persistence = DataPersistence(db_path)

        # Step 4: Execute configure phase (if needed)
        configure_result = None
        configure_metadata = None
        configuration_id = None

        if args.configure:
            logger.info("Configuring build...")
            if args.verbose:
                print(f"Source directory: {args.source_dir}")
                print(f"Build directory: {args.build_dir}")
                print(f"CMake command: {' '.join(param_manager.get_configure_command())}")

            configure_result = executor.execute_configure()

            if not configure_result.success:
                print(f"Configuration failed with exit code {configure_result.exit_code}", file=sys.stderr)
                if configure_result.stderr:
                    print(configure_result.stderr, file=sys.stderr)
                return configure_result.exit_code

            logger.info(f"Configuration completed in {configure_result.duration:.2f}s")

            # Inspect configure output
            configure_metadata = inspector.inspect_configure_output(
                configure_result.stdout
            )

            # Save configuration to database
            try:
                configuration_id = persistence.save_configuration(
                    configure_result, configure_metadata
                )
                logger.debug(f"Saved configuration with ID: {configuration_id}")
            except Exception as e:
                logger.warning(f"Failed to save configuration to database: {e}")

        # Step 5: Execute build phase
        logger.info("Building...")
        if args.verbose and args.configure:
            print(f"Build command: {' '.join(param_manager.get_build_command())}")

        build_result = executor.execute_build()

        if not build_result.success:
            print(f"Build failed with exit code {build_result.exit_code}", file=sys.stderr)
            if build_result.stderr:
                print(build_result.stderr, file=sys.stderr)

        logger.info(f"Build completed in {build_result.duration:.2f}s")

        # Step 6: Inspect build output
        build_metadata = inspector.inspect_build_output(
            build_result.stdout, args.source_dir
        )

        # Step 7: Save build data to database
        try:
            build_id = persistence.save_build(
                build_result, build_metadata, configuration_id
            )
            logger.debug(f"Saved build with ID: {build_id}")

            # Save warnings and errors
            if build_metadata.warnings:
                warning_count = persistence.save_warnings(build_metadata.warnings, build_id)
                logger.debug(f"Saved {warning_count} warnings")

            if build_metadata.errors:
                error_count = persistence.save_errors(build_metadata.errors, build_id)
                logger.debug(f"Saved {error_count} errors")

        except Exception as e:
            logger.warning(f"Failed to save build data to database: {e}")

        # Step 8: Print summary
        print("\n" + "=" * 70)
        print("BUILD SUMMARY")
        print("=" * 70)

        if configure_result:
            status = "SUCCESS" if configure_result.success else "FAILED"
            print(f"Configuration: {status} ({configure_result.duration:.2f}s)")

        status = "SUCCESS" if build_result.success else "FAILED"
        print(f"Build:         {status} ({build_result.duration:.2f}s)")

        if build_metadata.warnings:
            print(f"Warnings:      {len(build_metadata.warnings)}")
        if build_metadata.errors:
            print(f"Errors:        {len(build_metadata.errors)}")

        if build_metadata.targets:
            print(f"Targets built: {len(build_metadata.targets)}")

        print("=" * 70)

        # Return appropriate exit code
        return build_result.exit_code

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130  # Standard exit code for Ctrl+C

    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        logging.exception("Unexpected error occurred")
        return 1


if __name__ == "__main__":
    sys.exit(main())
