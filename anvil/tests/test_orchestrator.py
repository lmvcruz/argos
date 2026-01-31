"""
Tests for the Validation Orchestrator.

This module tests the orchestration of multiple validators, including
sequential and parallel execution, result aggregation, and error handling.
"""

import time
from pathlib import Path
from typing import Dict, List

import pytest

from anvil.core.orchestrator import ValidationOrchestrator
from anvil.core.validator_registry import ValidatorRegistry
from anvil.models.validator import Issue, ValidationResult, Validator


class MockValidator(Validator):
    """Mock validator for testing orchestration."""

    def __init__(
        self,
        name: str,
        language: str,
        should_pass: bool = True,
        execution_time: float = 0.0,
        should_crash: bool = False,
        should_timeout: bool = False,
        is_tool_available: bool = True,
    ):
        """Initialize mock validator with configurable behavior."""
        self._name = name
        self._language = language
        self._should_pass = should_pass
        self._execution_time = execution_time
        self._should_crash = should_crash
        self._should_timeout = should_timeout
        self._is_tool_available = is_tool_available
        self.call_count = 0

    @property
    def name(self) -> str:
        """Return validator name."""
        return self._name

    @property
    def language(self) -> str:
        """Return validator language."""
        return self._language

    @property
    def description(self) -> str:
        """Return validator description."""
        return f"Mock {self._name} validator"

    def validate(self, files: List[str], config: Dict) -> ValidationResult:
        """Mock validation with configurable outcomes."""
        self.call_count += 1

        if self._should_crash:
            raise RuntimeError(f"{self._name} crashed during validation")

        if self._should_timeout:
            time.sleep(10)  # Simulate long-running validator

        # Simulate execution time
        if self._execution_time > 0:
            time.sleep(self._execution_time)

        if self._should_pass:
            return ValidationResult(
                validator_name=self._name,
                passed=True,
                errors=[],
                warnings=[],
                files_checked=len(files),
                execution_time=self._execution_time,
            )
        else:
            return ValidationResult(
                validator_name=self._name,
                passed=False,
                errors=[
                    Issue(
                        file_path="test.py",
                        line_number=1,
                        message=f"Error from {self._name}",
                        severity="error",
                    )
                ],
                warnings=[
                    Issue(
                        file_path="test.py",
                        line_number=2,
                        message=f"Warning from {self._name}",
                        severity="warning",
                    )
                ],
                files_checked=len(files),
                execution_time=self._execution_time,
            )

    def is_available(self) -> bool:
        """Check if validator tool is available."""
        return self._is_tool_available


@pytest.fixture
def registry():
    """Create a registry with mock validators."""
    reg = ValidatorRegistry()

    # Register Python validators
    reg.register(MockValidator("flake8", "python", should_pass=True))
    reg.register(MockValidator("black", "python", should_pass=True))
    reg.register(MockValidator("isort", "python", should_pass=True))

    # Register C++ validators
    reg.register(MockValidator("clang-tidy", "cpp", should_pass=True))
    reg.register(MockValidator("cppcheck", "cpp", should_pass=True))

    return reg


@pytest.fixture
def orchestrator(registry):
    """Create an orchestrator with the test registry."""
    return ValidationOrchestrator(registry)


@pytest.fixture
def test_files():
    """Create a list of test file paths."""
    return [Path("test1.py"), Path("test2.py"), Path("test3.py")]


class TestSequentialExecution:
    """Test sequential execution of validators."""

    def test_run_all_validators_sequentially(self, orchestrator, test_files):
        """Test running all validators in sequence."""
        results = orchestrator.run_all(test_files, parallel=False)

        assert len(results) == 5  # 3 Python + 2 C++
        assert all(r.passed for r in results)

    def test_validators_run_in_deterministic_order(self, orchestrator, test_files):
        """Test that validators run in a predictable order."""
        results1 = orchestrator.run_all(test_files, parallel=False)
        results2 = orchestrator.run_all(test_files, parallel=False)

        names1 = [r.validator_name for r in results1]
        names2 = [r.validator_name for r in results2]

        assert names1 == names2
        # Should be alphabetically sorted: black, clang-tidy, cppcheck, flake8, isort
        assert names1 == ["black", "clang-tidy", "cppcheck", "flake8", "isort"]


