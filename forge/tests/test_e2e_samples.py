"""
End-to-end tests for Forge with real CMake sample projects.

Tests Forge against various sample CMake projects to validate
complete workflow from configuration through build to data persistence.
"""

from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile

import pytest

from forge.__main__ import main
from forge.storage.data_persistence import DataPersistence


def has_cxx_compiler():
    """Check if a C++ compiler is available."""
    # Try to find a compiler
    compilers = ["cl.exe", "g++", "clang++"]
    for compiler in compilers:
        try:
            subprocess.run(
                [compiler, "--version"],
                capture_output=True,
                timeout=5,
                check=False,
            )
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return False


# Mark all E2E tests to skip if no C++ compiler is available
pytestmark = pytest.mark.skipif(
    not has_cxx_compiler(),
    reason="C++ compiler not available (MSVC, GCC, or Clang required)",
)


@pytest.fixture
def temp_build_dir():
    """
    Create a temporary directory for build outputs.

    Yields:
        Path to temporary build directory, cleaned up after test
    """
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def temp_db():
    """
    Create a temporary database for testing.

    Yields:
        Path to temporary database file, cleaned up after test
    """
    temp_db_file = Path(tempfile.mktemp(suffix=".db"))
    yield temp_db_file
    # Give Windows time to release file locks
    import time

    time.sleep(0.1)
    if temp_db_file.exists():
        try:
            temp_db_file.unlink()
        except PermissionError:
            # If still locked, leave it for OS cleanup
            pass


