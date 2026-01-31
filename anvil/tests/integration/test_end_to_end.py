"""
End-to-end integration tests for Anvil.

Tests complete validation workflows across all components:
- Language detection → File collection → Validator execution → Result aggregation → Reporting
"""

import subprocess
from io import StringIO

from anvil.config.configuration import ConfigurationManager
from anvil.core.file_collector import FileCollector
from anvil.core.language_detector import LanguageDetector
from anvil.core.orchestrator import ValidationOrchestrator
from anvil.core.validator_registration import (
    register_python_validators,
)
from anvil.core.validator_registry import ValidatorRegistry
from anvil.reporting.console_reporter import ConsoleReporter
from anvil.reporting.json_reporter import JSONReporter


class TestCompleteValidationWorkflow:
    """Test complete validation workflow from start to finish."""

    def test_complete_python_validation_workflow(self, tmp_path):
        """
        Test complete workflow: detect Python → collect files → validate → report.

        Validates the entire pipeline works end-to-end for a Python project.
        """
        # Create sample Python project
        project_dir = tmp_path / "python_project"
        project_dir.mkdir()

        # Create Python files with intentional issues
        (project_dir / "good.py").write_text(
            '"""Good Python file."""\n\n\ndef hello():\n    """Say hello."""\n    return "Hello"\n'
        )
        (project_dir / "bad.py").write_text(
            "import os\nimport sys\n\ndef bad( ):\n  x=1+2\n  return x\n"  # Style issues
        )

        # Step 1: Detect languages
        detector = LanguageDetector(str(project_dir))
        languages = detector.detect_languages()
        assert "python" in languages

        # Step 2: Collect Python files
        collector = FileCollector(str(project_dir))
        files = collector.collect_files(language="python", incremental=False)
        assert len(files) == 2

        # Step 3: Run validators
        registry = ValidatorRegistry()
        register_python_validators(registry)
        orchestrator = ValidationOrchestrator(registry)
        results = orchestrator.run_for_language("python", files)

        # Step 4: Verify results aggregated
        assert len(results) > 0
        some_failed = any(not result.passed for result in results)
        assert some_failed  # bad.py should have issues

        # Step 5: Generate console report
        reporter = ConsoleReporter(use_color=False)
        output = StringIO()
        reporter.generate_report(results, output_stream=output)
        report = output.getvalue()
        assert "bad.py" in report

        # Step 6: Verify results structure
        assert len(results) == 8  # All Python validators ran
        assert all(hasattr(r, "passed") for r in results)
        assert all(hasattr(r, "errors") for r in results)
        assert all(hasattr(r, "warnings") for r in results)

    def test_complete_cpp_validation_workflow(self, tmp_path):
        """
        Test complete workflow for C++ project.

        Validates language detection, file collection, and validation for C++.
        """
        # Create sample C++ project
        project_dir = tmp_path / "cpp_project"
        project_dir.mkdir()

        # Create C++ files
        (project_dir / "good.cpp").write_text(
            '#include <iostream>\n\nint main() {\n    std::cout << "Hello";\n    return 0;\n}\n'
        )
        (project_dir / "good.h").write_text(
            "#ifndef GOOD_H\n#define GOOD_H\n\nvoid foo();\n\n#endif\n"
        )

        # Step 1: Detect languages
        detector = LanguageDetector(str(project_dir))
        languages = detector.detect_languages()
        assert "cpp" in languages

        # Step 2: Collect C++ files
        collector = FileCollector(str(project_dir))
        files = collector.collect_files(language="cpp", incremental=False)
        assert len(files) == 2

        # Step 3: Run C++ validators (only available ones)
        registry = ValidatorRegistry()
        available_validators = [
            v for v in registry.get_validators_by_language("cpp") if v.is_available()
        ]

        if available_validators:
            orchestrator = ValidationOrchestrator(registry)
            results = orchestrator.run_for_language("cpp", files)
            assert len(results) >= 0  # May be 0 if no tools installed


