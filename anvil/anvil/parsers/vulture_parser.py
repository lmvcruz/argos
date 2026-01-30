"""
Parser for vulture - finds dead/unused code in Python programs.

Vulture detects unused functions, methods, classes, variables, imports, and
properties with confidence percentages. This parser extracts all findings,
filters by confidence threshold, and provides statistics on dead code.
"""

import re
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from anvil.models.validator import Issue, ValidationResult


class VultureParser:
    """
    Parser for vulture output.

    Vulture finds unused code (functions, classes, variables, imports, etc.) and
    reports them with confidence scores. This parser handles text output format.
    """

    @staticmethod
    def parse_text(
        text_output: str, files: List[Path], config: Optional[Dict] = None
    ) -> ValidationResult:
        """
        Parse vulture text output into ValidationResult.

        Vulture output format:
            file.py:line: unused <type> '<name>' (<confidence>% confidence)

        Args:
            text_output: Text output from vulture
            files: List of files that were analyzed
            config: Configuration dict with options like min_confidence

        Returns:
            ValidationResult with unused code findings as warnings
        """
        if config is None:
            config = {}

        issues = []
        min_confidence = config.get("min_confidence", 0)

        # Parse each line of vulture output
        for line in text_output.strip().split("\n"):
            if not line.strip():
                continue

            # Pattern: file.py:line: unused <type> '<name>' (<confidence>% confidence)
            pattern = r"^(.+?):(\d+):\s+(.+?)\s+\((\d+)%\s+confidence\)"
            match = re.match(pattern, line)

            if match:
                file_path = match.group(1)
                line_number = int(match.group(2))
                message = match.group(3)
                confidence = int(match.group(4))

                # Filter by minimum confidence threshold
                if confidence < min_confidence:
                    continue

                issue = Issue(
                    file_path=file_path,
                    line_number=line_number,
                    column_number=None,
                    message=f"{message} ({confidence}% confidence)",
                    severity="warning",
                    rule_name="dead-code",
                )
                issues.append(issue)

        # All unused code findings are warnings
        passed = len(issues) == 0

        return ValidationResult(
            validator_name="vulture",
            passed=passed,
            errors=[],
            warnings=issues,
            files_checked=len(files),
        )

    @staticmethod
    def build_command(files: List[Path], config: Optional[Dict] = None) -> List[str]:
        """
        Build vulture command with configuration options.

        Args:
            files: List of Python files or directories to analyze
            config: Configuration dict with vulture options

        Returns:
            List of command arguments for subprocess
        """
        if config is None:
            config = {}

        cmd = ["vulture"]

        # Add files/directories to analyze
        cmd.extend(str(f) for f in files)

        # Add min-confidence threshold
        if "min_confidence" in config:
            cmd.extend(["--min-confidence", str(config["min_confidence"])])

        # Add exclude patterns
        if "exclude" in config:
            for pattern in config["exclude"]:
                cmd.extend(["--exclude", pattern])

        # Add ignore-decorators
        if "ignore_decorators" in config:
            for decorator in config["ignore_decorators"]:
                cmd.extend(["--ignore-decorators", decorator])

        # Add ignore-names
        if "ignore_names" in config:
            for name in config["ignore_names"]:
                cmd.extend(["--ignore-names", name])

        # Add make-whitelist flag
        if config.get("make_whitelist"):
            cmd.append("--make-whitelist")

        # Add sort-by-size flag
        if config.get("sort_by_size"):
            cmd.append("--sort-by-size")

        return cmd

    @staticmethod
    def run_vulture(
        files: List[Path],
        config: Optional[Dict] = None,
        timeout: int = 300,
    ) -> str:
        """
        Execute vulture subprocess and return text output.

        Args:
            files: List of files to analyze
            config: Configuration dict
            timeout: Subprocess timeout in seconds

        Returns:
            Text output from vulture

        Raises:
            FileNotFoundError: If vulture is not installed
            subprocess.TimeoutExpired: If execution exceeds timeout
        """
        cmd = VultureParser.build_command(files, config)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,  # Vulture exits with non-zero if it finds unused code
        )

        return result.stdout

    @staticmethod
    def run_and_parse(
        files: List[Path], config: Optional[Dict] = None, timeout: int = 300
    ) -> ValidationResult:
        """
        High-level method to run vulture and parse results.

        Args:
            files: List of files to analyze
            config: Configuration dict
            timeout: Subprocess timeout in seconds

        Returns:
            ValidationResult with parsed findings
        """
        text_output = VultureParser.run_vulture(files, config, timeout)
        return VultureParser.parse_text(text_output, files, config)

    @staticmethod
    def get_version() -> Optional[str]:
        """
        Detect installed vulture version.

        Returns:
            Version string (e.g., "2.7") or None if not installed
        """
        try:
            result = subprocess.run(
                ["vulture", "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )

            # Output format: "vulture 2.7"
            output = result.stdout.strip()
            match = re.search(r"vulture\s+([\d.]+)", output)
            if match:
                return match.group(1)
            return None

        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    @staticmethod
    def find_config_file(directory: Path) -> Optional[Path]:
        """
        Find vulture configuration file in project directory.

        Vulture supports configuration in:
        - pyproject.toml ([tool.vulture])
        - setup.cfg ([vulture])

        Args:
            directory: Project root directory

        Returns:
            Path to config file or None if not found
        """
        # Check pyproject.toml
        pyproject_toml = directory / "pyproject.toml"
        if pyproject_toml.exists():
            content = pyproject_toml.read_text()
            if "[tool.vulture]" in content:
                return pyproject_toml

        # Check setup.cfg
        setup_cfg = directory / "setup.cfg"
        if setup_cfg.exists():
            content = setup_cfg.read_text()
            if "[vulture]" in content:
                return setup_cfg

        return None

    @staticmethod
    def group_by_type(text_output: str) -> Dict[str, List[str]]:
        """
        Group unused items by type (function, class, method, etc.).

        Args:
            text_output: Vulture text output

        Returns:
            Dict mapping type to list of lines
        """
        grouped: Dict[str, List[str]] = {}

        for line in text_output.strip().split("\n"):
            if not line.strip():
                continue

            # Extract type from message
            for item_type in [
                "function",
                "method",
                "class",
                "variable",
                "import",
                "property",
                "attribute",
            ]:
                if f"unused {item_type}" in line:
                    if item_type not in grouped:
                        grouped[item_type] = []
                    grouped[item_type].append(line)
                    break

        return grouped

    @staticmethod
    def count_unused_items(text_output: str) -> int:
        """
        Count total number of unused items.

        Args:
            text_output: Vulture text output

        Returns:
            Total count of unused items
        """
        count = 0
        for line in text_output.strip().split("\n"):
            if line.strip() and "unused" in line:
                count += 1
        return count

    @staticmethod
    def extract_confidence_scores(text_output: str) -> List[int]:
        """
        Extract confidence scores from all findings.

        Args:
            text_output: Vulture text output

        Returns:
            List of confidence percentages
        """
        scores = []
        pattern = r"\((\d+)%\s+confidence\)"

        for line in text_output.strip().split("\n"):
            match = re.search(pattern, line)
            if match:
                scores.append(int(match.group(1)))

        return scores

    @staticmethod
    def calculate_average_confidence(text_output: str) -> float:
        """
        Calculate average confidence score of all findings.

        Args:
            text_output: Vulture text output

        Returns:
            Average confidence percentage (0.0 if no findings)
        """
        scores = VultureParser.extract_confidence_scores(text_output)
        if not scores:
            return 0.0
        return sum(scores) / len(scores)
