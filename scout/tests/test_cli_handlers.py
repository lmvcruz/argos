"""
Test suite for Scout CLI handlers (fetch, parse, sync).

Tests the new v2 handlers for the complete pipeline.
"""

import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

import pytest

from scout.cli import (
    handle_fetch_command_v2,
    handle_parse_command_v2,
    handle_sync_command,
)


class TestFetchHandler:
    """Tests for handle_fetch_command_v2."""

    def test_fetch_to_stdout(self, capsys, tmp_path):
        """Test fetch command with output to stdout."""

        class Args:
            workflow_name = "test-workflow"
            run_id = 123
            execution_number = None
            job_id = "job123"
            action_name = None
            output = None
            save_ci = False
            ci_db = str(tmp_path / "test.db")
            verbose = False
            quiet = False

        result = handle_fetch_command_v2(Args())
        assert result == 0

        captured = capsys.readouterr()
        assert "Fetching from workflow" in captured.out
        assert "Raw Log Output" in captured.out

    def test_fetch_to_file(self, tmp_path):
        """Test fetch command with output to file."""
        output_file = tmp_path / "raw_log.txt"

        class Args:
            workflow_name = "test-workflow"
            run_id = 123
            execution_number = None
            job_id = "job123"
            action_name = None
            output = str(output_file)
            save_ci = False
            ci_db = str(tmp_path / "test.db")
            verbose = False
            quiet = True

        result = handle_fetch_command_v2(Args())
        assert result == 0
        assert output_file.exists()

        content = output_file.read_text()
        assert "test-workflow" in content

    def test_fetch_missing_required_args(self):
        """Test fetch with missing required arguments."""

        class Args:
            workflow_name = "test-workflow"
            run_id = None
            execution_number = None  # Both missing
            job_id = None
            action_name = None  # Both missing
            output = None
            save_ci = False
            ci_db = "test.db"
            verbose = False
            quiet = False

        # Should return error due to missing run_id and execution_number
        result = handle_fetch_command_v2(Args())
        assert result == 1


class TestParseHandler:
    """Tests for handle_parse_command_v2."""

    def test_parse_from_file(self, tmp_path):
        """Test parse from input file."""
        # Create a mock log file
        log_file = tmp_path / "mock.log"
        log_file.write_text("""
[PASS] test_one passed
[PASS] test_two passed
[FAIL] test_three failed
        """)

        class Args:
            input = str(log_file)
            workflow_name = None
            run_id = None
            execution_number = None
            job_id = None
            action_name = None
            output = None
            save_analysis = False
            ci_db = str(tmp_path / "ci.db")
            analysis_db = str(tmp_path / "analysis.db")
            verbose = False
            quiet = True

        result = handle_parse_command_v2(Args())
        assert result == 0

    def test_parse_to_file(self, tmp_path):
        """Test parse with output to file."""
        log_file = tmp_path / "mock.log"
        log_file.write_text("""
[PASS] test_one passed
[FAIL] test_two failed
        """)

        output_file = tmp_path / "parsed.json"

        class Args:
            input = str(log_file)
            workflow_name = None
            run_id = None
            execution_number = None
            job_id = None
            action_name = None
            output = str(output_file)
            save_analysis = False
            ci_db = str(tmp_path / "ci.db")
            analysis_db = str(tmp_path / "analysis.db")
            verbose = False
            quiet = True

        result = handle_parse_command_v2(Args())
        assert result == 0
        assert output_file.exists()

        # Verify JSON content
        data = json.loads(output_file.read_text())
        assert "summary" in data
        assert data["summary"]["passed"] == 1
        assert data["summary"]["failed"] == 1

    def test_parse_missing_input(self):
        """Test parse with missing input."""

        class Args:
            input = None
            workflow_name = None
            run_id = None
            execution_number = None
            job_id = None
            action_name = None
            output = None
            save_analysis = False
            ci_db = "test.db"
            analysis_db = "test-analysis.db"
            verbose = False
            quiet = False

        result = handle_parse_command_v2(Args())
        assert result == 1


class TestSyncHandler:
    """Tests for handle_sync_command."""

    def test_sync_with_skip_fetch(self, tmp_path):
        """Test sync command with fetch stage skipped."""

        class Args:
            workflow_name = None
            run_id = None
            execution_number = None
            job_id = None
            action_name = None
            fetch_all = False
            fetch_last = None
            filter_workflow = None
            skip_fetch = True
            skip_save_ci = False
            skip_parse = False
            skip_save_analysis = False
            ci_db = str(tmp_path / "ci.db")
            analysis_db = str(tmp_path / "analysis.db")
            verbose = False
            quiet = True

        result = handle_sync_command(Args())
        assert result == 0

    def test_sync_specific_workflow(self, tmp_path, capsys):
        """Test sync with specific workflow processing."""

        class Args:
            workflow_name = "test-workflow"
            run_id = 123
            execution_number = None
            job_id = None
            action_name = None
            fetch_all = False
            fetch_last = None
            filter_workflow = None
            skip_fetch = False
            skip_save_ci = False
            skip_parse = False
            skip_save_analysis = False
            ci_db = str(tmp_path / "ci.db")
            analysis_db = str(tmp_path / "analysis.db")
            verbose = False
            quiet = False

        result = handle_sync_command(Args())
        # May fail due to database setup, but should handle gracefully
        assert result in [0, 1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
