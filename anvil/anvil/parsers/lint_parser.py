"""
Parser for code quality and linting tool outputs.

This module provides parsers for flake8, black, isort, and other code quality tools,
converting their output into structured LintViolation records for database storage.
"""

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class FileViolations:
    """
    Violations for a single file.

    Args:
        file_path: Path to the file with violations
        violations: List of violation dictionaries
        validator: Validator that found the violations
    """

    file_path: str
    violations: List[Dict]
    validator: str


@dataclass
class LintData:
    """
    Aggregated lint scan data.

    Args:
        validator: Validator that was run (flake8, black, isort, etc.)
        total_violations: Total number of violations found
        files_scanned: Number of files scanned
        errors: Number of ERROR severity violations
        warnings: Number of WARNING severity violations
        info: Number of INFO severity violations
        by_code: Dictionary mapping violation codes to counts
        file_violations: List of FileViolations instances
    """

    validator: str
    total_violations: int
    files_scanned: int
    errors: int
    warnings: int
    info: int
    by_code: Dict[str, int]
    file_violations: List[FileViolations]


class LintParser:
    """
    Parser for various code quality and linting tool outputs.

    Supports parsing output from:
    - flake8 (PEP8 linting)
    - black (code formatting)
    - isort (import sorting)
    - pylint (advanced linting)
    """

    # Severity mapping for flake8 codes
    FLAKE8_SEVERITY_MAP = {
        "E": "ERROR",  # PEP8 errors
        "W": "WARNING",  # PEP8 warnings
        "F": "ERROR",  # PyFlakes errors
        "C": "WARNING",  # McCabe complexity warnings
        "N": "WARNING",  # PEP8 naming conventions
        "D": "INFO",  # Docstring conventions
        "I": "INFO",  # Import order
        "B": "WARNING",  # Bugbear warnings
        "S": "WARNING",  # Security warnings
        "T": "INFO",  # Type checking
    }

    def parse_flake8_output(self, output: str, project_root: Optional[Path] = None) -> LintData:
        """
        Parse flake8 output into structured violation data.

        Args:
            output: Raw flake8 output text
            project_root: Project root path for making paths relative (optional)

        Returns:
            LintData instance with parsed violations

        Examples:
            >>> parser = LintParser()
            >>> output = "file.py:10:5: E501 line too long (105 > 100 characters)"
            >>> data = parser.parse_flake8_output(output)
            >>> data.total_violations
            1
        """
        violations_by_file: Dict[str, List[Dict]] = {}
        by_code: Dict[str, int] = {}
        errors = 0
        warnings = 0
        info = 0

        # Flake8 format: path/to/file.py:line:col: CODE message
        pattern = r"^(.+?):(\d+):(\d+):\s+([A-Z]\d+)\s+(.+)$"

        for line in output.strip().split("\n"):
            if not line.strip():
                continue

            match = re.match(pattern, line)
            if not match:
                continue

            file_path, line_num, col_num, code, message = match.groups()

            # Make path relative if project_root provided
            if project_root:
                try:
                    file_path = str(Path(file_path).relative_to(project_root))
                except ValueError:
                    # Path is not relative to project_root, keep as-is
                    pass

            # Determine severity from code prefix
            code_prefix = code[0]
            severity = self.FLAKE8_SEVERITY_MAP.get(code_prefix, "WARNING")

            # Count by severity
            if severity == "ERROR":
                errors += 1
            elif severity == "WARNING":
                warnings += 1
            else:
                info += 1

            # Count by code
            by_code[code] = by_code.get(code, 0) + 1

            # Create violation record
            violation = {
                "line_number": int(line_num),
                "column_number": int(col_num),
                "severity": severity,
                "code": code,
                "message": message.strip(),
            }

            # Group by file
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)

        # Create FileViolations instances
        file_violations = [
            FileViolations(file_path=path, violations=viols, validator="flake8")
            for path, viols in violations_by_file.items()
        ]

        return LintData(
            validator="flake8",
            total_violations=sum(by_code.values()),
            files_scanned=len(violations_by_file),
            errors=errors,
            warnings=warnings,
            info=info,
            by_code=by_code,
            file_violations=file_violations,
        )

    def parse_black_output(self, output: str, project_root: Optional[Path] = None) -> LintData:
        """
        Parse black --check output (with --diff) into structured violation data.

        Extracts file paths and line numbers from the unified diff format.
        Black violations always have code BLACK001 (formatting issue), so we omit
        redundant severity and code fields.

        Args:
            output: Raw black output text with unified diff format
            project_root: Project root path for making paths relative (optional)

        Returns:
            LintData instance with parsed violations
        """
        violations_by_file: Dict[str, List[Dict]] = {}
        by_code = {"BLACK001": 0}

        # Patterns:
        # Hunk header: @@ -start,count +start,count @@ or @@ -start +start @@
        hunk_pattern = r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@"
        # Black format: "would reformat path/to/file.py"
        reformat_pattern = r"would reformat (.+)"

        current_hunk_line_number = None
        lines = output.strip().split("\n")
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check for hunk header to capture starting line number
            hunk_match = re.match(hunk_pattern, line)
            if hunk_match:
                current_hunk_line_number = int(hunk_match.group(1))
                i += 1
                continue

            # Look for "would reformat" message
            match = re.search(reformat_pattern, line)
            if not match:
                i += 1
                continue

            file_path = match.group(1).strip()

            # Make path relative if project_root provided
            if project_root:
                try:
                    file_path = str(Path(file_path).relative_to(project_root))
                except ValueError:
                    pass

            # The violation occurs at the start of the hunk we're in
            # If no hunk found yet, default to 1
            line_number = current_hunk_line_number if current_hunk_line_number else 1

            # Minimal violation dict - severity and code are always BLACK001
            violation = {
                "line_number": line_number,
            }

            by_code["BLACK001"] += 1

            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)

            i += 1

        file_violations = [
            FileViolations(file_path=path, violations=viols, validator="black")
            for path, viols in violations_by_file.items()
        ]

        return LintData(
            validator="black",
            total_violations=by_code["BLACK001"],
            files_scanned=len(violations_by_file),
            errors=0,
            warnings=by_code["BLACK001"],
            info=0,
            by_code=by_code,
            file_violations=file_violations,
        )

    def parse_isort_output(self, output: str, project_root: Optional[Path] = None) -> LintData:
        """
        Parse isort --check-only output into structured violation data.

        Args:
            output: Raw isort output text
            project_root: Project root path for making paths relative (optional)

        Returns:
            LintData instance with parsed violations

        Examples:
            >>> parser = LintParser()
            >>> output = "ERROR: file.py Imports are incorrectly sorted"
            >>> data = parser.parse_isort_output(output)
            >>> data.total_violations
            1
        """
        violations_by_file: Dict[str, List[Dict]] = {}
        by_code = {"ISORT001": 0}  # Import sorting violation

        # isort format: "ERROR: path/to/file.py Imports are incorrectly sorted"
        pattern = r"ERROR:\s+(.+?)\s+(.+)"

        for line in output.strip().split("\n"):
            if not line.strip() or not line.startswith("ERROR:"):
                continue

            match = re.match(pattern, line)
            if not match:
                continue

            file_path, message = match.groups()

            # Make path relative if project_root provided
            if project_root:
                try:
                    file_path = str(Path(file_path).relative_to(project_root))
                except ValueError:
                    pass

            violation = {
                "line_number": 1,
                "column_number": None,
                "severity": "WARNING",
                "code": "ISORT001",
                "message": message.strip(),
            }

            by_code["ISORT001"] += 1

            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)

        file_violations = [
            FileViolations(file_path=path, violations=viols, validator="isort")
            for path, viols in violations_by_file.items()
        ]

        return LintData(
            validator="isort",
            total_violations=by_code["ISORT001"],
            files_scanned=len(violations_by_file),
            errors=0,
            warnings=by_code["ISORT001"],
            info=0,
            by_code=by_code,
            file_violations=file_violations,
        )

    def calculate_quality_score(self, violations_count: int, total_lines: int) -> float:
        """
        Calculate code quality score (0-100) based on violations per line.

        Args:
            violations_count: Number of violations
            total_lines: Total lines of code

        Returns:
            Quality score from 0 (worst) to 100 (perfect)

        Examples:
            >>> parser = LintParser()
            >>> parser.calculate_quality_score(0, 100)
            100.0
            >>> parser.calculate_quality_score(50, 100)
            50.0
        """
        if total_lines == 0:
            return 100.0

        violations_per_line = violations_count / total_lines
        # Score decreases by 100 points per violation per line
        # Capped at 0 minimum
        score = max(0.0, 100.0 - (violations_per_line * 100))
        return round(score, 2)

    def aggregate_by_severity(self, violations: List[Dict]) -> Dict[str, int]:
        """
        Aggregate violations by severity.

        Args:
            violations: List of violation dictionaries

        Returns:
            Dictionary mapping severity to count

        Examples:
            >>> parser = LintParser()
            >>> viols = [{"severity": "ERROR"}, {"severity": "WARNING"}, {"severity": "ERROR"}]
            >>> parser.aggregate_by_severity(viols)
            {'ERROR': 2, 'WARNING': 1}
        """
        counter = Counter(v["severity"] for v in violations)
        return dict(counter)

    def find_most_common_violation(self, violations: List[Dict]) -> Optional[str]:
        """
        Find the most common violation code.

        Args:
            violations: List of violation dictionaries

        Returns:
            Most common violation code or None if no violations

        Examples:
            >>> parser = LintParser()
            >>> viols = [{"code": "E501"}, {"code": "W503"}, {"code": "E501"}]
            >>> parser.find_most_common_violation(viols)
            'E501'
        """
        if not violations:
            return None

        counter = Counter(v["code"] for v in violations)
        most_common = counter.most_common(1)
        return most_common[0][0] if most_common else None

    def filter_by_severity(self, violations: List[Dict], severity: str) -> List[Dict]:
        """
        Filter violations by severity.

        Args:
            violations: List of violation dictionaries
            severity: Severity to filter for (ERROR, WARNING, INFO)

        Returns:
            Filtered list of violations

        Examples:
            >>> parser = LintParser()
            >>> viols = [
            ...     {"severity": "ERROR", "code": "E501"},
            ...     {"severity": "WARNING", "code": "W503"}
            ... ]
            >>> errors = parser.filter_by_severity(viols, "ERROR")
            >>> len(errors)
            1
        """
        return [v for v in violations if v["severity"] == severity]
