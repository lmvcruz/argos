"""
Validation Orchestrator for coordinating multiple validators.

This module provides the ValidationOrchestrator class which manages
the execution of multiple validators, supporting both sequential and
parallel execution modes, with comprehensive error handling and result
aggregation.
"""

import concurrent.futures
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from pathlib import Path
from typing import Dict, List, Optional

from anvil.core.validator_registry import ValidatorRegistry
from anvil.models.validator import Issue, ValidationResult


class ValidationOrchestrator:
    """
    Orchestrates validation execution across multiple validators.

    The orchestrator coordinates the execution of registered validators,
    supporting both sequential and parallel execution modes. It handles
    timeouts, errors, and aggregates results from all validators.

    Args:
        registry: The validator registry to use
        timeout: Maximum time (in seconds) allowed per validator. None means no timeout.
    """

    def __init__(self, registry: ValidatorRegistry, timeout: Optional[float] = None):
        """Initialize the orchestrator with a validator registry."""
        self._registry = registry
        self._timeout = timeout

    def run_all(
        self,
        files: List[Path],
        parallel: bool = False,
        fail_fast: bool = False,
        config: Optional[Dict] = None,
    ) -> List[ValidationResult]:
        """
        Run all registered validators on the given files.

        Args:
            files: List of file paths to validate
            parallel: If True, run validators in parallel
            fail_fast: If True, stop on first failure
            config: Configuration dictionary to pass to validators

        Returns:
            List of validation results from all validators

        Examples:
            >>> orch = ValidationOrchestrator(registry)
            >>> results = orch.run_all([Path("test.py")], parallel=True)
            >>> all_passed = all(r.passed for r in results)
        """
        if config is None:
            config = {}

        validators = self._registry.list_all()

        if parallel:
            return self._run_parallel(validators, files, config, fail_fast)
        else:
            return self._run_sequential(validators, files, config, fail_fast)

    def run_for_language(
        self,
        language: str,
        files: List[Path],
        parallel: bool = False,
        fail_fast: bool = False,
        config: Optional[Dict] = None,
    ) -> List[ValidationResult]:
        """
        Run validators for a specific language.

        Args:
            language: The language to run validators for
            files: List of file paths to validate
            parallel: If True, run validators in parallel
            fail_fast: If True, stop on first failure
            config: Configuration dictionary to pass to validators

        Returns:
            List of validation results from language-specific validators
        """
        if config is None:
            config = {}

        validators = self._registry.get_validators_by_language(language)

        if parallel:
            return self._run_parallel(validators, files, config, fail_fast)
        else:
            return self._run_sequential(validators, files, config, fail_fast)

    def run_validator(
        self, name: str, files: List[Path], config: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Run a specific validator by name.

        Args:
            name: Name of the validator to run
            files: List of file paths to validate
            config: Configuration dictionary to pass to validator

        Returns:
            Validation result from the specified validator

        Raises:
            KeyError: If validator with the given name is not found
        """
        if config is None:
            config = {}

        validator = self._registry.get_validator(name)
        if validator is None:
            raise KeyError(f"Validator '{name}' not found in registry")

        return self._run_single_validator(validator, files, config)

    def aggregate_results(self, results: List[ValidationResult]) -> Dict[str, any]:
        """
        Aggregate results from multiple validators into a summary.

        Args:
            results: List of validation results to aggregate

        Returns:
            Dictionary containing aggregated metrics including:
            - total_validators: Total number of validators run
            - passed: Number of validators that passed
            - failed: Number of validators that failed
            - total_errors: Total number of errors across all validators
            - total_warnings: Total number of warnings across all validators
            - total_files_checked: Total files checked (may include duplicates)
            - unique_files: Number of unique files checked
            - total_execution_time: Total time spent executing validators
            - overall_passed: True if all validators passed
        """
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        total_files = sum(r.files_checked for r in results)
        total_time = sum(r.execution_time or 0.0 for r in results)
        passed_count = sum(1 for r in results if r.passed)
        failed_count = len(results) - passed_count

        # Calculate unique files (assuming files are consistent across validators)
        unique_files = 0
        if results and len(results) > 0:
            if results[0].files_checked > 0:
                unique_files = results[0].files_checked

        return {
            "total_validators": len(results),
            "passed": passed_count,
            "failed": failed_count,
            "total_errors": total_errors,
            "total_warnings": total_warnings,
            "total_files_checked": total_files,
            "unique_files": unique_files,
            "total_execution_time": total_time,
            "overall_passed": all(r.passed for r in results),
        }

    def determine_overall_result(self, results: List[ValidationResult]) -> bool:
        """
        Determine overall pass/fail status from multiple results.

        Args:
            results: List of validation results

        Returns:
            True if all validators passed, False otherwise
        """
        return all(r.passed for r in results)

    def _run_sequential(
        self, validators: List, files: List[Path], config: Dict, fail_fast: bool
    ) -> List[ValidationResult]:
        """
        Run validators sequentially in order.

        Args:
            validators: List of validators to run
            files: List of files to validate
            config: Configuration dictionary
            fail_fast: Stop on first failure

        Returns:
            List of validation results
        """
        results = []

        for validator in validators:
            result = self._run_single_validator(validator, files, config)
            results.append(result)

            if fail_fast and not result.passed:
                break

        return results

    def _run_parallel(
        self, validators: List, files: List[Path], config: Dict, fail_fast: bool
    ) -> List[ValidationResult]:
        """
        Run validators in parallel using thread pool.

        Args:
            validators: List of validators to run
            files: List of files to validate
            config: Configuration dictionary
            fail_fast: Stop on first failure (note: parallel execution may
                      complete some tasks before stopping)

        Returns:
            List of validation results
        """
        results = []
        files_list = [files] * len(validators)
        config_list = [config] * len(validators)

        with ThreadPoolExecutor(max_workers=len(validators)) as executor:
            future_to_validator = {
                executor.submit(self._run_single_validator, validator, files, config): validator
                for validator, files, config in zip(validators, files_list, config_list)
            }

            for future in concurrent.futures.as_completed(future_to_validator):
                validator = future_to_validator[future]
                try:
                    result = future.result()
                    results.append(result)

                    if fail_fast and not result.passed:
                        # Cancel remaining futures
                        for f in future_to_validator:
                            if not f.done():
                                f.cancel()
                        break
                except Exception as e:
                    # Create error result for crashed validator
                    results.append(
                        ValidationResult(
                            validator_name=validator.name,
                            passed=False,
                            errors=[
                                Issue(
                                    file_path="<unknown>",
                                    line_number=0,
                                    message=f"Validator crashed: {str(e)}",
                                    severity="error",
                                )
                            ],
                            warnings=[],
                            files_checked=0,
                            execution_time=0.0,
                        )
                    )

        return results

    def _run_single_validator(self, validator, files: List[Path], config: Dict) -> ValidationResult:
        """
        Run a single validator with error handling and timeout.

        Args:
            validator: The validator to run
            files: List of files to validate
            config: Configuration dictionary

        Returns:
            Validation result from the validator
        """
        # Check if validator tool is available
        if not validator.is_available():
            return ValidationResult(
                validator_name=validator.name,
                passed=False,
                errors=[
                    Issue(
                        file_path="<system>",
                        line_number=0,
                        message=f"Validator tool '{validator.name}' is not available",
                        severity="error",
                    )
                ],
                warnings=[],
                files_checked=0,
                execution_time=0.0,
            )

        # Convert Path objects to strings for validator
        file_strings = [str(f) for f in files]

        start_time = time.time()

        try:
            if self._timeout is not None:
                # Run with timeout using thread pool
                with ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(validator.validate, file_strings, config)
                    try:
                        result = future.result(timeout=self._timeout)
                    except TimeoutError:
                        return ValidationResult(
                            validator_name=validator.name,
                            passed=False,
                            errors=[
                                Issue(
                                    file_path="<timeout>",
                                    line_number=0,
                                    message=(
                                        f"Validator '{validator.name}' "
                                        f"timed out after {self._timeout}s"
                                    ),
                                    severity="error",
                                )
                            ],
                            warnings=[],
                            files_checked=0,
                            execution_time=time.time() - start_time,
                        )
            else:
                # Run without timeout
                result = validator.validate(file_strings, config)

            return result

        except Exception as e:
            # Handle validator crashes
            return ValidationResult(
                validator_name=validator.name,
                passed=False,
                errors=[
                    Issue(
                        file_path="<crash>",
                        line_number=0,
                        message=f"Validator '{validator.name}' crashed: {str(e)}",
                        severity="error",
                    )
                ],
                warnings=[],
                files_checked=0,
                execution_time=time.time() - start_time,
            )