@pytest.fixture
def fixtures_dir():
    """Get the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures" / "projects"


class TestSimpleExecutable:
    """Test Forge with a simple C++ executable project."""

    def test_configure_and_build_simple_executable(self, fixtures_dir, temp_build_dir, temp_db):
        """
        Test complete workflow with simple executable project.

        Verifies that Forge can configure, build, and persist data
        for a basic C++ executable.
        """
        project_dir = fixtures_dir / "simple_executable"
        assert project_dir.exists(), f"Project directory not found: {project_dir}"

        # Run Forge
        args = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(temp_build_dir),
            "--database",
            str(temp_db),
        ]

        # Execute main (this should configure and build)
        exit_code = main(args)

        # Verify success
        assert exit_code == 0, "Forge should complete successfully"

        # Verify build directory was created
        assert temp_build_dir.exists(), "Build directory should exist"

        # Verify database was created and contains data
        assert temp_db.exists(), "Database should be created"

        # Check database contents
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Verify configuration record
        cursor.execute("SELECT COUNT(*) FROM configurations")
        config_count = cursor.fetchone()[0]
        assert config_count == 1, "Should have one configuration record"

        # Verify build record
        cursor.execute("SELECT COUNT(*) FROM builds")
        build_count = cursor.fetchone()[0]
        assert build_count == 1, "Should have one build record"

        # Verify project name
        cursor.execute("SELECT project_name FROM configurations")
        project_name = cursor.fetchone()[0]
        assert (
            project_name == "SimpleExecutable"
        ), f"Project name should be SimpleExecutable, got {project_name}"

        conn.close()

    def test_build_only_simple_executable(self, fixtures_dir, temp_build_dir, temp_db):
        """
        Test build-only workflow (no configure).

        Verifies that Forge can build a pre-configured project.
        """
        project_dir = fixtures_dir / "simple_executable"

        # First, configure the project manually
        args_configure = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(temp_build_dir),
            "--database",
            str(temp_db),
        ]
        exit_code = main(args_configure)
        assert exit_code == 0, "Initial configuration should succeed"

        # Now test build-only mode
        args_build = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(temp_build_dir),
            "--database",
            str(temp_db),
            "--no-configure",
        ]

        exit_code = main(args_build)
        assert exit_code == 0, "Build-only should succeed"

        # Verify database has two build records (one from configure+build, one from build-only)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM builds")
        build_count = cursor.fetchone()[0]
        assert build_count == 2, f"Should have two build records, got {build_count}"

        conn.close()


class TestMultipleTargets:
    """Test Forge with projects containing multiple build targets."""

    def test_multiple_targets_project(self, fixtures_dir, temp_build_dir, temp_db):
        """
        Test project with multiple executables and a library.

        Verifies that Forge correctly handles projects with
        multiple targets (library + executables).
        """
        project_dir = fixtures_dir / "multiple_targets"
        assert project_dir.exists(), f"Project directory not found: {project_dir}"

        args = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(temp_build_dir),
            "--database",
            str(temp_db),
        ]

        exit_code = main(args)
        assert exit_code == 0, "Forge should complete successfully"

        # Check database for project name
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT project_name FROM configurations")
        project_name = cursor.fetchone()[0]
        assert (
            project_name == "MultipleTargets"
        ), f"Project name should be MultipleTargets, got {project_name}"

        # Check that build completed successfully
        cursor.execute("SELECT success FROM builds")
        success = cursor.fetchone()[0]
        assert success == 1, "Build should be successful"

        conn.close()


class TestHeaderOnlyLibrary:
    """Test Forge with header-only library projects."""

    def test_header_only_library(self, fixtures_dir, temp_build_dir, temp_db):
        """
        Test project with header-only library.

        Verifies that Forge handles header-only libraries correctly.
        """
        project_dir = fixtures_dir / "header_only"
        assert project_dir.exists(), f"Project directory not found: {project_dir}"

        args = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(temp_build_dir),
            "--database",
            str(temp_db),
        ]

        exit_code = main(args)
        assert exit_code == 0, "Forge should complete successfully"

        # Verify project name
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT project_name FROM configurations")
        project_name = cursor.fetchone()[0]
        assert (
            project_name == "HeaderOnlyLib"
        ), f"Project name should be HeaderOnlyLib, got {project_name}"

        conn.close()


class TestSubdirectories:
    """Test Forge with projects using subdirectories."""

    def test_project_with_subdirectories(self, fixtures_dir, temp_build_dir, temp_db):
        """
        Test project with CMake subdirectories.

        Verifies that Forge handles projects with add_subdirectory
        correctly.
        """
        project_dir = fixtures_dir / "with_subdirectories"
        assert project_dir.exists(), f"Project directory not found: {project_dir}"

        args = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(temp_build_dir),
            "--database",
            str(temp_db),
        ]

        exit_code = main(args)
        assert exit_code == 0, "Forge should complete successfully"

        # Verify project name and success
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT project_name FROM configurations")
        result = cursor.fetchone()
        project_name = result[0]

        assert (
            project_name == "WithSubdirectories"
        ), f"Project name should be WithSubdirectories, got {project_name}"

        conn.close()


class TestBuildTypes:
    """Test Forge with different build types (Debug/Release)."""

    @pytest.mark.skipif(sys.platform == "win32", reason="Visual Studio is a multi-config generator")
    def test_debug_build(self, fixtures_dir, temp_build_dir, temp_db):
        """
        Test Debug build configuration.

        Verifies that Forge correctly handles Debug build type.
        Note: Skipped on Windows as Visual Studio generator is multi-config
        and doesn't use CMAKE_BUILD_TYPE.
        """
        project_dir = fixtures_dir / "debug_release"
        assert project_dir.exists(), f"Project directory not found: {project_dir}"

        args = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(temp_build_dir),
            "--database",
            str(temp_db),
            "--cmake-args",
            "-DCMAKE_BUILD_TYPE=Debug",
        ]

        exit_code = main(args)
        assert exit_code == 0, "Forge should complete successfully"

        # Verify build type in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT build_type FROM configurations")
        build_type = cursor.fetchone()[0]
        assert build_type == "Debug", f"Build type should be Debug, got {build_type}"

        conn.close()

    @pytest.mark.skipif(sys.platform == "win32", reason="Visual Studio is a multi-config generator")
    def test_release_build(self, fixtures_dir, temp_build_dir, temp_db):
        """
        Test Release build configuration.

        Verifies that Forge correctly handles Release build type.
        Note: Skipped on Windows as Visual Studio generator is multi-config
        and doesn't use CMAKE_BUILD_TYPE.
        """
        project_dir = fixtures_dir / "debug_release"
        release_build_dir = temp_build_dir / "release"
        release_build_dir.mkdir(parents=True, exist_ok=True)

        args = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(release_build_dir),
            "--database",
            str(temp_db),
            "--cmake-args",
            "-DCMAKE_BUILD_TYPE=Release",
        ]

        exit_code = main(args)
        assert exit_code == 0, "Forge should complete successfully"

        # Verify build type in database
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        # Get the most recent configuration (should be Release)
        cursor.execute("SELECT build_type FROM configurations ORDER BY timestamp DESC LIMIT 1")
        build_type = cursor.fetchone()[0]
        assert build_type == "Release", f"Build type should be Release, got {build_type}"

        conn.close()


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_complete_workflow_with_metadata(self, fixtures_dir, temp_build_dir, temp_db):
        """
        Test complete workflow including metadata extraction.

        Verifies that Forge extracts and stores all expected metadata
        from a successful build.
        """
        project_dir = fixtures_dir / "simple_executable"

        args = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(temp_build_dir),
            "--database",
            str(temp_db),
            "--verbose",
        ]

        exit_code = main(args)
        assert exit_code == 0, "Forge should complete successfully"

        # Verify comprehensive metadata
        persistence = DataPersistence(temp_db)

        # Get recent builds
        recent_builds = persistence.get_recent_builds(limit=1)
        assert len(recent_builds) == 1, "Should have one build record"

        build = recent_builds[0]
        assert build["project_name"] == "SimpleExecutable"
        assert build["success"] == 1
        assert build["duration"] is not None
        assert build["duration"] > 0

    def test_verbose_output(self, fixtures_dir, temp_build_dir, temp_db, capsys):
        """
        Test verbose output mode.

        Verifies that --verbose flag produces additional output.
        """
        project_dir = fixtures_dir / "simple_executable"

        args = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(temp_build_dir),
            "--database",
            str(temp_db),
            "--verbose",
        ]

        exit_code = main(args)
        assert exit_code == 0, "Forge should complete successfully"

        # Check that verbose output was produced
        captured = capsys.readouterr()
        output = captured.out + captured.err

        # Verbose output should contain DEBUG level messages
        # (This is a basic check - actual content depends on logging implementation)
        assert len(output) > 0, "Should produce some output"


class TestDataPersistence:
    """Test data persistence across multiple builds."""

    def test_multiple_builds_same_project(self, fixtures_dir, temp_build_dir, temp_db):
        """
        Test running multiple builds of the same project.

        Verifies that multiple builds are stored correctly
        with separate records.
        """
        project_dir = fixtures_dir / "simple_executable"

        # Create subdirectories for builds
        build1_dir = temp_build_dir / "build1"
        build1_dir.mkdir(parents=True, exist_ok=True)
        build2_dir = temp_build_dir / "build2"
        build2_dir.mkdir(parents=True, exist_ok=True)

        # Run first build
        args1 = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(build1_dir),
            "--database",
            str(temp_db),
        ]
        exit_code1 = main(args1)
        assert exit_code1 == 0

        # Run second build
        args2 = [
            "--source-dir",
            str(project_dir),
            "--build-dir",
            str(build2_dir),
            "--database",
            str(temp_db),
        ]
        exit_code2 = main(args2)
        assert exit_code2 == 0

        # Verify database has records for both builds
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM configurations")
        config_count = cursor.fetchone()[0]
        assert config_count == 2, f"Should have 2 configurations, got {config_count}"

        cursor.execute("SELECT COUNT(*) FROM builds")
        build_count = cursor.fetchone()[0]
        assert build_count == 2, f"Should have 2 builds, got {build_count}"

        conn.close()

    def test_multiple_different_projects(self, fixtures_dir, temp_build_dir, temp_db):
        """
        Test building multiple different projects into same database.

        Verifies that different projects are tracked separately
        in the same database.
        """
        # Create subdirectories for builds
        project1_build = temp_build_dir / "project1"
        project1_build.mkdir(parents=True, exist_ok=True)
        project2_build = temp_build_dir / "project2"
        project2_build.mkdir(parents=True, exist_ok=True)

        # Build first project
        project1 = fixtures_dir / "simple_executable"
        args1 = [
            "--source-dir",
            str(project1),
            "--build-dir",
            str(project1_build),
            "--database",
            str(temp_db),
        ]
        exit_code1 = main(args1)
        assert exit_code1 == 0

        # Build second project
        project2 = fixtures_dir / "multiple_targets"
        args2 = [
            "--source-dir",
            str(project2),
            "--build-dir",
            str(project2_build),
            "--database",
            str(temp_db),
        ]
        exit_code2 = main(args2)
        assert exit_code2 == 0

        # Verify database has both projects
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        cursor.execute("SELECT DISTINCT project_name FROM configurations")
        project_names = [row[0] for row in cursor.fetchall()]

        assert len(project_names) == 2, f"Should have 2 projects, got {len(project_names)}"
        assert "SimpleExecutable" in project_names
        assert "MultipleTargets" in project_names

        conn.close()
