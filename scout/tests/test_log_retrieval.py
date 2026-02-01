"""
Tests for log retrieval and caching functionality.

Tests cover:
- ANSI code removal
- Timestamp extraction
- Log parsing
- Cache storage and retrieval
- Log retriever integration
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

from scout.log_retrieval import LogCache, LogParser, LogRetriever, WorkflowLog
from scout.providers.base import Job, LogEntry


class TestLogParser:
    """Test the LogParser class."""

    def test_remove_ansi_codes_simple(self):
        """Test removal of basic ANSI escape codes."""
        text = "\x1b[31mError\x1b[0m: Something failed"
        clean = LogParser.remove_ansi_codes(text)
        assert clean == "Error: Something failed"

    def test_remove_ansi_codes_multiple(self):
        """Test removal of multiple ANSI codes in one line."""
        text = "\x1b[32mSUCCESS\x1b[0m \x1b[1mbold\x1b[0m \x1b[33mwarning\x1b[0m"
        clean = LogParser.remove_ansi_codes(text)
        assert clean == "SUCCESS bold warning"

    def test_remove_ansi_codes_no_codes(self):
        """Test that text without ANSI codes is unchanged."""
        text = "Plain text without codes"
        clean = LogParser.remove_ansi_codes(text)
        assert clean == text

    def test_remove_ansi_codes_empty(self):
        """Test removal from empty string."""
        clean = LogParser.remove_ansi_codes("")
        assert clean == ""

    def test_extract_timestamp_iso8601(self):
        """Test extraction of ISO 8601 timestamp."""
        line = "2026-02-01T10:30:45Z Starting build"
        timestamp = LogParser.extract_timestamp(line)
        assert timestamp is not None
        assert timestamp.year == 2026
        assert timestamp.month == 2
        assert timestamp.day == 1
        assert timestamp.hour == 10
        assert timestamp.minute == 30
        assert timestamp.second == 45

    def test_extract_timestamp_iso8601_with_millis(self):
        """Test extraction of ISO 8601 timestamp with milliseconds."""
        line = "2026-02-01T10:30:45.123Z Log entry"
        timestamp = LogParser.extract_timestamp(line)
        assert timestamp is not None
        assert timestamp.microsecond == 123000

    def test_extract_timestamp_space_separated(self):
        """Test extraction of space-separated timestamp."""
        line = "2026-02-01 10:30:45 Build completed"
        timestamp = LogParser.extract_timestamp(line)
        assert timestamp is not None
        assert timestamp.year == 2026
        assert timestamp.hour == 10

    def test_extract_timestamp_unix(self):
        """Test extraction of Unix timestamp."""
        line = "[1704110400] Log message"
        timestamp = LogParser.extract_timestamp(line)
        assert timestamp is not None

    def test_extract_timestamp_no_timestamp(self):
        """Test that None is returned when no timestamp found."""
        line = "Just a regular log line with no timestamp"
        timestamp = LogParser.extract_timestamp(line)
        assert timestamp is None

    def test_parse_log_lines_simple(self):
        """Test parsing simple log lines."""
        raw_log = "Line 1\nLine 2\nLine 3"
        entries = LogParser.parse_log_lines(raw_log)

        assert len(entries) == 3
        assert entries[0].line_number == 1
        assert entries[0].content == "Line 1"
        assert entries[1].line_number == 2
        assert entries[1].content == "Line 2"
        assert entries[2].line_number == 3
        assert entries[2].content == "Line 3"

    def test_parse_log_lines_with_ansi(self):
        """Test parsing log lines with ANSI codes."""
        raw_log = "\x1b[32mSuccess\x1b[0m\n\x1b[31mError\x1b[0m"
        entries = LogParser.parse_log_lines(raw_log)

        assert len(entries) == 2
        assert entries[0].content == "Success"
        assert entries[1].content == "Error"

    def test_parse_log_lines_with_timestamps(self):
        """Test parsing log lines with timestamps."""
        raw_log = "2026-02-01T10:30:45Z Build started\n" "2026-02-01T10:30:50Z Build completed"
        entries = LogParser.parse_log_lines(raw_log)

        assert len(entries) == 2
        assert entries[0].timestamp is not None
        assert entries[0].timestamp.minute == 30
        assert entries[0].timestamp.second == 45
        assert entries[1].timestamp is not None
        assert entries[1].timestamp.second == 50

    def test_parse_log_lines_skip_empty(self):
        """Test that empty lines are skipped."""
        raw_log = "Line 1\n\n\nLine 2\n"
        entries = LogParser.parse_log_lines(raw_log)

        assert len(entries) == 2
        assert entries[0].content == "Line 1"
        assert entries[1].content == "Line 2"

    def test_parse_log_lines_empty_input(self):
        """Test parsing empty log."""
        entries = LogParser.parse_log_lines("")
        assert len(entries) == 0

    def test_extract_timestamp_invalid_format(self):
        """Test that invalid timestamp formats don't crash the parser."""
        # This timestamp looks valid but has bad values
        line = "2026-99-99T99:99:99Z Invalid timestamp"
        timestamp = LogParser.extract_timestamp(line)
        # Should return None instead of crashing
        assert timestamp is None