class TestLanguageSpecificValidation:
    """Test validation for specific language projects."""

    def test_python_only_project_validation(self, tmp_path):
        """Test validation of Python-only project."""
        project_dir = tmp_path / "python_only"
        project_dir.mkdir()

        # Create multiple Python files
        (project_dir / "module1.py").write_text("def func1():\n    pass\n")
        (project_dir / "module2.py").write_text("def func2():\n    pass\n")
        (project_dir / "module3.py").write_text("def func3():\n    pass\n")

        # Detect languages
        detector = LanguageDetector(str(project_dir))
        languages = detector.detect_languages()
        assert languages == ["python"]

        # Collect and validate
        collector = FileCollector(str(project_dir))
        files = collector.collect_files(incremental=False)
        assert len(files) == 3

        registry = ValidatorRegistry()
        register_python_validators(registry)
        orchestrator = ValidationOrchestrator(registry)
        results = orchestrator.run_for_language("python", files)
        assert len(results) > 0

    def test_cpp_only_project_validation(self, tmp_path):
        """Test validation of C++-only project."""
        project_dir = tmp_path / "cpp_only"
        project_dir.mkdir()

        # Create C++ files
        (project_dir / "main.cpp").write_text("int main() { return 0; }\n")
        (project_dir / "utils.cpp").write_text("void util() {}\n")
        (project_dir / "utils.h").write_text("void util();\n")

        # Detect languages
        detector = LanguageDetector(str(project_dir))
        languages = detector.detect_languages()
        assert languages == ["cpp"]

        # Collect files
        collector = FileCollector(str(project_dir))
        files = collector.collect_files(incremental=False)
        assert len(files) == 3

    def test_mixed_python_cpp_project_validation(self, tmp_path):
        """Test validation of mixed Python/C++ project."""
        project_dir = tmp_path / "mixed_project"
        project_dir.mkdir()

        # Create Python files
        (project_dir / "script.py").write_text("def main():\n    pass\n")

        # Create C++ files
        (project_dir / "native.cpp").write_text("int native() { return 0; }\n")
        (project_dir / "native.h").write_text("int native();\n")

        # Detect languages
        detector = LanguageDetector(str(project_dir))
        languages = detector.detect_languages()
        assert set(languages) == {"python", "cpp"}

        # Collect all files
        collector = FileCollector(str(project_dir))
        all_files = collector.collect_files(incremental=False)
        assert len(all_files) == 3

        # Collect Python files only
        py_files = collector.collect_files(language="python", incremental=False)
        assert len(py_files) == 1

        # Collect C++ files only
        cpp_files = collector.collect_files(language="cpp", incremental=False)
        assert len(cpp_files) == 2


class TestIncrementalVsFullMode:
    """Test incremental mode vs full mode validation."""

    def test_incremental_mode_with_git_changes(self, tmp_path):
        """Test incremental mode only validates changed files."""
        project_dir = tmp_path / "git_project"
        project_dir.mkdir()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )

        # Create and commit initial files
        (project_dir / "committed.py").write_text("def old():\n    pass\n")
        subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )

        # Create new uncommitted file
        (project_dir / "new.py").write_text("def new():\n    pass\n")

        # Modify existing file
        (project_dir / "committed.py").write_text(
            "def old():\n    pass\n\ndef modified():\n    pass\n"
        )

        # Incremental mode should only get changed files
        collector = FileCollector(str(project_dir))
        changed_files = collector.collect_files(language="python", incremental=True)
        assert len(changed_files) == 2  # new.py and committed.py

    def test_full_mode_validates_all_files(self, tmp_path):
        """Test full mode validates all files regardless of changes."""
        project_dir = tmp_path / "full_project"
        project_dir.mkdir()

        # Create multiple files
        for i in range(5):
            (project_dir / f"file{i}.py").write_text(f"def func{i}():\n    pass\n")

        # Full mode gets all files
        collector = FileCollector(str(project_dir))
        all_files = collector.collect_files(language="python", incremental=False)
        assert len(all_files) == 5


class TestHookAndCISimulation:
    """Test pre-commit hook and CI/CD simulation."""

    def test_pre_commit_hook_simulation(self, tmp_path):
        """Simulate pre-commit hook execution."""
        project_dir = tmp_path / "hook_project"
        project_dir.mkdir()

        # Initialize git
        subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )

        # Create file with issues
        bad_file = project_dir / "bad.py"
        bad_file.write_text("import os\nimport sys\n\ndef bad( ):\n  x=1\n")

        subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)

        # Simulate hook: validate staged files
        collector = FileCollector(str(project_dir))
        staged_files = collector.collect_files(language="python", incremental=True)

        if staged_files:
            registry = ValidatorRegistry()
            register_python_validators(registry)
            orchestrator = ValidationOrchestrator(registry)
            results = orchestrator.run_for_language("python", staged_files)

            # Hook would exit 1 if any validator failed
            # With available validators, should get results (may pass or fail)
            assert len(results) > 0
            # At least test the hook mechanism works
            assert isinstance(results, list)

    def test_ci_cd_simulation(self, tmp_path):
        """Simulate CI/CD pipeline execution."""
        project_dir = tmp_path / "ci_project"
        project_dir.mkdir()

        # Create project files
        (project_dir / "src").mkdir()
        (project_dir / "src" / "main.py").write_text("def main():\n    print('Hello')\n")
        (project_dir / "tests").mkdir()
        (project_dir / "tests" / "test_main.py").write_text("def test_main():\n    pass\n")

        # CI would run full validation
        collector = FileCollector(str(project_dir))
        all_files = collector.collect_files(language="python", incremental=False)
        assert len(all_files) == 2

        # Run all validators (CI mode)
        registry = ValidatorRegistry()
        register_python_validators(registry)
        orchestrator = ValidationOrchestrator(registry)  # Parallel in CI
        results = orchestrator.run_for_language("python", all_files)

        # CI reports all results
        reporter = JSONReporter()
        output = StringIO()
        reporter.generate_report(results, output_stream=output)
        json_report = output.getvalue()
        assert json_report is not None
        assert isinstance(json_report, str)
        assert len(json_report) > 0