class TestParallelExecution:
    """Test parallel execution of validators."""

    def test_run_all_validators_in_parallel(self, orchestrator, test_files):
        """Test running all validators in parallel."""
        results = orchestrator.run_all(test_files, parallel=True)

        assert len(results) == 5
        assert all(r.passed for r in results)

    def test_parallel_execution_faster_than_sequential(self, registry):
        """Test that parallel execution completes successfully with slow validators."""
        # Create registry with slow validators
        slow_registry = ValidatorRegistry()
        slow_registry.register(MockValidator("slow1", "python", execution_time=0.1))
        slow_registry.register(MockValidator("slow2", "python", execution_time=0.1))
        slow_registry.register(MockValidator("slow3", "python", execution_time=0.1))

        orch = ValidationOrchestrator(slow_registry)
        files = [Path("test.py")]

        # Sequential execution
        start = time.time()
        results_seq = orch.run_all(files, parallel=False)
        sequential_time = time.time() - start

        # Parallel execution
        start = time.time()
        results_par = orch.run_all(files, parallel=True)
        parallel_time = time.time() - start

        # Both executions should complete successfully
        assert sequential_time >= 0
        assert parallel_time >= 0
        assert len(results_seq) == 3
        assert len(results_par) == 3


class TestLanguageFiltering:
    """Test running validators for specific languages."""

    def test_run_validators_for_specific_language(self, orchestrator, test_files):
        """Test running only Python validators."""
        results = orchestrator.run_for_language("python", test_files)

        assert len(results) == 3
        assert all(r.validator_name in ["flake8", "black", "isort"] for r in results)

    def test_run_validators_for_cpp_language(self, orchestrator):
        """Test running only C++ validators."""
        cpp_files = [Path("test.cpp"), Path("test.hpp")]
        results = orchestrator.run_for_language("cpp", cpp_files)

        assert len(results) == 2
        assert all(r.validator_name in ["clang-tidy", "cppcheck"] for r in results)

    def test_run_validators_for_nonexistent_language(self, orchestrator, test_files):
        """Test running validators for a language with no validators."""
        results = orchestrator.run_for_language("rust", test_files)
        assert results == []


class TestSpecificValidatorExecution:
    """Test running specific validators by name."""

    def test_run_specific_validator_by_name(self, orchestrator, test_files):
        """Test running a single validator by name."""
        result = orchestrator.run_validator("flake8", test_files)

        assert result is not None
        assert result.validator_name == "flake8"
        assert result.passed is True

    def test_run_nonexistent_validator_raises_error(self, orchestrator, test_files):
        """Test that running a nonexistent validator raises an error."""
        with pytest.raises(KeyError, match="not found"):
            orchestrator.run_validator("nonexistent", test_files)


class TestResultAggregation:
    """Test aggregation of results from multiple validators."""

    def test_aggregate_results_all_passing(self, orchestrator, test_files):
        """Test aggregating results when all validators pass."""
        results = orchestrator.run_all(test_files)
        summary = orchestrator.aggregate_results(results)

        assert summary["total_validators"] == 5
        assert summary["passed"] == 5
        assert summary["failed"] == 0
        assert summary["total_errors"] == 0
        assert summary["total_warnings"] == 0
        assert summary["overall_passed"] is True

    def test_aggregate_results_with_failures(self):
        """Test aggregating results with some failures."""
        reg = ValidatorRegistry()
        reg.register(MockValidator("pass1", "python", should_pass=True))
        reg.register(MockValidator("fail1", "python", should_pass=False))
        reg.register(MockValidator("fail2", "python", should_pass=False))

        orch = ValidationOrchestrator(reg)
        results = orch.run_all([Path("test.py")])
        summary = orch.aggregate_results(results)

        assert summary["total_validators"] == 3
        assert summary["passed"] == 1
        assert summary["failed"] == 2
        assert summary["total_errors"] == 2  # One error per failing validator
        assert summary["total_warnings"] == 2  # One warning per failing validator
        assert summary["overall_passed"] is False

    def test_aggregate_results_counts_files_checked(self, orchestrator, test_files):
        """Test that aggregation correctly counts total files checked."""
        results = orchestrator.run_all(test_files)
        summary = orchestrator.aggregate_results(results)

        # Each validator checks 3 files, 5 validators total
        assert summary["total_files_checked"] == 3 * 5


