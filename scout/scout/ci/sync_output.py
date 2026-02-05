"""
Verbose output formatting for Scout CI sync operations.

Provides formatted output for download, parsing, and summary operations.
"""

from datetime import datetime
from typing import List, Optional


class SyncOutputFormatter:
    """Format and print verbose output for CI sync operations."""

    # ANSI color codes
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

    @staticmethod
    def header(
        workflow: Optional[str], limit: Optional[int], force_download: bool, force_parse: bool
    ):
        """Print operation header."""
        print("\n" + "=" * 70)
        print(
            f"{SyncOutputFormatter.BOLD}Scout CI Sync - Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{SyncOutputFormatter.RESET}"
        )
        print("=" * 70)

        if workflow:
            print(f"Workflow filter:     {workflow}")
        else:
            print("Workflow filter:     All workflows")

        if limit:
            print(f"Limit:               Last {limit} executions")
        else:
            print("Limit:               All available executions")

        print(f"Force download:      {force_download}")
        print(f"Force parse:         {force_parse}")
        print("=" * 70 + "\n")

    @staticmethod
    def download_started(workflow_name: str, run_number: int):
        """Print download started message."""
        print(
            f"{SyncOutputFormatter.BLUE}[↓] Downloading{SyncOutputFormatter.RESET} {workflow_name} #{run_number}"
        )

    @staticmethod
    def download_completed(workflow_name: str, job_name: str, lines: int, size_kb: float):
        """Print download completed message."""
        print(
            f"    {SyncOutputFormatter.GREEN}✓{SyncOutputFormatter.RESET} Downloaded job '{job_name}'"
        )
        print(f"      File: {lines} lines, {size_kb:.1f} KB")

    @staticmethod
    def download_skipped(job_name: str, reason: str = "already cached"):
        """Print download skipped message."""
        print(
            f"    {SyncOutputFormatter.YELLOW}⊘{SyncOutputFormatter.RESET} Skipped job '{job_name}' ({reason})"
        )

    @staticmethod
    def parse_started(workflow_name: str, job_name: str, parser_names: List[str]):
        """Print parsing started message."""
        parsers_str = ", ".join(parser_names)
        print(
            f"{SyncOutputFormatter.BLUE}[⟲] Parsing{SyncOutputFormatter.RESET} {workflow_name}/{job_name}"
        )
        print(f"    Parsers: {parsers_str}")

    @staticmethod
    def parse_completed(test_count: int, passed: int, failed: int, skipped: int):
        """Print parsing completed message."""
        print(f"    {SyncOutputFormatter.GREEN}✓{SyncOutputFormatter.RESET} Parsed successfully")
        print(
            f"      Results: {test_count} tests ({passed} passed, {failed} failed, {skipped} skipped)"
        )

    @staticmethod
    def parse_skipped(reason: str = "already in database"):
        """Print parsing skipped message."""
        print(f"    {SyncOutputFormatter.YELLOW}⊘{SyncOutputFormatter.RESET} Skipped ({reason})")

    @staticmethod
    def error(message: str):
        """Print error message."""
        print(f"{SyncOutputFormatter.RED}[✗] Error{SyncOutputFormatter.RESET}: {message}")

    @staticmethod
    def summary(
        downloaded: int,
        skipped_download: int,
        parsed: int,
        skipped_parse: int,
        total_tests: int,
        errors: Optional[List[str]] = None,
    ):
        """Print operation summary."""
        print("\n" + "=" * 70)
        print(f"{SyncOutputFormatter.BOLD}Scout CI Sync Summary{SyncOutputFormatter.RESET}")
        print("=" * 70)
        print(f"Downloaded:          {downloaded} job(s)")
        print(f"Skipped (cached):    {skipped_download} job(s)")
        print(f"Total jobs:          {downloaded + skipped_download}")
        print()
        print(f"Parsed:              {parsed} run(s)")
        print(f"Skipped (in DB):     {skipped_parse} run(s)")
        print(f"Total tests synced:  {total_tests}")

        if errors:
            print()
            print("Errors encountered:")
            for error in errors:
                print(f"  {SyncOutputFormatter.RED}✗{SyncOutputFormatter.RESET} {error}")

        print("=" * 70 + "\n")
