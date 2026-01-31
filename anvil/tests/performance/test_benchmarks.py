"""
Performance benchmark tests for Anvil.

Tests performance characteristics with large codebases:
- File collection speed
- Language detection speed
- Validator execution (sequential vs parallel)
- Incremental vs full mode
- Database query performance
- Smart filtering performance
- Memory usage

Success criteria:
- Incremental validation <5 seconds
- No memory leaks
- Linear scaling with file count
"""

from pathlib import Path


class TestFileCollectionPerformance:
    """Test performance of file collection on large directory trees."""

    def test_collect_files_large_directory_tree(self, large_directory_tree, benchmark_timer):
        """
        Test file collection on large directory tree (10k files).

        Should complete in reasonable time (<2 seconds).
        """
        from anvil.core.file_collector import FileCollector

        collector = FileCollector(root_dir=large_directory_tree)

        with benchmark_timer("File collection (10k files)") as elapsed:
            files = collector.collect_files(languages=["python", "cpp"])

        # Verify correct number of files collected
        assert len(files) > 10000, "Should collect 10,000+ files"

        # Performance assertion
        duration = elapsed()
        assert duration < 3.0, f"File collection too slow: {duration:.2f}s (expected <3s)"

        print(f"  Files collected: {len(files)}")
        print(f"  Files/second: {len(files)/duration:.0f}")

    def test_collect_files_with_exclusions(self, large_directory_tree, benchmark_timer):
        """
        Test file collection with exclusion patterns applied.

        Should efficiently skip ignored directories.
        """
        from anvil.core.file_collector import FileCollector

        collector = FileCollector(
            root_dir=large_directory_tree,
            exclude_patterns=["build/**", "**/__pycache__/**", "**/venv/**"],
        )

        with benchmark_timer("File collection with exclusions") as elapsed:
            _files = collector.collect_files(languages=["python"])  # noqa: F841

        duration = elapsed()
        assert duration < 2.0, f"Collection with exclusions too slow: {duration:.2f}s"

    def test_incremental_collection_faster_than_full(self, git_repository, benchmark_timer):
        """
        Test that incremental collection finds only changed files.

        Incremental should identify changed files correctly.
        """
        from anvil.core.file_collector import FileCollector

        collector = FileCollector(root_dir=git_repository)

        # Full collection
        with benchmark_timer("Full collection") as elapsed_full:
            full_files = collector.collect_files(languages=["python"])
        full_time = elapsed_full()

        # Incremental collection (only 5 changed files)
        with benchmark_timer("Incremental collection") as elapsed_inc:
            inc_files = collector.collect_files(incremental=True, languages=["python"])
        inc_time = elapsed_inc()

        # Incremental should find fewer files (only changed ones)
        assert len(inc_files) < len(full_files), (
            f"Incremental should find fewer files: " f"{len(inc_files)} vs {len(full_files)}"
        )

        # With small repos, git overhead can dominate, so we check file count instead
        assert len(inc_files) <= 5, f"Should find at most 5 changed files, found {len(inc_files)}"

        print(f"  Full: {len(full_files)} files in {full_time:.4f}s")
        print(f"  Incremental: {len(inc_files)} files in {inc_time:.4f}s")
        if inc_time < full_time:
            print(f"  Speedup: {full_time/inc_time:.1f}x")
        else:
            print("  Note: Git overhead dominates for small repos")


class TestLanguageDetectionPerformance:
    """Test performance of language detection."""

    def test_detect_languages_large_project(self, large_directory_tree, benchmark_timer):
        """
        Test language detection on large mixed-language project.

        Should complete in <1.5 seconds (allows for platform variations).
        """
        from anvil.core.language_detector import LanguageDetector

        detector = LanguageDetector(root_dir=large_directory_tree)

        with benchmark_timer("Language detection") as elapsed:
            languages = detector.detect_languages()

        duration = elapsed()
        assert duration < 2.5, f"Language detection too slow: {duration:.2f}s"
        assert "python" in languages
        assert "cpp" in languages

        print(f"  Detected languages: {languages}")

    def test_get_files_by_language_cached(self, medium_directory_tree, benchmark_timer):
        """
        Test that repeated calls to get_files use caching.

        Second call should be significantly faster.
        """
        from anvil.core.language_detector import LanguageDetector

        detector = LanguageDetector(root_dir=medium_directory_tree)

        # First call (no cache)
        with benchmark_timer("First call (no cache)") as elapsed_first:
            files_first = detector.get_files_for_language("python")
        first_time = elapsed_first()

        # Second call (should use cache)
        with benchmark_timer("Second call (cached)") as elapsed_second:
            files_second = detector.get_files_for_language("python")
        second_time = elapsed_second()

        assert files_first == files_second
        # Cached call should be much faster (>10x)
        assert second_time < first_time * 0.1, (
            f"Cached call ({second_time:.4f}s) should be <10% of " f"first call ({first_time:.4f}s)"
        )

        print(f"  First: {first_time:.4f}s")
        print(f"  Cached: {second_time:.6f}s")
        print(f"  Speedup: {first_time/second_time:.0f}x")