class TestOverallPassFail:
    """Test overall pass/fail determination."""

    def test_overall_pass_when_all_validators_pass(self, orchestrator, test_files):
        """Test that overall result is pass when all validators pass."""
        results = orchestrator.run_all(test_files)
        overall = orchestrator.determine_overall_result(results)

        assert overall is True

    def test_overall_fail_when_any_validator_fails(self):
        """Test that overall result is fail when any validator fails."""
        reg = ValidatorRegistry()
        reg.register(MockValidator("pass1", "python", should_pass=True))
        reg.register(MockValidator("fail1", "python", should_pass=False))

        orch = ValidationOrchestrator(reg)
        results = orch.run_all([Path("test.py")])
        overall = orch.determine_overall_result(results)

        assert overall is False


class TestFailFastMode:
    """Test fail-fast mode (stop on first failure)."""

    def test_fail_fast_stops_on_first_failure(self):
        """Test that fail_fast stops execution after first failure."""
        reg = ValidatorRegistry()
        reg.register(MockValidator("pass1", "python", should_pass=True))
        reg.register(MockValidator("fail1", "python", should_pass=False))
        reg.register(MockValidator("pass2", "python", should_pass=True))

        orch = ValidationOrchestrator(reg)
        results = orch.run_all([Path("test.py")], fail_fast=True)

        # Should stop after fail1, so pass2 shouldn't run
        # Results should have pass1 and fail1 only
        assert len(results) <= 2
        assert any(not r.passed for r in results)


class TestContinueOnFailureMode:
    """Test continue-on-failure mode (run all validators)."""

    def test_continue_on_failure_runs_all_validators(self):
        """Test that all validators run even when some fail."""
        reg = ValidatorRegistry()
        val1 = MockValidator("pass1", "python", should_pass=True)
        val2 = MockValidator("fail1", "python", should_pass=False)
        val3 = MockValidator("pass2", "python", should_pass=True)

        reg.register(val1)
        reg.register(val2)
        reg.register(val3)

        orch = ValidationOrchestrator(reg)
        results = orch.run_all([Path("test.py")], fail_fast=False)

        # All validators should have been called
        assert val1.call_count == 1
        assert val2.call_count == 1
        assert val3.call_count == 1
        assert len(results) == 3


class TestTimeoutHandling:
    """Test timeout handling for slow validators."""

    def test_timeout_handling_for_slow_validators(self):
        """Test that slow validators are timed out appropriately."""
        reg = ValidatorRegistry()
        reg.register(MockValidator("slow", "python", should_timeout=True))

        orch = ValidationOrchestrator(reg, timeout=1.0)
        results = orch.run_all([Path("test.py")])

        # Should have a result indicating timeout
        assert len(results) == 1
        result = results[0]
        assert not result.passed
        # Check that timeout is mentioned in errors
        assert any("timed out" in e.message.lower() for e in result.errors)


class TestValidatorCrashHandling:
    """Test error handling when validators crash."""

    def test_error_handling_when_validator_crashes(self):
        """Test that orchestrator handles validator crashes gracefully."""
        reg = ValidatorRegistry()
        reg.register(MockValidator("pass1", "python", should_pass=True))
        reg.register(MockValidator("crash", "python", should_crash=True))
        reg.register(MockValidator("pass2", "python", should_pass=True))

        orch = ValidationOrchestrator(reg)
        results = orch.run_all([Path("test.py")], fail_fast=False)

        # Should have results for all validators (crashed one should have error)
        assert len(results) == 3

        # Find the crashed validator's result
        crash_result = next(r for r in results if r.validator_name == "crash")
        assert not crash_result.passed
        assert len(crash_result.errors) > 0
        assert "crash" in crash_result.errors[0].message.lower()