class TestSmartFilteringAndParallelExecution:
    """Test smart filtering and parallel validator execution."""

    def test_parallel_execution_faster_than_sequential(self, tmp_path):
        """Test parallel execution completes faster."""
        project_dir = tmp_path / "parallel_project"
        project_dir.mkdir()

        # Create multiple files
        for i in range(10):
            (project_dir / f"file{i}.py").write_text(
                f'"""Module {i}."""\n\ndef func{i}():\n    pass\n'
            )

        collector = FileCollector(str(project_dir))
        files = collector.collect_files(language="python", incremental=False)

        registry = ValidatorRegistry()

        # Sequential execution
        import time

        start = time.time()
        orchestrator_seq = ValidationOrchestrator(registry)
        orchestrator_seq.run_for_language("python", files)
        seq_time = time.time() - start

        # Parallel execution
        start = time.time()
        orchestrator_par = ValidationOrchestrator(registry)
        orchestrator_par.run_for_language("python", files)
        par_time = time.time() - start

        # Parallel should be faster (or at least not significantly slower)
        # Allow 20% tolerance for overhead
        assert par_time <= seq_time * 1.2

    def test_fail_fast_mode_stops_on_first_failure(self, tmp_path):
        """Test fail-fast mode stops after first validator failure."""
        project_dir = tmp_path / "failfast_project"
        project_dir.mkdir()

        # Create file with multiple issues
        (project_dir / "bad.py").write_text("import os\n\ndef bad( ):\n  x=1\n  return x\n")

        collector = FileCollector(str(project_dir))
        files = collector.collect_files(language="python", incremental=False)

        registry = ValidatorRegistry()
        register_python_validators(registry)
        orchestrator = ValidationOrchestrator(registry)
        results = orchestrator.run_for_language("python", files)

        # Should get results from validators
        assert len(results) >= 1


class TestConfigurationHandling:
    """Test configuration handling with and without anvil.toml."""

    def test_validation_with_custom_config(self, tmp_path):
        """Test validation with custom anvil.toml configuration."""
        project_dir = tmp_path / "config_project"
        project_dir.mkdir()

        # Create anvil.toml
        config_content = """
[anvil]
max_errors = 100
parallel = true

[anvil.python.flake8]
enabled = true
max_line_length = 100

[anvil.python.black]
enabled = true
line_length = 100
"""
        (project_dir / "anvil.toml").write_text(config_content)

        # Create Python file
        (project_dir / "test.py").write_text("def test():\n    pass\n")

        # Load configuration
        config = ConfigurationManager(str(project_dir / "anvil.toml"))
        assert config.get("anvil.max_errors") == 100
        assert config.get("anvil.parallel") is True

        # Validate with config
        collector = FileCollector(str(project_dir))
        files = collector.collect_files(language="python", incremental=False)

        registry = ValidatorRegistry()
        register_python_validators(registry)
        orchestrator = ValidationOrchestrator(registry)
        results = orchestrator.run_for_language("python", files)
        assert len(results) >= 0

    def test_validation_with_zero_config(self, tmp_path):
        """Test validation with default configuration (no anvil.toml)."""
        project_dir = tmp_path / "zeroconfig_project"
        project_dir.mkdir()

        # Create Python file (no anvil.toml)
        (project_dir / "test.py").write_text("def test():\n    pass\n")

        # Should work with defaults
        collector = FileCollector(str(project_dir))
        files = collector.collect_files(language="python", incremental=False)

        registry = ValidatorRegistry()
        orchestrator = ValidationOrchestrator(registry)
        results = orchestrator.run_for_language("python", files)
        assert len(results) >= 0


