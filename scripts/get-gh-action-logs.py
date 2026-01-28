#!/usr/bin/env python3
"""
Fetch and parse GitHub Actions logs for failed tests.

This script fetches the latest GitHub Actions workflow run logs and extracts
information about failed tests, making it easier to debug CI failures.

Usage:
    python scripts/get-gh-action-logs.py [--workflow-name WORKFLOW] [--run-id ID]

Requirements:
    pip install requests python-dotenv

Environment:
    GITHUB_TOKEN - Optional, but recommended for higher rate limits
                   Can be set in .env file or as environment variable

.env file example:
    GITHUB_TOKEN=your_token_here
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    print("Error: 'requests' module not found.")
    print("Install it with: pip install requests python-dotenv")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    # Load .env file from project root (parent of scripts directory)
    env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=env_path)
except ImportError:
    # python-dotenv not installed, will use system environment variables only
    pass


class GitHubActionsLogFetcher:
    """Fetch and parse GitHub Actions logs."""

    def __init__(self, repo_owner: str, repo_name: str, token: Optional[str] = None):
        """
        Initialize the log fetcher.

        Args:
            repo_owner: GitHub repository owner
            repo_name: GitHub repository name
            token: GitHub personal access token (optional, for rate limits)
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.base_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def get_latest_run(self, workflow_name: Optional[str] = None) -> Optional[Dict]:
        """
        Get the latest workflow run.

        Args:
            workflow_name: Filter by workflow name (optional)

        Returns:
            Workflow run data or None if not found
        """
        url = f"{self.base_url}/actions/runs"
        params = {"per_page": 10, "status": "completed"}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            runs = data.get("workflow_runs", [])
            if not runs:
                print("No workflow runs found")
                return None

            # Filter by workflow name if provided
            if workflow_name:
                runs = [r for r in runs if workflow_name.lower() in r["name"].lower()]

            if not runs:
                print(f"No runs found for workflow: {workflow_name}")
                return None

            return runs[0]

        except requests.RequestException as e:
            print(f"Error fetching workflow runs: {e}")
            return None

    def get_run_by_id(self, run_id: int) -> Optional[Dict]:
        """
        Get a specific workflow run by ID.

        Args:
            run_id: GitHub Actions workflow run ID

        Returns:
            Workflow run data or None if not found
        """
        url = f"{self.base_url}/actions/runs/{run_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching run {run_id}: {e}")
            return None

    def get_failed_jobs(self, run_id: int) -> List[Dict]:
        """
        Get all failed jobs for a workflow run.

        Args:
            run_id: GitHub Actions workflow run ID

        Returns:
            List of failed job data
        """
        url = f"{self.base_url}/actions/runs/{run_id}/jobs"

        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            jobs = data.get("jobs", [])
            failed_jobs = [job for job in jobs if job["conclusion"] == "failure"]
            return failed_jobs

        except requests.RequestException as e:
            print(f"Error fetching jobs: {e}")
            return []

    def get_job_logs(self, job_id: int) -> Optional[str]:
        """
        Get logs for a specific job.

        Args:
            job_id: GitHub Actions job ID

        Returns:
            Job logs as string or None if not found
        """
        url = f"{self.base_url}/actions/jobs/{job_id}/logs"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching logs for job {job_id}: {e}")
            return None

    def parse_pytest_failures(self, logs: str) -> List[Dict]:
        """
        Parse pytest failure information from logs.

        Args:
            logs: Raw log text

        Returns:
            List of failed test information
        """
        failures = []

        # Pattern for pytest FAILED lines
        failed_pattern = re.compile(
            r"FAILED ([\w/:.]+::\w+(?:::\w+)*) - (.+)$", re.MULTILINE
        )

        for match in failed_pattern.finditer(logs):
            test_name = match.group(1)
            error_msg = match.group(2)
            failures.append({"test": test_name, "error": error_msg})

        # Also look for ERROR lines
        error_pattern = re.compile(
            r"ERROR ([\w/:.]+::\w+(?:::\w+)*) - (.+)$", re.MULTILINE
        )

        for match in error_pattern.finditer(logs):
            test_name = match.group(1)
            error_msg = match.group(2)
            failures.append({"test": test_name, "error": error_msg, "type": "ERROR"})

        # Extract collection errors (ERROR collecting tests/...)
        collection_errors = self.extract_collection_errors(logs)
        failures.extend(collection_errors)

        return failures

    def extract_collection_errors(self, logs: str) -> List[Dict]:
        """
        Extract collection errors from pytest output.

        Args:
            logs: Raw log text

        Returns:
            List of collection error information
        """
        errors = []
        lines = logs.split('\n')

        # Look for "ERROR collecting" pattern
        for i, line in enumerate(lines):
            if 'ERROR collecting' in line:
                # Extract filename
                match = re.search(r'ERROR collecting (.+)$', line)
                if match:
                    file_path = match.group(1)

                    # Look ahead for the actual error message
                    error_details = []
                    for j in range(i+1, min(i+20, len(lines))):
                        next_line = lines[j]

                        # Stop at section boundaries
                        if '====' in next_line or '____' in next_line:
                            if error_details:  # Only break if we've found some details
                                break
                            continue

                        # Capture error messages
                        if any(keyword in next_line for keyword in
                               ['ModuleNotFoundError', 'ImportError', 'Error:', 'E   ']):
                            # Clean up the line
                            clean_line = next_line.strip()
                            if clean_line.startswith('E   '):
                                clean_line = clean_line[4:]  # Remove 'E   ' prefix
                            error_details.append(clean_line)

                    error_msg = ' '.join(error_details) if error_details else 'Collection error'
                    errors.append({
                        'test': file_path,
                        'error': error_msg,
                        'type': 'COLLECTION_ERROR'
                    })

        # Also extract summary error lines at the end
        summary_errors = re.findall(r'ERROR (tests/[\w/]+\.py)', logs)
        for error_file in summary_errors:
            # Check if we already have this error
            if not any(e['test'] == error_file for e in errors):
                errors.append({
                    'test': error_file,
                    'error': 'Collection failed (see details above)',
                    'type': 'COLLECTION_ERROR'
                })

        return errors

    def extract_failure_context(self, logs: str, test_name: str) -> Optional[str]:
        """
        Extract detailed failure context for a specific test.

        Args:
            logs: Raw log text
            test_name: Name of the failed test

        Returns:
            Failure context or None if not found
        """
        # Find the section with the test failure details
        pattern = re.compile(
            rf"_{40,}\s+{re.escape(test_name)}\s+_{40,}(.*?)(?=_{40,}|$)",
            re.DOTALL,
        )

        match = pattern.search(logs)
        if match:
            context = match.group(1).strip()
            # Limit to first 1000 characters to avoid overwhelming output
            if len(context) > 1000:
                context = context[:1000] + "\n... (truncated)"
            return context

        return None


