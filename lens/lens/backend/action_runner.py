"""
ActionRunner for Lens backend.

Coordinates selective execution actions from Lens UI with Anvil storage.
Manages test execution, coverage analysis, and CI sync operations.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid


class ActionType(str, Enum):
    """Types of actions that can be triggered from Lens UI."""

    RUN_TESTS = "run_tests"
    RUN_COVERAGE = "run_coverage"
    RUN_LINT = "run_lint"
    SYNC_CI = "sync_ci"
    COMPARE_CI_LOCAL = "compare_ci_local"
    GET_FLAKY_TESTS = "get_flaky_tests"
    REPRODUCE_CI_FAILURE = "reproduce_ci_failure"


class ActionStatus(str, Enum):
    """Status of an action during execution."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ActionInput:
    """Input parameters for an action."""

    action_type: ActionType
    project_path: str
    parameters: Dict[str, Any]


@dataclass
class ActionOutput:
    """Output results from an action execution."""

    action_id: str
    action_type: ActionType
    status: ActionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    result: Dict[str, Any]
    error: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = asdict(self)
        result["action_type"] = self.action_type.value
        result["status"] = self.status.value
        result["started_at"] = self.started_at.isoformat()
        result["completed_at"] = (
            self.completed_at.isoformat() if self.completed_at else None
        )
        return result


