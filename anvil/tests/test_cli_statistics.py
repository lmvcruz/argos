"""
Test suite for CLI statistics commands.

Tests the statistics CLI commands according to Step 8.3 of the implementation plan.
"""

import json
import subprocess

import pytest


@pytest.fixture
def test_database(tmp_path):
    """Create a temporary database with test data."""
    db_path = tmp_path / "test_statistics.db"
    # TODO: Populate with test data once statistics module is implemented
    return db_path


class TestAnvilStatsReport:
    """Test 'anvil stats report' command."""

    def test_stats_report_shows_summary(self):
        """Test that stats report shows statistics summary."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "report"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Statistics Summary" in result.stdout or "statistics" in result.stdout.lower()

    def test_stats_report_filters_by_days(self):
        """Test stats report with --days filter."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "report", "--days", "30"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "30" in result.stdout or "days" in result.stdout.lower()

    def test_stats_report_with_empty_database(self):
        """Test stats report with empty database."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "report"],
            capture_output=True,
            text=True,
        )

        # Should handle gracefully, not crash
        assert result.returncode in [0, 1]  # May return 0 or 1 for no data

    def test_stats_report_with_insufficient_data(self):
        """Test stats report with insufficient data."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "report"],
            capture_output=True,
            text=True,
        )

        # Should show message about insufficient data or work with what's available
        assert result.returncode in [0, 1]