def print_run_summary(run: Dict) -> None:
    """Print a summary of the workflow run."""
    print("\n" + "=" * 80)
    print(f"Workflow: {run['name']}")
    print(f"Run ID: {run['id']}")
    print(f"Status: {run['status']} / {run['conclusion']}")
    print(f"Branch: {run['head_branch']}")
    print(f"Commit: {run['head_sha'][:8]}")
    print(f"URL: {run['html_url']}")
    print("=" * 80 + "\n")


def print_failed_tests(failures: List[Dict], detailed: bool = False) -> None:
    """Print failed test information."""
    if not failures:
        print("[OK] No test failures found in logs")
        return

    print(f"\n[FAIL] Found {len(failures)} failed test(s):\n")

    for i, failure in enumerate(failures, 1):
        test_type = failure.get("type", "FAILED")
        print(f"{i}. [{test_type}] {failure['test']}")
        print(f"   Error: {failure['error']}")

        if detailed and "context" in failure:
            print(f"   Context:\n{failure['context']}\n")
        else:
            print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fetch and parse GitHub Actions logs for failed tests"
    )
    parser.add_argument(
        "--owner",
        default="lmvcruz",
        help="GitHub repository owner (default: lmvcruz)",
    )
    parser.add_argument(
        "--repo", default="argos", help="GitHub repository name (default: argos)"
    )
    parser.add_argument(
        "--workflow",
        help="Filter by workflow name (e.g., 'Forge Tests')",
    )
    parser.add_argument(
        "--run-id",
        type=int,
        help="Specific run ID to fetch (instead of latest)",
    )
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Show detailed failure context",
    )
    parser.add_argument(
        "--token",
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
    )

    args = parser.parse_args()

    # Get token from args or environment
    token = args.token or os.environ.get("GITHUB_TOKEN")

    # Initialize fetcher
    fetcher = GitHubActionsLogFetcher(args.owner, args.repo, token)

    # Get workflow run
    if args.run_id:
        print(f"Fetching run ID {args.run_id}...")
        run = fetcher.get_run_by_id(args.run_id)
    else:
        print("Fetching latest workflow run...")
        run = fetcher.get_latest_run(args.workflow)

    if not run:
        print("No workflow run found")
        return 1

    print_run_summary(run)

    # Check if run failed
    if run["conclusion"] == "success":
        print("[OK] Workflow run succeeded - no failures to report")
        return 0

    # Get failed jobs
    print("Fetching failed jobs...")
    failed_jobs = fetcher.get_failed_jobs(run["id"])

    if not failed_jobs:
        print("No failed jobs found (might be a different type of failure)")
        return 0

    print(f"Found {len(failed_jobs)} failed job(s)\n")

    # Process each failed job
    all_failures = []
    for job in failed_jobs:
        print(f"[JOB] {job['name']}")
        print(f"   URL: {job['html_url']}\n")

        print("   Fetching logs...")
        logs = fetcher.get_job_logs(job["id"])

        if not logs:
            print("   Could not fetch logs\n")
            continue

        # Parse failures
        failures = fetcher.parse_pytest_failures(logs)

        if args.detailed:
            for failure in failures:
                context = fetcher.extract_failure_context(logs, failure["test"])
                if context:
                    failure["context"] = context

        all_failures.extend(failures)
        print_failed_tests(failures, args.detailed)

    # Summary
    if all_failures:
        print("\n" + "=" * 80)
        print(f"Total failures across all jobs: {len(all_failures)}")
        print("=" * 80)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
