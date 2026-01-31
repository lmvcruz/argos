"""
Pytest configuration for performance tests.

Provides fixtures for creating large test directories and projects.
"""

import pytest


@pytest.fixture
def large_directory_tree(tmp_path):
    """
    Create a large directory tree with many files for performance testing.

    Creates a directory tree with:
    - 10,000 Python files
    - 1,000 C++ files
    - Various subdirectories
    - Realistic project structure

    Returns:
        Path to the root directory
    """
    root = tmp_path / "large_project"
    root.mkdir()

    # Create Python files in multiple subdirectories
    for i in range(50):
        subdir = root / f"module_{i}"
        subdir.mkdir()
        for j in range(200):
            file_path = subdir / f"file_{j}.py"
            file_path.write_text(
                f"# File {j} in module {i}\n" f"def function_{j}():\n" f"    pass\n"
            )

    # Create C++ files
    cpp_dir = root / "src"
    cpp_dir.mkdir()
    for i in range(10):
        subdir = cpp_dir / f"component_{i}"
        subdir.mkdir()
        for j in range(100):
            # Create .cpp files
            cpp_file = subdir / f"file_{j}.cpp"
            cpp_file.write_text(f"// File {j} in component {i}\n" f"void function_{j}() {{}}\n")
            # Create .h files
            h_file = subdir / f"file_{j}.h"
            h_file.write_text(
                f"// Header {j} in component {i}\n" f"#pragma once\n" f"void function_{j}();\n"
            )

    # Create some ignored directories
    ignored = root / "build"
    ignored.mkdir()
    for i in range(100):
        (ignored / f"file_{i}.o").write_text("binary content")

    return root


@pytest.fixture
def medium_directory_tree(tmp_path):
    """
    Create a medium-sized directory tree (1000 files) for faster benchmarks.

    Returns:
        Path to the root directory
    """
    root = tmp_path / "medium_project"
    root.mkdir()

    # Create 800 Python files
    for i in range(10):
        subdir = root / f"module_{i}"
        subdir.mkdir()
        for j in range(80):
            file_path = subdir / f"file_{j}.py"
            file_path.write_text(f"# File {j}\ndef function_{j}():\n    pass\n")

    # Create 200 C++ files
    cpp_dir = root / "src"
    cpp_dir.mkdir()
    for i in range(100):
        (cpp_dir / f"file_{i}.cpp").write_text(f"void f{i}() {{}}")
        (cpp_dir / f"file_{i}.h").write_text(f"void f{i}();")

    return root


@pytest.fixture
def git_repository(tmp_path):
    """
    Create a git repository with history for incremental mode testing.

    Returns:
        Path to the git repository root
    """
    import subprocess

    repo_root = tmp_path / "git_repo"
    repo_root.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    for i in range(20):
        (repo_root / f"file_{i}.py").write_text(f"# File {i}\n")

    subprocess.run(["git", "add", "."], cwd=repo_root, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    # Create uncommitted changes
    for i in range(5):
        (repo_root / f"file_{i}.py").write_text(f"# Modified file {i}\n")

    return repo_root


@pytest.fixture
def populated_statistics_db(tmp_path):
    """
    Create a statistics database with historical data.

    Creates:
    - 100 validation runs
    - 1000+ test case records
    - Multiple validators per run

    Returns:
        Path to the database file
    """
    from datetime import datetime, timedelta

    from anvil.storage.statistics_database import (
        StatisticsDatabase,
        TestCaseRecord,
        ValidationRun,
        ValidatorRunRecord,
    )

    db_path = tmp_path / "stats.db"
    db = StatisticsDatabase(db_path)

    base_time = datetime.now() - timedelta(days=100)

    # Create 100 runs over the past 100 days
    for i in range(100):
        run_time = base_time + timedelta(days=i)

        # Create ValidationRun dataclass
        run = ValidationRun(
            timestamp=run_time,
            git_commit=f"commit_{i:03d}",
            git_branch="main",
            incremental=i % 2 == 0,
            passed=i % 10 != 0,  # 90% success rate
            duration_seconds=300.0,  # 5 minutes
        )
        run_id = db.insert_validation_run(run)

        # Add validator results
        for validator in ["flake8", "black", "pylint", "pytest"]:
            validator_record = ValidatorRunRecord(
                run_id=run_id,
                validator_name=validator,
                passed=i % 10 != 0,
                error_count=0 if i % 10 != 0 else 5,
                warning_count=i % 3,
                files_checked=100 + i,
                duration_seconds=1.5 + (i % 10) * 0.1,
            )
            db.insert_validator_run_record(validator_record)

        # Add test case results (10 tests per run)
        for test_num in range(10):
            test_name = f"test_function_{test_num}"
            # Make test 5 flaky (60% success rate)
            passed = test_num != 5 or (i % 5 < 3)

            test_record = TestCaseRecord(
                run_id=run_id,
                test_name=test_name,
                test_suite=f"tests.test_{test_num}",
                passed=passed,
                skipped=False,
                duration_seconds=0.01 + (test_num * 0.005),
                failure_message="" if passed else "Assertion failed",
            )
            db.insert_test_case_record(test_record)

    return db_path


@pytest.fixture
def benchmark_timer():
    """
    Provide a simple timer utility for benchmarking.

    Returns:
        Timer context manager
    """
    import time
    from contextlib import contextmanager

    @contextmanager
    def timer(label="Operation"):
        start = time.perf_counter()
        yield lambda: time.perf_counter() - start
        elapsed = time.perf_counter() - start
        print(f"\n{label}: {elapsed:.4f}s")

    return timer