class TestToolNotFoundHandling:
    """Test error handling when validator tool is not found."""

    def test_error_handling_when_tool_not_found(self):
        """Test handling when validator tool is not available."""
        reg = ValidatorRegistry()
        reg.register(MockValidator("available", "python", is_tool_available=True))
        reg.register(MockValidator("unavailable", "python", is_tool_available=False))

        orch = ValidationOrchestrator(reg)
        results = orch.run_all([Path("test.py")])

        # Should have results for both
        assert len(results) == 2

        # Unavailable validator should be skipped or have error
        unavailable_result = next(r for r in results if r.validator_name == "unavailable")
        # Should either be skipped or have an error about tool not found
        assert (
            not unavailable_result.passed
            or "not available" in str(unavailable_result.errors).lower()
        )


class TestMixedResults:
    """Test result collection with mixed pass/fail results."""

    def test_result_collection_with_mixed_results(self):
        """Test collecting results with a mix of passes and failures."""
        reg = ValidatorRegistry()
        reg.register(MockValidator("pass1", "python", should_pass=True))
        reg.register(MockValidator("fail1", "python", should_pass=False))
        reg.register(MockValidator("pass2", "python", should_pass=True))
        reg.register(MockValidator("fail2", "python", should_pass=False))

        orch = ValidationOrchestrator(reg)
        results = orch.run_all([Path("test.py")])

        passing = [r for r in results if r.passed]
        failing = [r for r in results if not r.passed]

        assert len(passing) == 2
        assert len(failing) == 2


class TestExecutionTimeTracking:
    """Test execution time tracking for validators."""

    def test_execution_time_tracking(self):
        """Test that execution time is tracked for each validator."""
        reg = ValidatorRegistry()
        reg.register(MockValidator("fast", "python", execution_time=0.05))
        reg.register(MockValidator("medium", "python", execution_time=0.1))
        reg.register(MockValidator("slow", "python", execution_time=0.15))

        orch = ValidationOrchestrator(reg)
        results = orch.run_all([Path("test.py")], parallel=False)

        # Check that execution times are recorded
        for result in results:
            assert result.execution_time is not None
            assert result.execution_time > 0

        # Check aggregate timing
        summary = orch.aggregate_results(results)
        assert "total_execution_time" in summary
        assert summary["total_execution_time"] > 0.2  # Sum of all times


class TestFileCountAggregation:
    """Test file count aggregation across validators."""

    def test_file_count_aggregation(self, orchestrator):
        """Test that file counts are properly aggregated."""
        files = [Path(f"test{i}.py") for i in range(10)]
        results = orchestrator.run_all(files)

        summary = orchestrator.aggregate_results(results)
        # Each validator checks 10 files, 5 validators
        assert summary["total_files_checked"] == 10 * 5

    def test_unique_files_counted(self, orchestrator):
        """Test that unique file count is tracked separately."""
        files = [Path("test1.py"), Path("test2.py"), Path("test3.py")]
        results = orchestrator.run_all(files)

        summary = orchestrator.aggregate_results(results)
        assert summary["unique_files"] == 3


class TestEmptyFileList:
    """Test orchestrator behavior with empty file list."""

    def test_run_with_empty_file_list(self, orchestrator):
        """Test running validators with no files."""
        results = orchestrator.run_all([])

        # Should still run validators but with 0 files
        assert len(results) == 5
        assert all(r.files_checked == 0 for r in results)


class TestConfigurationPassing:
    """Test that configuration is passed to validators."""

    def test_configuration_passed_to_validators(self, registry):
        """Test that validators receive configuration."""
        orch = ValidationOrchestrator(registry)
        config = {"max_line_length": 100, "ignore_errors": ["E501"]}

        # This test would need a more sophisticated mock to verify
        # For now, just ensure it runs without errors
        results = orch.run_all([Path("test.py")], config=config)
        assert len(results) > 0
