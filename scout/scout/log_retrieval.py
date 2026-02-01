"""
Log retrieval and caching module for Scout.

This module handles downloading logs from CI providers, parsing them
(removing ANSI codes, extracting timestamps), and caching them locally.
"""

import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from scout.providers.base import CIProvider, LogEntry


@dataclass
class WorkflowLog:
    """
    Complete log for a workflow run with metadata.

    Attributes:
        run_id: Unique identifier for the workflow run
        job_id: Unique identifier for the job
        job_name: Name of the job
        entries: List of log entries
        retrieved_at: Timestamp when log was retrieved
        raw_size: Size of raw log in bytes
        parsed_size: Size of parsed log (without ANSI codes)
    """

    run_id: str
    job_id: str
    job_name: str
    entries: List[LogEntry]
    retrieved_at: datetime
    raw_size: int
    parsed_size: int


class LogParser:
    """
    Parser for CI log output.

    Handles ANSI escape code removal and timestamp extraction.
    """

    # ANSI escape code pattern
    ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")

    # Common timestamp patterns in logs
    TIMESTAMP_PATTERNS = [
        # ISO 8601 format: 2026-02-01T10:30:45.123Z
        re.compile(r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)"),
        # GitHub Actions format: 2026-02-01 10:30:45
        re.compile(r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"),
        # Unix timestamp format: [1234567890]
        re.compile(r"\[(\d{10})\]"),
    ]

    @classmethod
    def remove_ansi_codes(cls, text: str) -> str:
        """
        Remove ANSI escape codes from text.

        Args:
            text: Text potentially containing ANSI codes

        Returns:
            Text with ANSI codes removed

        Examples:
            >>> LogParser.remove_ansi_codes("\\x1b[31mError\\x1b[0m")
            'Error'
        """
        return cls.ANSI_PATTERN.sub("", text)

    @classmethod
    def extract_timestamp(cls, line: str) -> Optional[datetime]:
        """
        Extract timestamp from a log line.

        Tries multiple timestamp patterns to find a match.

        Args:
            line: Log line that may contain a timestamp

        Returns:
            Extracted timestamp or None if not found

        Examples:
            >>> line = "2026-02-01T10:30:45Z Starting build"
            >>> ts = LogParser.extract_timestamp(line)
            >>> ts.year
            2026
        """
        for pattern in cls.TIMESTAMP_PATTERNS:
            match = pattern.search(line)
            if match:
                timestamp_str = match.group(1)
                try:
                    # Try ISO 8601 format first
                    if "T" in timestamp_str:
                        timestamp_str = timestamp_str.rstrip("Z")
                        return datetime.fromisoformat(timestamp_str)
                    # Try space-separated format
                    elif " " in timestamp_str:
                        return datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    # Try Unix timestamp
                    else:
                        return datetime.fromtimestamp(int(timestamp_str))
                except (ValueError, OSError):
                    continue

        return None

    @classmethod
    def parse_log_lines(cls, raw_log: str) -> List[LogEntry]:
        """
        Parse raw log text into structured LogEntry objects.

        Args:
            raw_log: Raw log text from CI provider

        Returns:
            List of parsed log entries

        Examples:
            >>> raw = "\\x1b[32m2026-02-01T10:30:45Z\\x1b[0m Build started\\n"
            >>> entries = LogParser.parse_log_lines(raw)
            >>> len(entries)
            1
            >>> entries[0].content
            '2026-02-01T10:30:45Z Build started'
        """
        entries = []
        lines = raw_log.splitlines()

        for line_num, line in enumerate(lines, start=1):
            # Remove ANSI codes
            clean_line = cls.remove_ansi_codes(line)

            # Skip empty lines
            if not clean_line.strip():
                continue

            # Extract timestamp if present
            timestamp = cls.extract_timestamp(clean_line)

            # Create log entry
            entry = LogEntry(timestamp=timestamp, line_number=line_num, content=clean_line)
            entries.append(entry)

        return entries


class LogCache:
    """
    Local cache for downloaded logs.

    Stores logs in a directory structure organized by run ID and job ID.
    """

    def __init__(self, cache_dir: Path):
        """
        Initialize log cache.

        Args:
            cache_dir: Directory to store cached logs
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_path(self, run_id: str, job_id: str) -> Path:
        """
        Get the file path for a cached log.

        Args:
            run_id: Workflow run ID
            job_id: Job ID

        Returns:
            Path to cached log file
        """
        return self.cache_dir / run_id / f"{job_id}.log"

    def _get_metadata_path(self, run_id: str, job_id: str) -> Path:
        """
        Get the file path for log metadata.

        Args:
            run_id: Workflow run ID
            job_id: Job ID

        Returns:
            Path to metadata file
        """
        return self.cache_dir / run_id / f"{job_id}.meta"

    def is_cached(self, run_id: str, job_id: str) -> bool:
        """
        Check if a log is in the cache.

        Args:
            run_id: Workflow run ID
            job_id: Job ID

        Returns:
            True if log is cached, False otherwise
        """
        log_path = self._get_log_path(run_id, job_id)
        return log_path.exists()

    def save(self, workflow_log: WorkflowLog) -> None:
        """
        Save a log to the cache.

        Args:
            workflow_log: Log to cache

        Examples:
            >>> from datetime import datetime
            >>> cache = LogCache(Path("/tmp/logs"))
            >>> log = WorkflowLog(
            ...     run_id="123",
            ...     job_id="456",
            ...     job_name="test",
            ...     entries=[],
            ...     retrieved_at=datetime.now(),
            ...     raw_size=100,
            ...     parsed_size=90
            ... )
            >>> cache.save(log)
        """
        log_path = self._get_log_path(workflow_log.run_id, workflow_log.job_id)
        metadata_path = self._get_metadata_path(workflow_log.run_id, workflow_log.job_id)

        # Create directory
        log_path.parent.mkdir(parents=True, exist_ok=True)

        # Save log entries
        with open(log_path, "w", encoding="utf-8") as f:
            for entry in workflow_log.entries:
                # Format: timestamp|line_number|content
                timestamp_str = entry.timestamp.isoformat() if entry.timestamp else "None"
                f.write(f"{timestamp_str}|{entry.line_number}|{entry.content}\n")

        # Save metadata
        with open(metadata_path, "w", encoding="utf-8") as f:
            f.write(f"run_id={workflow_log.run_id}\n")
            f.write(f"job_id={workflow_log.job_id}\n")
            f.write(f"job_name={workflow_log.job_name}\n")
            f.write(f"retrieved_at={workflow_log.retrieved_at.isoformat()}\n")
            f.write(f"raw_size={workflow_log.raw_size}\n")
            f.write(f"parsed_size={workflow_log.parsed_size}\n")

    def load(self, run_id: str, job_id: str) -> Optional[WorkflowLog]:
        """
        Load a log from the cache.

        Args:
            run_id: Workflow run ID
            job_id: Job ID

        Returns:
            Cached log or None if not found

        Examples:
            >>> cache = LogCache(Path("/tmp/logs"))
            >>> log = cache.load("123", "456")
            >>> log is None or isinstance(log, WorkflowLog)
            True
        """
        if not self.is_cached(run_id, job_id):
            return None

        log_path = self._get_log_path(run_id, job_id)
        metadata_path = self._get_metadata_path(run_id, job_id)

        # Load metadata
        metadata = {}
        with open(metadata_path, "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    metadata[key] = value

        # Load log entries
        entries = []
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.rstrip("\n").split("|", 2)
                if len(parts) == 3:
                    timestamp_str, line_num_str, content = parts

                    # Parse timestamp
                    timestamp = None
                    if timestamp_str != "None":
                        try:
                            timestamp = datetime.fromisoformat(timestamp_str)
                        except ValueError:
                            pass

                    # Create entry
                    entry = LogEntry(
                        timestamp=timestamp,
                        line_number=int(line_num_str),
                        content=content,
                    )
                    entries.append(entry)

        # Create WorkflowLog
        return WorkflowLog(
            run_id=metadata["run_id"],
            job_id=metadata["job_id"],
            job_name=metadata["job_name"],
            entries=entries,
            retrieved_at=datetime.fromisoformat(metadata["retrieved_at"]),
            raw_size=int(metadata["raw_size"]),
            parsed_size=int(metadata["parsed_size"]),
        )

    def clear(self, run_id: Optional[str] = None) -> int:
        """
        Clear cached logs.

        Args:
            run_id: If provided, clear only logs for this run.
                   If None, clear all cached logs.

        Returns:
            Number of logs cleared

        Examples:
            >>> cache = LogCache(Path("/tmp/logs"))
            >>> count = cache.clear()
            >>> count >= 0
            True
        """
        import shutil

        count = 0

        if run_id:
            # Clear specific run
            run_dir = self.cache_dir / run_id
            if run_dir.exists():
                shutil.rmtree(run_dir)
                count = len(list(run_dir.glob("*.log"))) if run_dir.exists() else 0
        else:
            # Clear all
            if self.cache_dir.exists():
                count = len(list(self.cache_dir.rglob("*.log")))
                shutil.rmtree(self.cache_dir)
                self.cache_dir.mkdir(parents=True, exist_ok=True)

        return count


class LogRetriever:
    """
    High-level interface for retrieving and caching logs from CI providers.
    """

    def __init__(self, provider: CIProvider, cache_dir: Optional[Path] = None):
        """
        Initialize log retriever.

        Args:
            provider: CI provider to retrieve logs from
            cache_dir: Directory for caching logs (default: ~/.scout/cache)
        """
        self.provider = provider

        if cache_dir is None:
            cache_dir = Path.home() / ".scout" / "cache"

        self.cache = LogCache(cache_dir)

    def get_logs(self, run_id: str, job_id: str, use_cache: bool = True) -> WorkflowLog:
        """
        Get logs for a specific job.

        Retrieves from cache if available, otherwise downloads from provider.

        Args:
            run_id: Workflow run ID
            job_id: Job ID
            use_cache: Whether to use cached logs if available

        Returns:
            Workflow log with parsed entries

        Raises:
            Exception: If log retrieval fails

        Examples:
            >>> from scout.providers.github_actions import GitHubActionsProvider
            >>> provider = GitHubActionsProvider("owner", "repo")
            >>> retriever = LogRetriever(provider)
            >>> # log = retriever.get_logs("123", "456")  # Would fetch from API
        """
        # Check cache first
        if use_cache and self.cache.is_cached(run_id, job_id):
            cached_log = self.cache.load(run_id, job_id)
            if cached_log:
                return cached_log

        # Download from provider
        raw_entries = self.provider.get_logs(job_id)

        # Reconstruct raw log text
        raw_log = "\n".join(entry.content for entry in raw_entries)
        raw_size = len(raw_log)

        # Parse log
        parsed_entries = LogParser.parse_log_lines(raw_log)
        parsed_size = sum(len(entry.content) for entry in parsed_entries)

        # Get job info
        jobs = self.provider.get_jobs(run_id)
        job = next((j for j in jobs if j.id == job_id), None)
        job_name = job.name if job else f"Job {job_id}"

        # Create workflow log
        workflow_log = WorkflowLog(
            run_id=run_id,
            job_id=job_id,
            job_name=job_name,
            entries=parsed_entries,
            retrieved_at=datetime.now(),
            raw_size=raw_size,
            parsed_size=parsed_size,
        )

        # Save to cache
        self.cache.save(workflow_log)

        return workflow_log

    def get_all_job_logs(self, run_id: str, use_cache: bool = True) -> List[WorkflowLog]:
        """
        Get logs for all jobs in a workflow run.

        Args:
            run_id: Workflow run ID
            use_cache: Whether to use cached logs if available

        Returns:
            List of workflow logs for all jobs

        Examples:
            >>> from scout.providers.github_actions import GitHubActionsProvider
            >>> provider = GitHubActionsProvider("owner", "repo")
            >>> retriever = LogRetriever(provider)
            >>> # logs = retriever.get_all_job_logs("123")  # Would fetch from API
        """
        jobs = self.provider.get_jobs(run_id)
        logs = []

        for job in jobs:
            try:
                log = self.get_logs(run_id, job.id, use_cache=use_cache)
                logs.append(log)
            except Exception as e:
                # Log error but continue with other jobs
                print(f"Warning: Failed to get logs for job {job.id}: {e}")

        return logs