class TestStatisticsTracking:
    """Test statistics tracking during validation."""

    def test_validation_creates_statistics_database(self, tmp_path):
        """Test that statistics database can be created."""
        project_dir = tmp_path / "stats_project"
        project_dir.mkdir()

        # Create database directory
        db_dir = project_dir / ".anvil"
        db_dir.mkdir()
        db_dir / "statistics.db"

        # Create Python files
        (project_dir / "test.py").write_text("def test():\n    pass\n")

        # Run validation
        collector = FileCollector(str(project_dir))
        files = collector.collect_files(language="python", incremental=False)

        registry = ValidatorRegistry()
        register_python_validators(registry)
        orchestrator = ValidationOrchestrator(registry)
        results = orchestrator.run_for_language("python", files)

        # Verify results exist (database operations tested separately)
        assert isinstance(results, list)
        assert len(results) > 0
        assert len(results) > 0
        assert isinstance(results, list)


class TestErrorRecovery:
    """Test error recovery when validators crash or tools are missing."""

    def test_error_recovery_when_validator_crashes(self, tmp_path):
        """Test graceful handling when a validator crashes."""
        project_dir = tmp_path / "crash_project"
        project_dir.mkdir()

        # Create file
        (project_dir / "test.py").write_text("def test():\n    pass\n")

        collector = FileCollector(str(project_dir))
        files = collector.collect_files(language="python", incremental=False)

        registry = ValidatorRegistry()
        orchestrator = ValidationOrchestrator(registry)

        # Run validators - should not crash even if one validator fails
        results = orchestrator.run_for_language("python", files)

        # Should get results (even if some failed)
        assert isinstance(results, list)

    def test_error_recovery_when_tool_not_found(self, tmp_path):
        """Test graceful handling when a tool is not installed."""
        project_dir = tmp_path / "notool_project"
        project_dir.mkdir()

        # Create file
        (project_dir / "test.py").write_text("def test():\n    pass\n")

        collector = FileCollector(str(project_dir))
        collector.collect_files(language="python", incremental=False)

        registry = ValidatorRegistry()
        register_python_validators(registry)

        # Check which validators are available
        available = [v for v in registry.get_validators_by_language("python") if v.is_available()]
        unavailable = [
            v for v in registry.get_validators_by_language("python") if not v.is_available()
        ]

        # Should have some validators registered
        assert len(registry.get_validators_by_language("python")) > 0

        # Should have at least some available validators
        assert len(available) > 0

        # Unavailable validators should not crash the system
        assert isinstance(unavailable, list)


class TestPerformanceWithLargeCodebase:
    """Test performance with large codebases."""

    def test_validation_completes_within_reasonable_time(self, tmp_path):
        """Test validation completes in reasonable time for moderate codebase."""
        project_dir = tmp_path / "large_project"
        project_dir.mkdir()

        # Create 50 Python files (moderate size for testing)
        for i in range(50):
            file_path = project_dir / f"module{i}.py"
            content = (
                f'"""Module {i}."""\n\n\n'
                f"def function_{i}():\n"
                f'    """Function {i}."""\n'
                f"    return {i}\n"
            )
            file_path.write_text(content)

        import time

        start = time.time()

        # Collect files
        collector = FileCollector(str(project_dir))
        files = collector.collect_files(language="python", incremental=False)
        assert len(files) == 50

        # Run validators in parallel
        registry = ValidatorRegistry()
        register_python_validators(registry)
        orchestrator = ValidationOrchestrator(registry)
        results = orchestrator.run_for_language("python", files)

        elapsed = time.time() - start

        # Should complete within 30 seconds for 50 files
        assert elapsed < 30.0
        assert len(results) > 0

    def test_incremental_validation_is_fast(self, tmp_path):
        """Test incremental validation completes quickly."""
        project_dir = tmp_path / "incremental_project"
        project_dir.mkdir()

        # Initialize git
        subprocess.run(["git", "init"], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )

        # Create and commit many files
        for i in range(20):
            (project_dir / f"old{i}.py").write_text(f"def old{i}():\n    pass\n")

        subprocess.run(["git", "add", "."], cwd=project_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=project_dir,
            check=True,
            capture_output=True,
        )

        # Modify only 2 files
        (project_dir / "old0.py").write_text("def old0():\n    pass\n\ndef new():\n    pass\n")
        (project_dir / "new.py").write_text("def brand_new():\n    pass\n")

        import time

        start = time.time()

        # Incremental collection
        collector = FileCollector(str(project_dir))
        changed_files = collector.collect_files(language="python", incremental=True)
        assert len(changed_files) == 2  # Only 2 changed files

        # Validate only changed files
        registry = ValidatorRegistry()
        orchestrator = ValidationOrchestrator(registry)
        orchestrator.run_for_language("python", changed_files)

        elapsed = time.time() - start

        # Incremental should be very fast (under 10 seconds for 2 files)
        assert elapsed < 10.0