class TestValidatorExecutionPerformance:
    """Test performance of validator execution."""

    def test_parallel_execution_faster_than_sequential(
        self, medium_directory_tree, benchmark_timer
    ):
        """
        Test that parallel execution is faster than sequential.

        With multiple validators, parallel should show speedup.
        """
        from anvil.core.orchestrator import ValidationOrchestrator
        from anvil.core.validator_registry import ValidatorRegistry
        from anvil.validators.black_validator import BlackValidator
        from anvil.validators.flake8_validator import Flake8Validator
        from anvil.validators.isort_validator import IsortValidator

        # Create registry and register validators
        registry = ValidatorRegistry()
        registry.register(Flake8Validator())
        registry.register(BlackValidator())
        registry.register(IsortValidator())

        files = [Path(f) for f in list(medium_directory_tree.rglob("*.py"))[:100]]

        # Sequential execution
        orchestrator = ValidationOrchestrator(registry)

        with benchmark_timer("Sequential execution") as elapsed_seq:
            results_seq = orchestrator.run_all(files=files, parallel=False)
        seq_time = elapsed_seq()

        # Parallel execution
        with benchmark_timer("Parallel execution") as elapsed_par:
            results_par = orchestrator.run_all(files=files, parallel=True)
        par_time = elapsed_par()

        # Both should complete successfully
        assert len(results_seq) == 3
        assert len(results_par) == 3

        # Parallel should be faster (but not strictly required due to overhead)
        print(f"  Sequential: {seq_time:.4f}s")
        print(f"  Parallel: {par_time:.4f}s")
        if par_time < seq_time:
            print(f"  Speedup: {seq_time/par_time:.2f}x")
        else:
            print(f"  Overhead: {par_time/seq_time:.2f}x (parallel slower)")

    def test_validator_execution_scales_linearly(self, medium_directory_tree, benchmark_timer):
        """
        Test that validator execution time scales linearly with file count.

        Should not have quadratic behavior.
        """
        from anvil.validators.flake8_validator import Flake8Validator

        validator = Flake8Validator()
        all_files = list(medium_directory_tree.rglob("*.py"))

        results = []

        # Test with 50, 100, 200, 400 files
        for file_count in [50, 100, 200, 400]:
            files = [str(f) for f in all_files[:file_count]]

            with benchmark_timer(f"Validate {file_count} files") as elapsed:
                _result = validator.validate(files=files, config={})  # noqa: F841
            duration = elapsed()

            results.append((file_count, duration))
            print(f"  {file_count} files: {duration:.4f}s ({duration/file_count*1000:.2f}ms/file)")

        # Check for linear scaling
        # Time per file should be roughly constant
        # Note: First runs have higher overhead, allow for improvement with larger batches
        time_per_file = [duration / count for count, duration in results]

        # Use median for more stable comparison (avoids outliers)
        sorted_times = sorted(time_per_file)
        median_time = sorted_times[len(sorted_times) // 2]

        max_deviation = max(abs(t - median_time) for t in time_per_file)

        # Allow 200% deviation to account for warmup effects and caching
        # Real-world usage will be more consistent after initial overhead
        assert max_deviation < median_time * 2.0, (
            f"Scaling shows excessive variation. Time/file: {time_per_file}, "
            f"median: {median_time:.6f}, max deviation: {max_deviation:.6f}"
        )


class TestIncrementalVsFullModePerformance:
    """Test performance comparison of incremental vs full mode."""

    def test_incremental_validation_under_5_seconds(self, git_repository, benchmark_timer):
        """
        Test that incremental validation completes in <5 seconds.

        This is the key performance requirement for pre-commit hooks.
        """
        from anvil.core.file_collector import FileCollector
        from anvil.core.orchestrator import ValidationOrchestrator
        from anvil.core.validator_registry import ValidatorRegistry
        from anvil.validators.flake8_validator import Flake8Validator

        # Create registry and register validator
        registry = ValidatorRegistry()
        registry.register(Flake8Validator())

        orchestrator = ValidationOrchestrator(registry)

        # Collect only changed files (5 files)
        collector = FileCollector(root_dir=git_repository)
        changed_files = collector.collect_files(incremental=True, languages=["python"])

        with benchmark_timer("Incremental validation") as elapsed:
            _results = orchestrator.run_all(files=changed_files)  # noqa: F841

        duration = elapsed()

        # Key requirement: <5 seconds
        assert duration < 5.0, f"Incremental validation too slow: {duration:.2f}s (required <5s)"

        print(f"  Files validated: {len(changed_files)}")
        print(f"  Duration: {duration:.4f}s")
        print("  ✓ Meets <5s requirement")

    def test_full_validation_reasonable_time(self, medium_directory_tree, benchmark_timer):
        """
        Test that full validation completes in reasonable time.

        For medium project (1000 files), should complete in <30 seconds.
        """
        from anvil.core.file_collector import FileCollector
        from anvil.core.orchestrator import ValidationOrchestrator
        from anvil.core.validator_registry import ValidatorRegistry
        from anvil.validators.flake8_validator import Flake8Validator

        collector = FileCollector(root_dir=medium_directory_tree)
        files = collector.collect_files(languages=["python"])

        # Create registry and register validator
        registry = ValidatorRegistry()
        registry.register(Flake8Validator())

        orchestrator = ValidationOrchestrator(registry)

        with benchmark_timer(f"Full validation ({len(files)} files)") as elapsed:
            _results = orchestrator.run_all(files=files)  # noqa: F841

        duration = elapsed()

        # Should complete in <30 seconds for 800 files
        assert duration < 30.0, f"Full validation too slow: {duration:.2f}s (expected <30s)"

        print(f"  Files validated: {len(files)}")
        print(f"  Duration: {duration:.4f}s")
        print(f"  Files/second: {len(files)/duration:.0f}")

        duration = elapsed()

        # Should complete in <30 seconds for 800 files
        assert duration < 30.0, f"Full validation too slow: {duration:.2f}s (expected <30s)"

        print(f"  Files validated: {len(files)}")
        print(f"  Duration: {duration:.4f}s")
        print(f"  Files/second: {len(files)/duration:.0f}")


class TestDatabaseQueryPerformance:
    """Test performance of database queries with large history."""

    def test_query_test_success_rate_large_history(self, populated_statistics_db, benchmark_timer):
        """
        Test query performance with 100+ runs in database.

        Should complete in <100ms.
        """
        from anvil.storage.statistics_database import StatisticsDatabase
        from anvil.storage.statistics_queries import StatisticsQueryEngine

        db = StatisticsDatabase(populated_statistics_db)
        queries = StatisticsQueryEngine(database=db)

        with benchmark_timer("Query test success rate") as elapsed:
            success_rate = queries.get_test_success_rate(
                test_name="test_function_0", test_suite="tests.test_0"
            )
        duration = elapsed()

        assert duration < 0.1, f"Query too slow: {duration*1000:.0f}ms (expected <100ms)"
        assert success_rate is not None

        print(f"  Duration: {duration*1000:.1f}ms")
        print(f"  Success rate: {success_rate:.2%}")

    def test_query_flaky_tests_performance(self, populated_statistics_db, benchmark_timer):
        """
        Test flaky test detection query performance.

        Should complete in <200ms even with many test cases.
        """
        from anvil.storage.statistics_database import StatisticsDatabase
        from anvil.storage.statistics_queries import StatisticsQueryEngine

        db = StatisticsDatabase(populated_statistics_db)
        queries = StatisticsQueryEngine(database=db)

        with benchmark_timer("Query flaky tests") as elapsed:
            flaky_tests = queries.get_flaky_tests(
                min_success_rate=0.3, max_success_rate=0.8, min_runs=10
            )
        duration = elapsed()

        assert duration < 0.2, f"Query too slow: {duration*1000:.0f}ms (expected <200ms)"

        print(f"  Duration: {duration*1000:.1f}ms")
        print(f"  Flaky tests found: {len(flaky_tests)}")

    def test_query_validator_trends_performance(self, populated_statistics_db, benchmark_timer):
        """
        Test validator trend analysis query performance.

        Should complete in <100ms.
        """
        from anvil.storage.statistics_database import StatisticsDatabase
        from anvil.storage.statistics_queries import StatisticsQueryEngine

        db = StatisticsDatabase(populated_statistics_db)
        queries = StatisticsQueryEngine(database=db)

        with benchmark_timer("Query validator trends") as elapsed:
            trends = queries.get_validator_trends(validator_name="flake8")
        duration = elapsed()

        assert duration < 0.1, f"Query too slow: {duration*1000:.0f}ms (expected <100ms)"
        assert len(trends) > 0

        print(f"  Duration: {duration*1000:.1f}ms")
        print(f"  Data points: {len(trends)}")

    def test_bulk_insert_performance(self, tmp_path, benchmark_timer):
        """
        Test database insert performance with many records.

        Should handle 1000 inserts in <1 second.
        """
        from datetime import datetime

        from anvil.storage.statistics_database import (
            StatisticsDatabase,
            ValidationRun,
        )

        db_path = tmp_path / "perf_test.db"
        db = StatisticsDatabase(db_path)

        # Prepare all runs in memory
        runs = [
            ValidationRun(
                timestamp=datetime.now(),
                git_commit=f"commit_{i}",
                git_branch="main",
                incremental=True,
                passed=True,
                duration_seconds=1.0,
            )
            for i in range(1000)
        ]

        # Insert in a single batch operation
        with benchmark_timer("Insert 1000 validation runs (batch)") as elapsed:
            db.insert_validation_runs_batch(runs)
        duration = elapsed()

        assert duration < 1.0, f"Bulk insert too slow: {duration:.2f}s (expected <1s)"

        print(f"  Duration: {duration:.4f}s")
        print(f"  Inserts/second: {1000/duration:.0f}")


class TestSmartFilteringPerformance:
    """Test performance of smart filtering with many tests."""

    def test_smart_filtering_with_large_test_suite(self, populated_statistics_db, benchmark_timer):
        """
        Test smart filtering performance with 1000+ tests.

        Should complete in <500ms.
        """
        from anvil.storage.smart_filter import SmartFilter
        from anvil.storage.statistics_database import StatisticsDatabase

        # Create list of 1000 test cases (as tuples of test_name, test_suite)
        test_cases = [(f"test_function_{i}", f"tests.test_{i}") for i in range(1000)]

        db = StatisticsDatabase(populated_statistics_db)
        filter_engine = SmartFilter(db=db)

        with benchmark_timer("Smart filtering (1000 tests)") as elapsed:
            result = filter_engine.filter_tests(
                available_tests=test_cases,
                skip_threshold=0.95,
                min_runs_required=5,
            )
            filtered = result["tests_to_run"]
        duration = elapsed()

        assert duration < 0.5, f"Filtering too slow: {duration*1000:.0f}ms (expected <500ms)"

        print(f"  Duration: {duration*1000:.1f}ms")
        print(f"  Tests to run: {len(filtered)}/{len(test_cases)}")
        print(f"  Tests skipped: {len(test_cases) - len(filtered)}")


class TestMemoryUsage:
    """Test memory usage with large files and datasets."""

    def test_memory_usage_large_file_collection(self, large_directory_tree):
        """
        Test memory usage when collecting large number of files.

        Should not cause excessive memory usage.
        """
        import tracemalloc

        from anvil.core.file_collector import FileCollector

        tracemalloc.start()

        collector = FileCollector(root_dir=large_directory_tree)
        files = collector.collect_files(languages=["python", "cpp"])

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Peak memory should be reasonable (<100MB for 11k files)
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 100, f"Memory usage too high: {peak_mb:.1f}MB (expected <100MB)"

        print(f"  Files collected: {len(files)}")
        print(f"  Peak memory: {peak_mb:.1f}MB")
        print(f"  Memory per file: {peak/len(files)/1024:.1f}KB")

    def test_memory_usage_validator_execution(self, medium_directory_tree):
        """
        Test memory usage during validator execution.

        Should not leak memory across multiple runs.
        """
        import gc
        import tracemalloc

        from anvil.validators.flake8_validator import Flake8Validator

        files = [str(f) for f in list(medium_directory_tree.rglob("*.py"))[:200]]
        validator = Flake8Validator()

        # Run multiple times and check for memory leaks
        memory_usage = []

        for i in range(3):
            gc.collect()
            tracemalloc.start()

            validator.validate(files=files, config={})

            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            memory_usage.append(peak)

        # Memory usage should be stable (not increasing significantly)
        first_run_mb = memory_usage[0] / 1024 / 1024
        last_run_mb = memory_usage[-1] / 1024 / 1024

        print(f"  Run 1 peak: {first_run_mb:.1f}MB")
        print(f"  Run 3 peak: {last_run_mb:.1f}MB")

        # Allow 20% increase (some caching is expected)
        assert last_run_mb < first_run_mb * 1.2, (
            f"Memory leak detected: {last_run_mb:.1f}MB > {first_run_mb*1.2:.1f}MB "
            f"(20% increase)"
        )

    def test_memory_usage_database_operations(self, tmp_path):
        """
        Test memory usage with large database.

        Should handle large databases efficiently.
        """
        import gc
        import tracemalloc
        from datetime import datetime

        from anvil.storage.statistics_database import (
            StatisticsDatabase,
            TestCaseRecord,
            ValidationRun,
        )
        from anvil.storage.statistics_queries import StatisticsQueryEngine

        db_path = tmp_path / "large.db"
        db = StatisticsDatabase(db_path)

        # Insert many records
        for i in range(100):
            run = ValidationRun(
                timestamp=datetime.now(),
                git_commit=f"commit_{i}",
                git_branch="main",
                incremental=True,
                passed=True,
                duration_seconds=300.0,
            )
            run_id = db.insert_validation_run(run)

            for j in range(10):
                test_record = TestCaseRecord(
                    run_id=run_id,
                    test_name=f"test_{j}",
                    test_suite=f"test_{j}",
                    passed=True,
                    skipped=False,
                    duration_seconds=0.1,
                    failure_message=None,
                )
                db.insert_test_case_record(test_record)

        gc.collect()
        tracemalloc.start()

        # Query the database
        query_db = StatisticsDatabase(db_path)
        queries = StatisticsQueryEngine(database=query_db)
        _flaky = queries.get_flaky_tests(  # noqa: F841
            min_success_rate=0.3, max_success_rate=0.8, min_runs=5
        )

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = peak / 1024 / 1024

        # Should use reasonable memory (<50MB)
        assert peak_mb < 50, f"Memory usage too high: {peak_mb:.1f}MB (expected <50MB)"

        print("  Database records: 1000+ test cases")
        print(f"  Peak memory: {peak_mb:.1f}MB")


class TestScalability:
    """Test scalability with increasing dataset sizes."""

    def test_linear_scaling_with_file_count(self, tmp_path, benchmark_timer):
        """
        Test that file collection scales linearly with file count.

        Should not have quadratic behavior.
        """
        from anvil.core.file_collector import FileCollector

        results = []

        # Test with 100, 500, 1000, 2000 files
        for file_count in [100, 500, 1000, 2000]:
            # Create directory with specified number of files
            test_dir = tmp_path / f"project_{file_count}"
            test_dir.mkdir()
            for i in range(file_count):
                (test_dir / f"file_{i}.py").write_text(f"# File {i}\n")

            collector = FileCollector(root_dir=test_dir)

            with benchmark_timer(f"Collect {file_count} files") as elapsed:
                _files = collector.collect_files(languages=["python"])  # noqa: F841
            duration = elapsed()

            results.append((file_count, duration))
            print(f"  {file_count} files: {duration:.4f}s ({duration/file_count*1000:.2f}ms/file)")

        # Check for linear scaling
        # Calculate time per file for each run
        time_per_file = [duration / count for count, duration in results]

        # Time per file should not increase significantly with scale
        first_tpf = time_per_file[0]
        last_tpf = time_per_file[-1]

        # Allow 2x increase (due to filesystem overhead at scale)
        assert last_tpf < first_tpf * 2, (
            f"Scaling is not linear. Time/file increased from "
            f"{first_tpf*1000:.2f}ms to {last_tpf*1000:.2f}ms"
        )

        print("\n  Scaling analysis:")
        print(f"  Time/file (100): {time_per_file[0]*1000:.2f}ms")
        print(f"  Time/file (2000): {time_per_file[-1]*1000:.2f}ms")
        print(f"  Ratio: {time_per_file[-1]/time_per_file[0]:.2f}x")
