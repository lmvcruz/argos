"""
Radon parser module.

This module provides parsing functionality for radon JSON output,
extracting cyclomatic complexity metrics, maintainability index,
and raw code metrics (LOC, LLOC, comments).
"""

import json
import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from anvil.models.validator import Issue, ValidationResult


class RadonParser:
    """
    Parser for radon JSON output.

    Parses radon complexity analysis results including:
    - Cyclomatic complexity (CC): Function and method complexity scores
    - Maintainability index (MI): Overall code maintainability rating
    - Raw metrics: Lines of code, logical lines, comments, blank lines
    """

    @staticmethod
    def parse_cc(
        json_output: str, files: List[Path], config: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Parse radon cyclomatic complexity (CC) output into ValidationResult.

        Args:
            json_output: JSON string output from radon cc
            files: List of files that were validated
            config: Configuration dictionary with options:
                - max_complexity: Maximum allowed complexity (default: 10)

        Returns:
            ValidationResult containing parsed complexity issues

        Raises:
            json.JSONDecodeError: If JSON output is invalid
        """
        if config is None:
            config = {}

        max_complexity = config.get("max_complexity", 10)
        data = json.loads(json_output)

        warnings = []

        for file_path, functions in data.items():
            if not functions:
                continue

            for func in functions:
                complexity = func.get("complexity", 0)
                name = func.get("name", "unknown")
                lineno = func.get("lineno", 0)
                rank = func.get("rank", "?")

                if complexity > max_complexity:
                    issue = Issue(
                        file_path=file_path,
                        line_number=lineno,
                        column_number=None,
                        severity="warning",
                        rule_name="high-complexity",
                        message=f"Function '{name}' has complexity {complexity} (rank {rank}), "
                        f"exceeds maximum {max_complexity}",
                        error_code="CC",
                    )
                    warnings.append(issue)

                # Process closures if present
                closures = func.get("closures", [])
                for closure in closures:
                    closure_complexity = closure.get("complexity", 0)
                    closure_name = closure.get("name", "unknown")
                    closure_lineno = closure.get("lineno", 0)
                    closure_rank = closure.get("rank", "?")

                    if closure_complexity > max_complexity:
                        issue = Issue(
                            file_path=file_path,
                            line_number=closure_lineno,
                            column_number=None,
                            severity="warning",
                            rule_name="high-complexity",
                            message=f"Closure '{closure_name}' has complexity {closure_complexity} "
                            f"(rank {closure_rank}), exceeds maximum {max_complexity}",
                            error_code="CC",
                        )
                        warnings.append(issue)

        passed = len(warnings) == 0

        return ValidationResult(
            validator_name="radon-cc",
            passed=passed,
            errors=[],
            warnings=warnings,
            files_checked=len(files),
        )

    @staticmethod
    def parse_mi(
        json_output: str, files: List[Path], config: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Parse radon maintainability index (MI) output into ValidationResult.

        Args:
            json_output: JSON string output from radon mi
            files: List of files that were validated
            config: Configuration dictionary with options:
                - min_maintainability: Minimum required MI score (default: 20)

        Returns:
            ValidationResult containing parsed MI issues

        Raises:
            json.JSONDecodeError: If JSON output is invalid
        """
        if config is None:
            config = {}

        min_maintainability = config.get("min_maintainability", 20)
        data = json.loads(json_output)

        warnings = []

        for file_path, metrics in data.items():
            if isinstance(metrics, dict):
                mi = metrics.get("mi", 100)
                rank = metrics.get("rank", "A")

                if mi < min_maintainability:
                    issue = Issue(
                        file_path=file_path,
                        line_number=1,
                        column_number=None,
                        severity="warning",
                        rule_name="low-maintainability",
                        message=f"Maintainability index {mi:.2f} (rank {rank}), "
                        f"below minimum {min_maintainability}",
                        error_code="MI",
                    )
                    warnings.append(issue)

        passed = len(warnings) == 0

        return ValidationResult(
            validator_name="radon-mi",
            passed=passed,
            errors=[],
            warnings=warnings,
            files_checked=len(files),
        )

    @staticmethod
    def parse_raw(json_output: str, files: List[Path]) -> ValidationResult:
        """
        Parse radon raw metrics output.

        Raw metrics are informational only and do not generate warnings.

        Args:
            json_output: JSON string output from radon raw
            files: List of files that were validated

        Returns:
            ValidationResult (always passes, informational only)

        Raises:
            json.JSONDecodeError: If JSON output is invalid
        """
        # Parse to validate JSON, but raw metrics are informational only
        json.loads(json_output)

        return ValidationResult(
            validator_name="radon-raw",
            passed=True,
            errors=[],
            warnings=[],
            files_checked=len(files),
        )

    @staticmethod
    def build_cc_command(files: List[Path], config: Dict) -> List[str]:
        """
        Build radon cc command with configuration options.

        Args:
            files: List of files to analyze
            config: Configuration dictionary with options:
                - min_grade: Minimum grade threshold (A-F)
                - show_closures: Include closures in output
                - exclude: Exclude patterns

        Returns:
            List of command arguments
        """
        command = ["radon", "cc", "--json"]

        # Add min grade threshold
        if "min_grade" in config:
            command.append(f"--min={config['min_grade']}")

        # Add show closures option
        if config.get("show_closures", False):
            command.append("--show-closures")

        # Add exclude patterns
        if "exclude" in config:
            command.append(f"--exclude={config['exclude']}")

        # Add files
        for file in files:
            command.append(str(file))

        return command

    @staticmethod
    def build_mi_command(files: List[Path], config: Dict) -> List[str]:
        """
        Build radon mi command with configuration options.

        Args:
            files: List of files to analyze
            config: Configuration dictionary with options:
                - show_details: Show detailed MI information

        Returns:
            List of command arguments
        """
        command = ["radon", "mi", "--json"]

        # Add show details option
        if config.get("show_details", False):
            command.append("--show")

        # Add files
        for file in files:
            command.append(str(file))

        return command

    @staticmethod
    def build_raw_command(files: List[Path], config: Dict) -> List[str]:
        """
        Build radon raw metrics command.

        Args:
            files: List of files to analyze
            config: Configuration dictionary (currently unused)

        Returns:
            List of command arguments
        """
        command = ["radon", "raw", "--json"]

        # Add files
        for file in files:
            command.append(str(file))

        return command

    @staticmethod
    def run_radon_cc(
        files: List[Path], config: Dict, timeout: int = 300
    ) -> subprocess.CompletedProcess:
        """
        Execute radon cc command.

        Args:
            files: List of files to analyze
            config: Configuration dictionary
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess with stdout and stderr

        Raises:
            FileNotFoundError: If radon is not installed
            TimeoutError: If command exceeds timeout
        """
        command = RadonParser.build_cc_command(files, config)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return result
        except FileNotFoundError:
            raise FileNotFoundError("radon not found. Install with: pip install radon")
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"radon command timed out after {timeout} seconds") from e

    @staticmethod
    def run_radon_mi(
        files: List[Path], config: Dict, timeout: int = 300
    ) -> subprocess.CompletedProcess:
        """
        Execute radon mi command.

        Args:
            files: List of files to analyze
            config: Configuration dictionary
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess with stdout and stderr

        Raises:
            FileNotFoundError: If radon is not installed
            TimeoutError: If command exceeds timeout
        """
        command = RadonParser.build_mi_command(files, config)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return result
        except FileNotFoundError:
            raise FileNotFoundError("radon not found. Install with: pip install radon")
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"radon command timed out after {timeout} seconds") from e

    @staticmethod
    def run_radon_raw(
        files: List[Path], config: Dict, timeout: int = 300
    ) -> subprocess.CompletedProcess:
        """
        Execute radon raw command.

        Args:
            files: List of files to analyze
            config: Configuration dictionary
            timeout: Command timeout in seconds

        Returns:
            CompletedProcess with stdout and stderr

        Raises:
            FileNotFoundError: If radon is not installed
            TimeoutError: If command exceeds timeout
        """
        command = RadonParser.build_raw_command(files, config)

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            return result
        except FileNotFoundError:
            raise FileNotFoundError("radon not found. Install with: pip install radon")
        except subprocess.TimeoutExpired as e:
            raise TimeoutError(f"radon command timed out after {timeout} seconds") from e

    @staticmethod
    def run_and_parse_cc(files: List[Path], config: Dict) -> ValidationResult:
        """
        Run radon cc and parse the output.

        Args:
            files: List of files to analyze
            config: Configuration dictionary

        Returns:
            ValidationResult with parsed complexity issues
        """
        try:
            result = RadonParser.run_radon_cc(files, config)
            return RadonParser.parse_cc(result.stdout, files, config)
        except (FileNotFoundError, TimeoutError) as e:
            # Return failed result with error
            return ValidationResult(
                validator_name="radon-cc",
                passed=False,
                errors=[
                    Issue(
                        file_path=str(files[0]) if files else ".",
                        line_number=1,
                        column_number=None,
                        severity="error",
                        message=str(e),
                        rule_name="RADON_ERROR",
                        error_code="RADON_ERROR",
                    )
                ],
                warnings=[],
                files_checked=len(files),
            )

    @staticmethod
    def run_and_parse_mi(files: List[Path], config: Dict) -> ValidationResult:
        """
        Run radon mi and parse the output.

        Args:
            files: List of files to analyze
            config: Configuration dictionary

        Returns:
            ValidationResult with parsed MI issues
        """
        try:
            result = RadonParser.run_radon_mi(files, config)
            return RadonParser.parse_mi(result.stdout, files, config)
        except (FileNotFoundError, TimeoutError) as e:
            # Return failed result with error
            return ValidationResult(
                validator_name="radon-mi",
                passed=False,
                errors=[
                    Issue(
                        file_path=str(files[0]) if files else ".",
                        line_number=1,
                        column_number=None,
                        severity="error",
                        message=str(e),
                        rule_name="RADON_ERROR",
                        error_code="RADON_ERROR",
                    )
                ],
                warnings=[],
                files_checked=len(files),
            )

    @staticmethod
    def run_and_parse_raw(files: List[Path], config: Dict) -> ValidationResult:
        """
        Run radon raw and parse the output.

        Args:
            files: List of files to analyze
            config: Configuration dictionary

        Returns:
            ValidationResult (informational only)
        """
        try:
            result = RadonParser.run_radon_raw(files, config)
            return RadonParser.parse_raw(result.stdout, files)
        except (FileNotFoundError, TimeoutError) as e:
            # Return failed result with error
            return ValidationResult(
                validator_name="radon-raw",
                passed=False,
                errors=[
                    Issue(
                        file_path=str(files[0]) if files else ".",
                        line_number=1,
                        column_number=None,
                        severity="error",
                        message=str(e),
                        rule_name="RADON_ERROR",
                        error_code="RADON_ERROR",
                    )
                ],
                warnings=[],
                files_checked=len(files),
            )

    @staticmethod
    def run_and_parse(files: List, config: Optional[Dict] = None) -> ValidationResult:
        """
        Run radon and parse the output.

        This is the standard parser interface that delegates to the specific
        radon metric based on configuration. Defaults to cyclomatic complexity.

        Args:
            files: List of files to analyze
            config: Configuration dictionary with optional 'metric' field:
                - 'cc' or missing: Cyclomatic complexity (default)
                - 'mi': Maintainability index
                - 'raw': Raw metrics

        Returns:
            ValidationResult with parsed issues
        """
        if config is None:
            config = {}

        # Convert to Path objects if needed
        from pathlib import Path

        file_paths = [Path(f) if not isinstance(f, Path) else f for f in files]

        # Determine which metric to run
        metric = config.get("metric", "cc")

        if metric == "mi":
            return RadonParser.run_and_parse_mi(file_paths, config)
        elif metric == "raw":
            return RadonParser.run_and_parse_raw(file_paths, config)
        else:  # Default to cc (cyclomatic complexity)
            return RadonParser.run_and_parse_cc(file_paths, config)

    @staticmethod
    def get_version() -> Optional[str]:
        """
        Get radon version.

        Returns:
            Version string (e.g., "5.1.0") or None if not found
        """
        try:
            result = subprocess.run(
                ["radon", "--version"],
                capture_output=True,
                text=True,
                check=False,
                timeout=10,
            )

            # Parse version from output like: "radon 5.1.0"
            match = re.search(r"radon\s+([\d.]+)", result.stdout)
            if match:
                return match.group(1)

            return None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    @staticmethod
    def find_config_file(directory: Path) -> Optional[Path]:
        """
        Find radon configuration file in directory.

        Searches for configuration files in order:
        1. pyproject.toml (with [tool.radon] section)
        2. setup.cfg (with [radon] section)

        Args:
            directory: Directory to search

        Returns:
            Path to config file or None if not found
        """
        # Check for pyproject.toml with radon config
        pyproject = directory / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[tool.radon" in content:
                return pyproject

        # Check for setup.cfg with radon config
        setup_cfg = directory / "setup.cfg"
        if setup_cfg.exists():
            content = setup_cfg.read_text()
            if "[radon" in content:
                return setup_cfg

        return None

    @staticmethod
    def calculate_average_complexity(json_output: str) -> float:
        """
        Calculate average complexity across all functions.

        Args:
            json_output: JSON string output from radon cc

        Returns:
            Average complexity score
        """
        data = json.loads(json_output)

        total_complexity = 0
        function_count = 0

        for functions in data.values():
            if not functions:
                continue

            for func in functions:
                total_complexity += func.get("complexity", 0)
                function_count += 1

                # Include closures
                for closure in func.get("closures", []):
                    total_complexity += closure.get("complexity", 0)
                    function_count += 1

        if function_count == 0:
            return 0.0

        return total_complexity / function_count

    @staticmethod
    def identify_high_complexity_functions(json_output: str, threshold: int) -> List[Dict]:
        """
        Identify functions with complexity above threshold.

        Args:
            json_output: JSON string output from radon cc
            threshold: Complexity threshold

        Returns:
            List of functions exceeding threshold
        """
        data = json.loads(json_output)

        high_complexity = []

        for file_path, functions in data.items():
            if not functions:
                continue

            for func in functions:
                complexity = func.get("complexity", 0)
                if complexity > threshold:
                    func["file"] = file_path
                    high_complexity.append(func)

                # Include closures
                for closure in func.get("closures", []):
                    closure_complexity = closure.get("complexity", 0)
                    if closure_complexity > threshold:
                        closure["file"] = file_path
                        high_complexity.append(closure)

        return high_complexity
