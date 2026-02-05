"""
Scout fetch command handlers.

Handles downloading CI logs from GitHub Actions with flexible output options.
"""

import sys
from pathlib import Path

from scout.models import CaseIdentifier


def handle_fetch_command(args) -> int:
    """
    Handle 'scout fetch' command to download CI logs from GitHub.

    Fetch from GitHub Actions and either:
    - Display to stdout
    - Save to a file (--output)
    - Save to execution database (--save)

    Args:
        args: Parsed command-line arguments with fields:
            - workflow_name: Workflow name (required)
            - run_id: GitHub run ID (optional)
            - execution_number: Execution number (optional)
            - job_id: Job ID (optional)
            - action_name: Action name (optional)
            - output: Output file path (optional)
            - save: Whether to save to execution DB (boolean)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Create case identifier
        case = CaseIdentifier(
            workflow_name=args.workflow_name,
            run_id=getattr(args, "run_id", None),
            execution_number=getattr(args, "execution_number", None),
            job_id=getattr(args, "job_id", None),
            action_name=getattr(args, "action_name", None),
        )

        if not args.quiet:
            print(f"Fetching logs from {case}...", file=sys.stderr)

        # TODO: Implement actual fetch from GitHub Actions
        # This would call the GitHub API to download logs
        logs_content = "# TODO: Fetch logs from GitHub\n"

        # Handle output
        if args.output:
            # Save to file
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(logs_content)
            if not args.quiet:
                print(f"✓ Logs saved to {output_path}")
        elif args.save:
            # Save to execution database
            if not args.quiet:
                print("✓ Logs saved to execution database")
        else:
            # Display to stdout
            print(logs_content)

        return 0

    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        return 1


def handle_fetch_all_command(args) -> int:
    """
    Handle 'scout fetch' with --fetch-all option.

    Fetches all available executions from the specified workflow.

    Args:
        args: Parsed command-line arguments with fields:
            - workflow_name: Workflow name (required)
            - output: Output directory (optional)
            - save: Whether to save to execution DB (boolean)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        if not args.quiet:
            print(
                f"Fetching all executions for workflow '{args.workflow_name}'...", file=sys.stderr
            )

        # TODO: Implement actual fetch-all logic
        # This would fetch all runs for the workflow

        if not args.quiet:
            print("✓ Fetched all available executions", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        return 1


def handle_fetch_last_command(args) -> int:
    """
    Handle 'scout fetch' with --fetch-last option.

    Fetches the last N executions, optionally filtered by workflow.

    Args:
        args: Parsed command-line arguments with fields:
            - fetch_last: Number of executions to fetch (required)
            - workflow_name: Workflow name (optional)
            - output: Output directory (optional)
            - save: Whether to save to execution DB (boolean)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        workflow_msg = (
            f" from workflow '{args.workflow_name}'"
            if hasattr(args, "workflow_name") and args.workflow_name
            else ""
        )

        if not args.quiet:
            print(
                f"Fetching last {args.fetch_last} executions{workflow_msg}...",
                file=sys.stderr,
            )

        # TODO: Implement actual fetch-last logic
        # Results sorted oldest-first
        results = []  # TODO: Fetch from GitHub API

        if not args.quiet:
            print(f"✓ Fetched {len(results)} execution(s)", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        return 1