class ActionRunner:
    """
    Executes actions triggered from Lens UI.

    Coordinates with Anvil storage for test execution tracking and
    provides selective execution capabilities.

    Example:
        >>> runner = ActionRunner()
        >>> output = runner.run_action(
        ...     ActionInput(
        ...         action_type=ActionType.RUN_TESTS,
        ...         project_path="/path/to/project",
        ...         parameters={"test_path": "tests/unit/"}
        ...     )
        ... )
    """

    def __init__(self):
        """Initialize ActionRunner."""
        self.actions: Dict[str, ActionOutput] = {}
        self.anvil_db = None  # Will be injected by Lens backend

    def run_action(self, action_input: ActionInput) -> ActionOutput:
        """
        Execute an action.

        Determines action type and delegates to appropriate handler.

        Args:
            action_input: Input parameters for the action

        Returns:
            ActionOutput with execution results

        Raises:
            ValueError: If action type is unsupported
        """
        action_id = str(uuid.uuid4())
        action_output = ActionOutput(
            action_id=action_id,
            action_type=action_input.action_type,
            status=ActionStatus.QUEUED,
            started_at=datetime.now(),
            completed_at=None,
            result={},
        )

        self.actions[action_id] = action_output

        try:
            action_output.status = ActionStatus.RUNNING
            action_output.started_at = datetime.now()

            if action_input.action_type == ActionType.RUN_TESTS:
                result = self._run_tests(
                    action_input.project_path, action_input.parameters
                )
            elif action_input.action_type == ActionType.RUN_COVERAGE:
                result = self._run_coverage(
                    action_input.project_path, action_input.parameters
                )
            elif action_input.action_type == ActionType.RUN_LINT:
                result = self._run_lint(
                    action_input.project_path, action_input.parameters
                )
            elif action_input.action_type == ActionType.SYNC_CI:
                result = self._sync_ci(
                    action_input.project_path, action_input.parameters
                )
            elif action_input.action_type == ActionType.COMPARE_CI_LOCAL:
                result = self._compare_ci_local(
                    action_input.project_path, action_input.parameters
                )
            elif action_input.action_type == ActionType.GET_FLAKY_TESTS:
                result = self._get_flaky_tests(action_input.parameters)
            elif action_input.action_type == ActionType.REPRODUCE_CI_FAILURE:
                result = self._reproduce_ci_failure(
                    action_input.project_path, action_input.parameters
                )
            else:
                raise ValueError(
                    f"Unsupported action type: {action_input.action_type}")

            action_output.result = result
            action_output.status = ActionStatus.COMPLETED
            action_output.completed_at = datetime.now()

        except Exception as e:
            action_output.status = ActionStatus.FAILED
            action_output.error = str(e)
            action_output.completed_at = datetime.now()

        return action_output

    def get_action_status(self, action_id: str) -> Optional[ActionOutput]:
        """
        Get status of a running or completed action.

        Args:
            action_id: ID of the action to check

        Returns:
            ActionOutput if found, None otherwise
        """
        return self.actions.get(action_id)

    def _run_tests(self, project_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run tests in specified project.

        Args:
            project_path: Path to project
            parameters: Test parameters (test_path, filters, etc.)

        Returns:
            Dictionary with test results
        """
        test_path = parameters.get("test_path", "tests/")
        filters = parameters.get("filters", [])

        return {
            "test_path": test_path,
            "filters": filters,
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "execution_time": 0.0,
            "message": f"Would run tests in {project_path}/{test_path}",
        }

    def _run_coverage(
        self, project_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run coverage analysis on project.

        Args:
            project_path: Path to project
            parameters: Coverage parameters

        Returns:
            Dictionary with coverage results
        """
        coverage_threshold = parameters.get("threshold", 80)

        return {
            "coverage_threshold": coverage_threshold,
            "total_coverage": 0.0,
            "files_below_threshold": [],
            "message": f"Would run coverage analysis in {project_path}",
        }

    def _run_lint(self, project_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run linting checks on project.

        Args:
            project_path: Path to project
            parameters: Lint parameters (tools, filters, etc.)

        Returns:
            Dictionary with linting results
        """
        tools = parameters.get("tools", ["flake8", "black", "isort"])

        return {
            "tools": tools,
            "total_issues": 0,
            "critical": 0,
            "warning": 0,
            "info": 0,
            "message": f"Would run linters: {', '.join(tools)}",
        }

    def _sync_ci(self, project_path: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sync CI logs and results from GitHub Actions.

        Args:
            project_path: Path to project
            parameters: Sync parameters (workflow, limit, force, etc.)

        Returns:
            Dictionary with sync results
        """
        workflow = parameters.get("workflow")
        limit = parameters.get("limit", 10)
        force_download = parameters.get("force_download", False)
        force_parse = parameters.get("force_parse", False)

        return {
            "workflow": workflow,
            "limit": limit,
            "force_download": force_download,
            "force_parse": force_parse,
            "downloaded": 0,
            "skipped": 0,
            "parsed": 0,
            "message": f"Would sync CI logs for {workflow or 'all workflows'}",
        }

    def _compare_ci_local(
        self, project_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare CI execution results with local results.

        Args:
            project_path: Path to project
            parameters: Comparison parameters

        Returns:
            Dictionary with comparison analysis
        """
        entity_type = parameters.get("entity_type", "test")
        entity_id = parameters.get("entity_id")

        return {
            "entity_type": entity_type,
            "entity_id": entity_id,
            "local_status": None,
            "ci_status": None,
            "platform_specific": False,
            "platforms_failed": [],
            "message": f"Would compare {entity_type} results for CI vs local",
        }

    def _get_flaky_tests(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get flaky test detection results.

        Args:
            parameters: Detection parameters (threshold, lookback, etc.)

        Returns:
            Dictionary with flaky test analysis
        """
        threshold = parameters.get("threshold", 3)
        lookback_runs = parameters.get("lookback_runs", 10)

        return {
            "threshold": threshold,
            "lookback_runs": lookback_runs,
            "flaky_tests": [],
            "total_flaky": 0,
            "message": f"Would analyze flaky tests (threshold={threshold})",
        }

    def _reproduce_ci_failure(
        self, project_path: str, parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate reproduction script for CI-specific failure.

        Args:
            project_path: Path to project
            parameters: Failure parameters (test_id, platform, python_version, etc.)

        Returns:
            Dictionary with reproduction information
        """
        test_id = parameters.get("test_id")
        platform = parameters.get("platform", "linux")
        python_version = parameters.get("python_version", "3.11")

        return {
            "test_id": test_id,
            "platform": platform,
            "python_version": python_version,
            "reproduction_steps": [],
            "docker_command": (
                f"docker run -it python:{python_version} "
                f"bash -c 'pip install -e . && pytest {test_id}'"
            ),
            "message": f"Would generate reproduction for {test_id}",
        }

    def cancel_action(self, action_id: str) -> bool:
        """
        Cancel a running action.

        Args:
            action_id: ID of action to cancel

        Returns:
            True if cancelled successfully, False otherwise
        """
        action = self.actions.get(action_id)
        if action and action.status in (ActionStatus.QUEUED, ActionStatus.RUNNING):
            action.status = ActionStatus.CANCELLED
            action.completed_at = datetime.now()
            return True
        return False
