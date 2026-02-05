"""
Tests for Scout validation utilities.

Tests argument validation for fetch, parse, and sync commands.
"""

from unittest.mock import MagicMock

from scout.validation import (
    validate_fetch_args,
    validate_parse_args,
    validate_sync_args,
)


class TestValidateFetchArgs:
    """Test validate_fetch_args function."""

    def test_fetch_all_flag_valid(self):
        """Test fetch with --fetch-all flag."""
        args = MagicMock(
            fetch_all=True,
            fetch_last=None,
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
        )
        assert validate_fetch_args(args) == ""

    def test_fetch_last_flag_valid(self):
        """Test fetch with --fetch-last N flag."""
        args = MagicMock(
            fetch_all=False,
            fetch_last=5,
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
        )
        assert validate_fetch_args(args) == ""

    def test_workflow_with_run_id_and_job_id_valid(self):
        """Test fetch with --workflow-name and required identifiers."""
        args = MagicMock(
            fetch_all=False,
            fetch_last=None,
            workflow_name="test-workflow",
            run_id=123,
            execution_number=None,
            job_id="job1",
            action_name=None,
        )
        assert validate_fetch_args(args) == ""

    def test_workflow_with_execution_number_and_action_name_valid(self):
        """Test fetch with --workflow-name and alternative identifiers."""
        args = MagicMock(
            fetch_all=False,
            fetch_last=None,
            workflow_name="test-workflow",
            run_id=None,
            execution_number=5,
            job_id=None,
            action_name="action1",
        )
        assert validate_fetch_args(args) == ""

    def test_no_mode_specified_invalid(self):
        """Test fetch with no fetch mode specified."""
        args = MagicMock(
            fetch_all=False,
            fetch_last=None,
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
        )
        error = validate_fetch_args(args)
        assert "Error" in error
        assert "--fetch-all" in error or "--fetch-last" in error

    def test_workflow_without_execution_id_invalid(self):
        """Test fetch with --workflow-name but no execution ID."""
        args = MagicMock(
            fetch_all=False,
            fetch_last=None,
            workflow_name="test-workflow",
            run_id=None,
            execution_number=None,
            job_id="job1",
            action_name=None,
        )
        error = validate_fetch_args(args)
        assert "Error" in error
        assert "--run-id" in error or "--execution-number" in error

    def test_workflow_without_job_id_invalid(self):
        """Test fetch with --workflow-name but no job ID."""
        args = MagicMock(
            fetch_all=False,
            fetch_last=None,
            workflow_name="test-workflow",
            run_id=123,
            execution_number=None,
            job_id=None,
            action_name=None,
        )
        error = validate_fetch_args(args)
        assert "Error" in error
        assert "--job-id" in error or "--action-name" in error

    def test_fetch_last_with_workflow_name_valid(self):
        """Test fetch with both --fetch-last and --workflow-name."""
        args = MagicMock(
            fetch_all=False,
            fetch_last=3,
            workflow_name="test-workflow",
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
        )
        assert validate_fetch_args(args) == ""

    def test_fetch_all_with_workflow_name_valid(self):
        """Test fetch with both --fetch-all and --workflow-name."""
        args = MagicMock(
            fetch_all=True,
            fetch_last=None,
            workflow_name="test-workflow",
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
        )
        assert validate_fetch_args(args) == ""