class TestLogCache:
    """Test the LogCache class."""

    def test_cache_initialization(self):
        """Test cache directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache_dir = Path(tmpdir) / "cache"
            cache = LogCache(cache_dir)
            assert cache.cache_dir == cache_dir
            assert cache.cache_dir.exists()

    def test_is_cached_false_for_missing(self):
        """Test is_cached returns False for missing logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LogCache(Path(tmpdir))
            assert not cache.is_cached("run123", "job456")

    def test_save_and_load_log(self):
        """Test saving and loading a log."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LogCache(Path(tmpdir))

            # Create a test log
            entries = [
                LogEntry(
                    timestamp=datetime(2026, 2, 1, 10, 30, 45),
                    line_number=1,
                    content="Build started",
                ),
                LogEntry(
                    timestamp=datetime(2026, 2, 1, 10, 30, 50),
                    line_number=2,
                    content="Build completed",
                ),
            ]

            workflow_log = WorkflowLog(
                run_id="run123",
                job_id="job456",
                job_name="Test Job",
                entries=entries,
                retrieved_at=datetime(2026, 2, 1, 10, 31, 0),
                raw_size=100,
                parsed_size=90,
            )

            # Save and verify cached
            cache.save(workflow_log)
            assert cache.is_cached("run123", "job456")

            # Load and verify
            loaded = cache.load("run123", "job456")
            assert loaded is not None
            assert loaded.run_id == "run123"
            assert loaded.job_id == "job456"
            assert loaded.job_name == "Test Job"
            assert len(loaded.entries) == 2
            assert loaded.entries[0].content == "Build started"
            assert loaded.entries[1].content == "Build completed"
            assert loaded.raw_size == 100
            assert loaded.parsed_size == 90

    def test_save_log_with_no_timestamps(self):
        """Test saving log entries without timestamps."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LogCache(Path(tmpdir))

            entries = [LogEntry(timestamp=None, line_number=1, content="Line without timestamp")]

            workflow_log = WorkflowLog(
                run_id="run123",
                job_id="job456",
                job_name="Test",
                entries=entries,
                retrieved_at=datetime.now(),
                raw_size=50,
                parsed_size=50,
            )

            cache.save(workflow_log)
            loaded = cache.load("run123", "job456")

            assert loaded is not None
            assert len(loaded.entries) == 1
            assert loaded.entries[0].timestamp is None
            assert loaded.entries[0].content == "Line without timestamp"

    def test_load_nonexistent_log(self):
        """Test loading a log that doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LogCache(Path(tmpdir))
            loaded = cache.load("nonexistent", "job")
            assert loaded is None

    def test_clear_specific_run(self):
        """Test clearing logs for a specific run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LogCache(Path(tmpdir))

            # Create logs for two different runs
            for run_id in ["run1", "run2"]:
                for job_id in ["job1", "job2"]:
                    log = WorkflowLog(
                        run_id=run_id,
                        job_id=job_id,
                        job_name=f"Job {job_id}",
                        entries=[],
                        retrieved_at=datetime.now(),
                        raw_size=0,
                        parsed_size=0,
                    )
                    cache.save(log)

            # Clear run1
            cache.clear("run1")

            # Verify run1 is cleared but run2 remains
            assert not cache.is_cached("run1", "job1")
            assert not cache.is_cached("run1", "job2")
            assert cache.is_cached("run2", "job1")
            assert cache.is_cached("run2", "job2")

    def test_clear_all_logs(self):
        """Test clearing all cached logs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LogCache(Path(tmpdir))

            # Create multiple logs
            for run_id in ["run1", "run2"]:
                for job_id in ["job1", "job2"]:
                    log = WorkflowLog(
                        run_id=run_id,
                        job_id=job_id,
                        job_name="Test",
                        entries=[],
                        retrieved_at=datetime.now(),
                        raw_size=0,
                        parsed_size=0,
                    )
                    cache.save(log)

            # Clear all
            count = cache.clear()

            # Verify all cleared
            assert count >= 0
            assert not cache.is_cached("run1", "job1")
            assert not cache.is_cached("run2", "job2")


class TestLogRetriever:
    """Test the LogRetriever class."""

    def test_initialization_default_cache_dir(self):
        """Test retriever initialization with default cache directory."""
        provider = Mock()
        retriever = LogRetriever(provider)

        assert retriever.provider == provider
        assert retriever.cache.cache_dir == Path.home() / ".scout" / "cache"

    def test_initialization_custom_cache_dir(self):
        """Test retriever initialization with custom cache directory."""
        provider = Mock()
        custom_dir = Path("/tmp/custom_cache")

        retriever = LogRetriever(provider, cache_dir=custom_dir)

        assert retriever.cache.cache_dir == custom_dir

    def test_get_logs_from_provider(self):
        """Test getting logs from provider when not cached."""
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = Mock()
            provider.get_logs.return_value = [
                LogEntry(
                    timestamp=None, line_number=1, content="2026-02-01T10:30:45Z Build started"
                ),
                LogEntry(
                    timestamp=None, line_number=2, content="2026-02-01T10:30:50Z Tests passed"
                ),
            ]
            provider.get_jobs.return_value = [
                Job(
                    id="job456",
                    name="Test Job",
                    status="completed",
                    conclusion="success",
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    url="https://example.com",
                )
            ]

            retriever = LogRetriever(provider, cache_dir=Path(tmpdir))

            # Get logs
            log = retriever.get_logs("run123", "job456", use_cache=False)

            # Verify provider was called
            provider.get_logs.assert_called_once_with("job456")
            provider.get_jobs.assert_called_once_with("run123")

            # Verify log structure
            assert log.run_id == "run123"
            assert log.job_id == "job456"
            assert log.job_name == "Test Job"
            assert len(log.entries) == 2
            assert log.entries[0].content == "2026-02-01T10:30:45Z Build started"
            assert log.entries[0].timestamp is not None

    def test_get_logs_from_cache(self):
        """Test getting logs from cache when available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = Mock()

            retriever = LogRetriever(provider, cache_dir=Path(tmpdir))

            # Pre-populate cache
            cached_log = WorkflowLog(
                run_id="run123",
                job_id="job456",
                job_name="Cached Job",
                entries=[LogEntry(timestamp=None, line_number=1, content="Cached log line")],
                retrieved_at=datetime.now(),
                raw_size=50,
                parsed_size=50,
            )
            retriever.cache.save(cached_log)

            # Get logs with cache enabled
            log = retriever.get_logs("run123", "job456", use_cache=True)

            # Verify provider was NOT called
            provider.get_logs.assert_not_called()

            # Verify we got cached log
            assert log.job_name == "Cached Job"
            assert log.entries[0].content == "Cached log line"

    def test_get_logs_bypasses_cache_when_disabled(self):
        """Test that cache can be bypassed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = Mock()
            provider.get_logs.return_value = [
                LogEntry(timestamp=None, line_number=1, content="Fresh log")
            ]
            provider.get_jobs.return_value = [
                Job(
                    id="job456",
                    name="Fresh Job",
                    status="completed",
                    conclusion="success",
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    url="https://example.com",
                )
            ]

            retriever = LogRetriever(provider, cache_dir=Path(tmpdir))

            # Pre-populate cache
            cached_log = WorkflowLog(
                run_id="run123",
                job_id="job456",
                job_name="Cached Job",
                entries=[LogEntry(timestamp=None, line_number=1, content="Cached log")],
                retrieved_at=datetime.now(),
                raw_size=50,
                parsed_size=50,
            )
            retriever.cache.save(cached_log)

            # Get logs with cache disabled
            log = retriever.get_logs("run123", "job456", use_cache=False)

            # Verify provider WAS called
            provider.get_logs.assert_called_once()

            # Verify we got fresh log
            assert log.entries[0].content == "Fresh log"

    def test_get_all_job_logs(self):
        """Test getting logs for all jobs in a run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = Mock()

            # Mock jobs
            provider.get_jobs.return_value = [
                Job(
                    id="job1",
                    name="Job 1",
                    status="completed",
                    conclusion="success",
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    url="https://example.com",
                ),
                Job(
                    id="job2",
                    name="Job 2",
                    status="completed",
                    conclusion="failure",
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    url="https://example.com",
                ),
            ]

            # Mock logs
            def get_logs_side_effect(job_id):
                return [LogEntry(timestamp=None, line_number=1, content=f"Log for {job_id}")]

            provider.get_logs.side_effect = get_logs_side_effect

            retriever = LogRetriever(provider, cache_dir=Path(tmpdir))

            # Get all logs
            logs = retriever.get_all_job_logs("run123", use_cache=False)

            # Verify
            assert len(logs) == 2
            assert logs[0].job_id == "job1"
            assert logs[1].job_id == "job2"
            assert logs[0].job_name == "Job 1"
            assert logs[1].job_name == "Job 2"

    def test_get_all_job_logs_handles_errors(self):
        """Test that get_all_job_logs continues on individual failures."""
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = Mock()

            provider.get_jobs.return_value = [
                Job(
                    id="job1",
                    name="Job 1",
                    status="completed",
                    conclusion="success",
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    url="https://example.com",
                ),
                Job(
                    id="job2",
                    name="Job 2",
                    status="completed",
                    conclusion="success",
                    started_at=datetime.now(),
                    completed_at=datetime.now(),
                    url="https://example.com",
                ),
            ]

            # job1 succeeds, job2 fails
            def get_logs_side_effect(job_id):
                if job_id == "job1":
                    return [LogEntry(timestamp=None, line_number=1, content="Success")]
                else:
                    raise Exception("API error")

            provider.get_logs.side_effect = get_logs_side_effect

            retriever = LogRetriever(provider, cache_dir=Path(tmpdir))

            # Should get job1's log despite job2 failing
            logs = retriever.get_all_job_logs("run123", use_cache=False)

            assert len(logs) == 1
            assert logs[0].job_id == "job1"

    def test_get_logs_with_no_job_found(self):
        """Test getting logs when job info is not found."""
        with tempfile.TemporaryDirectory() as tmpdir:
            provider = Mock()
            provider.get_logs.return_value = [
                LogEntry(timestamp=None, line_number=1, content="Log line")
            ]
            # Return empty job list (job not found)
            provider.get_jobs.return_value = []

            retriever = LogRetriever(provider, cache_dir=Path(tmpdir))
            log = retriever.get_logs("run123", "job456", use_cache=False)

            # Should use generic job name
            assert log.job_name == "Job job456"

    def test_cache_save_creates_directory_structure(self):
        """Test that saving creates the necessary directory structure."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LogCache(Path(tmpdir))

            log = WorkflowLog(
                run_id="nested/run",
                job_id="job123",
                job_name="Test",
                entries=[],
                retrieved_at=datetime.now(),
                raw_size=0,
                parsed_size=0,
            )

            cache.save(log)
            assert cache.is_cached("nested/run", "job123")

    def test_load_with_invalid_timestamp_in_cache(self):
        """Test loading cached log with corrupted timestamp."""
        with tempfile.TemporaryDirectory() as tmpdir:
            cache = LogCache(Path(tmpdir))

            # Create a log file with invalid timestamp
            log_path = cache._get_log_path("run123", "job456")
            metadata_path = cache._get_metadata_path("run123", "job456")

            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Write log with invalid timestamp
            with open(log_path, "w", encoding="utf-8") as f:
                f.write("invalid-timestamp|1|Test content\n")

            # Write valid metadata
            with open(metadata_path, "w", encoding="utf-8") as f:
                f.write("run_id=run123\n")
                f.write("job_id=job456\n")
                f.write("job_name=Test\n")
                f.write("retrieved_at=2026-02-01T10:00:00\n")
                f.write("raw_size=100\n")
                f.write("parsed_size=90\n")

            # Load should handle invalid timestamp gracefully
            loaded = cache.load("run123", "job456")
            assert loaded is not None
            assert len(loaded.entries) == 1
            assert loaded.entries[0].timestamp is None


class TestWorkflowLog:
    """Test the WorkflowLog dataclass."""

    def test_workflow_log_creation(self):
        """Test creating a WorkflowLog."""
        entries = [LogEntry(timestamp=datetime.now(), line_number=1, content="Test log")]

        log = WorkflowLog(
            run_id="run123",
            job_id="job456",
            job_name="Test Job",
            entries=entries,
            retrieved_at=datetime.now(),
            raw_size=100,
            parsed_size=90,
        )

        assert log.run_id == "run123"
        assert log.job_id == "job456"
        assert log.job_name == "Test Job"
        assert len(log.entries) == 1
        assert log.raw_size == 100
        assert log.parsed_size == 90
