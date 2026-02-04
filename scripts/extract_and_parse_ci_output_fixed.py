#!/usr/bin/env python
"""
Workflow to extract command output from GitHub Actions using Scout.

This script demonstrates the proper use of Scout component:
1. Scout: Fetch GitHub Actions execution logs
2. Scout: Extract specific command output (e.g., black check)
3. Save extracted output for Anvil validation

Usage:
    python extract_and_parse_ci_output.py 21606378341 62333994010 --command black --output output.txt
"""

import argparse
import os
import sys
from pathlib import Path

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from scout.log_retrieval import LogRetriever
from scout.providers.github_actions import GitHubActionsProvider


def extract_command_output(log_entries, command_marker: str) -> str:
    """
    Extract output for a specific command from log entries.

    Args:
        log_entries: List of LogEntry objects from Scout
        command_marker: Marker to identify the command output section (e.g., "Run black")

    Returns:
        Extracted command output (without timestamps)
    """
    output_lines = []
    found_group = False
    found_endgroup = False

    for entry in log_entries:
        content = entry.content

        # Look for the group marker for this command
        if not found_group and command_marker.lower() in content.lower() and '##[group]' in content:
            found_group = True
            continue

        # If we've found the group, look for the endgroup marker
        if found_group and not found_endgroup:
            if '##[endgroup]' in content:
                found_endgroup = True
                continue
            # Skip the command metadata lines before endgroup
            continue

        # After finding endgroup, collect output until the next group marker
        if found_endgroup:
            # Stop at the next group marker
            if content.startswith('##[') and 'group' in content.lower():
                break

            # Collect the output line
            output_lines.append(content)

    return '\n'.join(output_lines).strip()


def main():
    parser = argparse.ArgumentParser(
        description="Extract CI command output using Scout"
    )
    parser.add_argument("run_id", help="GitHub Actions run ID")
    parser.add_argument("job_id", help="GitHub Actions job ID")
    parser.add_argument(
        "--command",
        default="black",
        help="Command to extract output for (default: black)"
    )
    parser.add_argument("--output", help="Output file path")
    parser.add_argument(
        "--token", help="GitHub token (or set GITHUB_TOKEN env var)")
    parser.add_argument("--owner", default="lmvcruz", help="Repository owner")
    parser.add_argument("--repo", default="argos", help="Repository name")
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Get token from argument or environment
    token = args.token or os.getenv("GITHUB_TOKEN")
    if not token:
        print(
            "Error: GitHub token required. Set GITHUB_TOKEN env var or use --token",
            file=sys.stderr
        )
        return 1

    try:
        # Step 1: Use Scout to fetch the job log
        if args.verbose:
            print(
                f"[Scout] Fetching job {args.job_id} from run {args.run_id}...")

        provider = GitHubActionsProvider(
            owner=args.owner,
            repo=args.repo,
            token=token
        )
        retriever = LogRetriever(provider=provider)

        # Get the log for this specific job
        workflow_log = retriever.get_logs(
            run_id=args.run_id, job_id=args.job_id)

        if args.verbose:
            print(f"[Scout] ✓ Retrieved: {workflow_log.job_name}")
            print(f"        Raw size: {workflow_log.raw_size} bytes")
            print(f"        Entries: {len(workflow_log.entries)}")

        # Step 2: Extract command output
        if args.verbose:
            print(f"[Scout] Extracting {args.command.upper()} output...")

        command_marker = f"Run {args.command}"
        command_output = extract_command_output(
            workflow_log.entries, command_marker)

        if not command_output:
            print(
                f"Error: No output found for command '{args.command}'",
                file=sys.stderr
            )
            return 1

        if args.verbose:
            print(f"[Scout] ✓ Extracted {len(command_output)} bytes")

        # Step 3: Save to file or print
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(command_output, encoding='utf-8')
            if args.verbose:
                print(f"[Scout] ✓ Saved to {output_path}")
            else:
                print(f"Saved to {output_path}")
            return 0
        else:
            print(command_output)
            return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