class TestValidateParseArgs:
    """Test validate_parse_args function."""

    def test_input_file_valid(self):
        """Test parse with --input file."""
        args = MagicMock(
            input="results.json",
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
        )
        assert validate_parse_args(args) == ""

    def test_workflow_with_run_id_and_job_id_valid(self):
        """Test parse with --workflow-name and required identifiers."""
        args = MagicMock(
            input=None,
            workflow_name="test-workflow",
            run_id=123,
            execution_number=None,
            job_id="job1",
            action_name=None,
        )
        assert validate_parse_args(args) == ""

    def test_workflow_with_execution_number_and_action_name_valid(self):
        """Test parse with --workflow-name and alternative identifiers."""
        args = MagicMock(
            input=None,
            workflow_name="test-workflow",
            run_id=None,
            execution_number=5,
            job_id=None,
            action_name="action1",
        )
        assert validate_parse_args(args) == ""

    def test_no_input_no_workflow_invalid(self):
        """Test parse with neither --input nor --workflow-name."""
        args = MagicMock(
            input=None,
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
        )
        error = validate_parse_args(args)
        assert "Error" in error
        assert "--input" in error or "--workflow-name" in error

    def test_workflow_without_execution_id_invalid(self):
        """Test parse with --workflow-name but no execution ID."""
        args = MagicMock(
            input=None,
            workflow_name="test-workflow",
            run_id=None,
            execution_number=None,
            job_id="job1",
            action_name=None,
        )
        error = validate_parse_args(args)
        assert "Error" in error
        assert "--run-id" in error or "--execution-number" in error

    def test_workflow_without_job_id_invalid(self):
        """Test parse with --workflow-name but no job ID."""
        args = MagicMock(
            input=None,
            workflow_name="test-workflow",
            run_id=123,
            execution_number=None,
            job_id=None,
            action_name=None,
        )
        error = validate_parse_args(args)
        assert "Error" in error
        assert "--job-id" in error or "--action-name" in error

    def test_input_and_workflow_both_provided_valid(self):
        """Test parse with both --input and --workflow-name."""
        args = MagicMock(
            input="results.json",
            workflow_name="test-workflow",
            run_id=123,
            execution_number=None,
            job_id="job1",
            action_name=None,
        )
        assert validate_parse_args(args) == ""


class TestValidateSyncArgs:
    """Test validate_sync_args function."""

    def test_fetch_all_flag_valid(self):
        """Test sync with --fetch-all flag."""
        args = MagicMock(
            fetch_all=True,
            fetch_last=None,
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
            skip_fetch=False,
            skip_save_ci=False,
            skip_parse=False,
            skip_save_analysis=False,
        )
        assert validate_sync_args(args) == ""

    def test_fetch_last_flag_valid(self):
        """Test sync with --fetch-last N flag."""
        args = MagicMock(
            fetch_all=False,
            fetch_last=5,
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
            skip_fetch=False,
            skip_save_ci=False,
            skip_parse=False,
            skip_save_analysis=False,
        )
        assert validate_sync_args(args) == ""

    def test_workflow_with_run_id_and_job_id_valid(self):
        """Test sync with --workflow-name and required identifiers."""
        args = MagicMock(
            fetch_all=False,
            fetch_last=None,
            workflow_name="test-workflow",
            run_id=123,
            execution_number=None,
            job_id="job1",
            action_name=None,
            skip_fetch=False,
            skip_save_ci=False,
            skip_parse=False,
            skip_save_analysis=False,
        )
        assert validate_sync_args(args) == ""

    def test_no_mode_specified_invalid(self):
        """Test sync with no sync mode specified."""
        args = MagicMock(
            fetch_all=False,
            fetch_last=None,
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
            skip_fetch=False,
            skip_save_ci=False,
            skip_parse=False,
            skip_save_analysis=False,
        )
        error = validate_sync_args(args)
        assert "Error" in error
        assert "--fetch-all" in error or "--fetch-last" in error

    def test_skip_all_stages_invalid(self):
        """Test sync with all stages skipped."""
        args = MagicMock(
            fetch_all=True,
            fetch_last=None,
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
            skip_fetch=True,
            skip_save_ci=True,
            skip_parse=True,
            skip_save_analysis=True,
        )
        error = validate_sync_args(args)
        assert "Error" in error
        assert "skip" in error.lower()

    def test_skip_some_stages_valid(self):
        """Test sync with some (but not all) stages skipped."""
        args = MagicMock(
            fetch_all=True,
            fetch_last=None,
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
            skip_fetch=True,
            skip_save_ci=False,
            skip_parse=False,
            skip_save_analysis=False,
        )
        assert validate_sync_args(args) == ""

    def test_skip_three_stages_valid(self):
        """Test sync with three stages skipped (one remaining)."""
        args = MagicMock(
            fetch_all=True,
            fetch_last=None,
            workflow_name=None,
            run_id=None,
            execution_number=None,
            job_id=None,
            action_name=None,
            skip_fetch=False,
            skip_save_ci=True,
            skip_parse=True,
            skip_save_analysis=True,
        )
        assert validate_sync_args(args) == ""