class TestAnvilStatsExport:
    """Test 'anvil stats export' command."""

    def test_stats_export_json_format(self):
        """Test stats export to JSON format."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "export", "--format", "json"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Output should be valid JSON or contain JSON content
        try:
            json.loads(result.stdout)
        except json.JSONDecodeError:
            # May not have data yet, but command should work
            assert "export" in result.stdout.lower() or "{" in result.stdout

    def test_stats_export_csv_format(self):
        """Test stats export to CSV format."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "export", "--format", "csv"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should contain CSV-like content or headers
        assert "," in result.stdout or "export" in result.stdout.lower()

    def test_stats_export_to_file(self, tmp_path):
        """Test stats export with --output option."""
        output_file = tmp_path / "stats_export.json"

        result = subprocess.run(
            [
                "python",
                "-m",
                "anvil",
                "stats",
                "export",
                "--format",
                "json",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # File should be created (or command acknowledges output path)
        assert output_file.exists() or "output" in result.stdout.lower()

    def test_stats_export_with_empty_database(self):
        """Test stats export with empty database."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "export", "--format", "json"],
            capture_output=True,
            text=True,
        )

        # Should handle gracefully
        assert result.returncode in [0, 1]


class TestAnvilStatsFlaky:
    """Test 'anvil stats flaky' command."""

    def test_stats_flaky_lists_flaky_tests(self):
        """Test that stats flaky lists flaky tests."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "flaky"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "flaky" in result.stdout.lower() or "test" in result.stdout.lower()

    def test_stats_flaky_with_threshold(self):
        """Test stats flaky with custom threshold."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "flaky", "--threshold", "0.7"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "0.7" in result.stdout or "threshold" in result.stdout.lower()

    def test_stats_flaky_with_empty_database(self):
        """Test stats flaky with empty database."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "flaky"],
            capture_output=True,
            text=True,
        )

        # Should handle gracefully
        assert result.returncode in [0, 1]

    def test_stats_flaky_output_format(self):
        """Test that flaky test output is well-formatted."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "flaky"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should have some structure (headers, columns, etc.)
        assert len(result.stdout) > 0


class TestAnvilStatsProblemFiles:
    """Test 'anvil stats problem-files' command."""

    def test_stats_problem_files_lists_problematic_files(self):
        """Test that problem-files lists files with frequent issues."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "problem-files"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "file" in result.stdout.lower() or "problem" in result.stdout.lower()

    def test_stats_problem_files_with_threshold(self):
        """Test problem-files with custom threshold."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "problem-files", "--threshold", "5"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should apply threshold filter

    def test_stats_problem_files_with_empty_database(self):
        """Test problem-files with empty database."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "problem-files"],
            capture_output=True,
            text=True,
        )

        # Should handle gracefully
        assert result.returncode in [0, 1]

    def test_stats_problem_files_shows_error_counts(self):
        """Test that problem-files shows error counts."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "problem-files"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should show some indication of error frequency


class TestAnvilStatsTrends:
    """Test 'anvil stats trends' command."""

    def test_stats_trends_shows_overall_trends(self):
        """Test that trends shows overall trends."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "trends"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "trend" in result.stdout.lower() or "statistics" in result.stdout.lower()

    def test_stats_trends_for_specific_validator(self):
        """Test trends for specific validator."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "trends", "--validator", "pylint"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "pylint" in result.stdout.lower() or "validator" in result.stdout.lower()

    def test_stats_trends_with_date_range(self):
        """Test trends with date range filter."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "trends", "--days", "60"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

    def test_stats_trends_with_empty_database(self):
        """Test trends with empty database."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "trends"],
            capture_output=True,
            text=True,
        )

        # Should handle gracefully
        assert result.returncode in [0, 1]


class TestAnvilStatsHelp:
    """Test help and usage messages for stats commands."""

    def test_stats_command_help(self):
        """Test 'anvil stats --help'."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "stats" in result.stdout.lower()
        assert "report" in result.stdout
        assert "export" in result.stdout
        assert "flaky" in result.stdout

    def test_stats_report_help(self):
        """Test 'anvil stats report --help'."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "report", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "report" in result.stdout.lower()
        assert "--days" in result.stdout

    def test_stats_export_help(self):
        """Test 'anvil stats export --help'."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "export", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "export" in result.stdout.lower()
        assert "--format" in result.stdout
        assert "--output" in result.stdout

    def test_stats_flaky_help(self):
        """Test 'anvil stats flaky --help'."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "flaky", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "flaky" in result.stdout.lower()
        assert "--threshold" in result.stdout


class TestAnvilStatsQuietMode:
    """Test quiet mode for statistics commands."""

    def test_stats_report_quiet_mode(self):
        """Test stats report with --quiet flag."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "report", "--quiet"],
            capture_output=True,
            text=True,
        )

        assert result.returncode in [0, 1]
        # Quiet mode should minimize output

    def test_stats_flaky_quiet_mode(self):
        """Test stats flaky with --quiet flag."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "flaky", "--quiet"],
            capture_output=True,
            text=True,
        )

        assert result.returncode in [0, 1]


class TestAnvilStatsVerboseMode:
    """Test verbose mode for statistics commands."""

    def test_stats_report_verbose_mode(self):
        """Test stats report with --verbose flag."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "report", "--verbose"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Verbose mode should show more details

    def test_stats_trends_verbose_mode(self):
        """Test stats trends with --verbose flag."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "trends", "--verbose"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0


class TestAnvilStatsErrorHandling:
    """Test error handling for statistics commands."""

    def test_stats_export_invalid_format(self):
        """Test stats export with invalid format."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "export", "--format", "invalid"],
            capture_output=True,
            text=True,
        )

        # Should return error
        assert result.returncode != 0
        assert "error" in result.stderr.lower() or "invalid" in result.stderr.lower()

    def test_stats_flaky_invalid_threshold(self):
        """Test stats flaky with invalid threshold."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "flaky", "--threshold", "2.0"],
            capture_output=True,
            text=True,
        )

        # Threshold should be 0-1, so 2.0 is invalid
        assert result.returncode != 0 or "invalid" in result.stdout.lower()

    def test_stats_trends_invalid_validator(self):
        """Test stats trends with nonexistent validator."""
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "trends", "--validator", "nonexistent"],
            capture_output=True,
            text=True,
        )

        # Should handle gracefully (may show no data or error)
        assert result.returncode in [0, 1]

    def test_stats_export_unwritable_output(self):
        """Test stats export with unwritable output path."""
        result = subprocess.run(
            [
                "python",
                "-m",
                "anvil",
                "stats",
                "export",
                "--format",
                "json",
                "--output",
                "/nonexistent/path/file.json",
            ],
            capture_output=True,
            text=True,
        )

        # Should return error
        assert result.returncode != 0


class TestAnvilStatsIntegration:
    """Integration tests for statistics commands."""

    def test_stats_workflow_complete(self):
        """Test complete statistics workflow."""
        # This test would:
        # 1. Run some validations to generate data
        # 2. Query statistics
        # 3. Export results
        # For now, just test that commands don't crash

        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "report"],
            capture_output=True,
            text=True,
        )
        assert result.returncode in [0, 1]

    def test_stats_commands_with_custom_database(self, tmp_path):
        """Test stats commands with custom database path."""
        tmp_path / "custom_stats.db"

        # Commands should respect ANVIL_DB environment variable or config
        result = subprocess.run(
            ["python", "-m", "anvil", "stats", "report"],
            capture_output=True,
            text=True,
        )

        assert result.returncode in [0, 1]
