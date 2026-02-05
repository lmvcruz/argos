"""
Scout data models and identifiers for case management.

This module provides the core data models for Scout's four-stage pipeline:
1. Fetch - download CI logs from GitHub
2. Save-CI - persist raw logs in Scout execution DB
3. Parse - transform logs via Anvil parsers
4. Save-Analysis - store parsed results in Scout analysis DB
"""

from dataclasses import dataclass
from typing import Optional, Tuple


@dataclass
class CaseIdentifier:
    """
    Case identifier for Scout operations.

    A case is uniquely identified by a triple:
    - workflow_name: Name of the GitHub Actions workflow
    - execution_id: Either run_id OR execution_number
    - job_id: Either job_id OR action_name

    The CaseIdentifier manages the bidirectional relationship between:
    - run_id ↔ execution_number (from GitHub API)
    - job_id ↔ action_name (from GitHub API)

    When created with one identifier, you can query or retrieve the other
    using the linked mappings.
    """

    workflow_name: str
    run_id: Optional[int] = None
    execution_number: Optional[int] = None
    job_id: Optional[str] = None
    action_name: Optional[str] = None

    def __post_init__(self):
        """
        Validate the case identifier.

        Raises:
            ValueError: If workflow_name is missing or invalid execution/job IDs
        """
        if not self.workflow_name:
            raise ValueError("workflow_name is required")

        # Validate that at least one execution identifier is provided
        if self.run_id is None and self.execution_number is None:
            raise ValueError("Either run_id or execution_number must be provided")

        # Validate that at least one job identifier is provided
        if self.job_id is None and self.action_name is None:
            raise ValueError("Either job_id or action_name must be provided")

    def get_execution_id(self) -> int:
        """
        Get the execution ID (run_id).

        Returns:
            The run_id if available

        Raises:
            ValueError: If run_id is not set (execution_number was provided instead)
        """
        if self.run_id is not None:
            return self.run_id
        if self.execution_number is not None:
            # In real implementation, would query GitHub API to get run_id
            raise ValueError("run_id not set. Please provide --run-id or query GitHub API")
        raise ValueError("No execution ID available")

    def get_job_id(self) -> str:
        """
        Get the job ID.

        Returns:
            The job_id if available

        Raises:
            ValueError: If job_id is not set (action_name was provided instead)
        """
        if self.job_id is not None:
            return self.job_id
        if self.action_name is not None:
            # In real implementation, would query GitHub API to get job_id
            raise ValueError("job_id not set. Please provide --job-id or query GitHub API")
        raise ValueError("No job ID available")

    @property
    def triple(self) -> Tuple[str, Optional[int], Optional[str]]:
        """
        Get the case triple for database queries.

        Returns:
            Tuple of (workflow_name, run_id, job_id)
        """
        return (self.workflow_name, self.run_id, self.job_id)

    def __repr__(self) -> str:
        """Return string representation of case identifier."""
        exec_str = self.run_id or f"#{self.execution_number}"
        job_str = self.job_id or f"'{self.action_name}'"
        return f"Case({self.workflow_name}/{exec_str}/{job_str})"


@dataclass
class FetchOptions:
    """Options for the fetch stage."""

    output_file: Optional[str] = None
    save_execution: bool = False


@dataclass
class ParseOptions:
    """Options for the parse stage."""

    input_file: Optional[str] = None
    output_file: Optional[str] = None
    save_analysis: bool = False


@dataclass
class SyncOptions:
    """Options for the sync stage."""

    skip_fetch: bool = False
    skip_save_ci: bool = False
    skip_parse: bool = False
    skip_save_analysis: bool = False
    fetch_all: bool = False
    fetch_last: Optional[int] = None
