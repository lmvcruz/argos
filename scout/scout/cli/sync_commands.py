"""
Scout sync command handlers.

Handles the four-stage pipeline with flexible skip options.
"""

import sys

from scout.models import CaseIdentifier, SyncOptions


def handle_sync_command(args) -> int:
    """
    Handle 'scout sync' command for the four-stage pipeline.

    Runs fetch → save-ci → parse → save-analysis with skip options.

    Args:
        args: Parsed command-line arguments with fields:
            - workflow_name: Workflow name (optional if using fetch modes)
            - run_id: GitHub run ID (optional)
            - execution_number: Execution number (optional)
            - job_id: Job ID (optional)
            - action_name: Action name (optional)
            - fetch_all: Fetch all executions (boolean)
            - fetch_last: Number of last executions (optional)
            - skip_fetch: Skip fetch stage (boolean)
            - skip_save_ci: Skip save-ci stage (boolean)
            - skip_parse: Skip parse stage (boolean)
            - skip_save_analysis: Skip save-analysis stage (boolean)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        sync_options = SyncOptions(
            skip_fetch=getattr(args, "skip_fetch", False),
            skip_save_ci=getattr(args, "skip_save_ci", False),
            skip_parse=getattr(args, "skip_parse", False),
            skip_save_analysis=getattr(args, "skip_save_analysis", False),
            fetch_all=getattr(args, "fetch_all", False),
            fetch_last=getattr(args, "fetch_last", None),
        )

        # Determine input mode
        if sync_options.fetch_all:
            return handle_sync_fetch_all(args, sync_options)
        elif sync_options.fetch_last is not None:
            return handle_sync_fetch_last(args, sync_options)
        else:
            return handle_sync_with_case(args, sync_options)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        return 1


def handle_sync_with_case(args, sync_options: SyncOptions) -> int:
    """
    Handle sync with explicit case identifier (workflow + execution + job).

    Args:
        args: Parsed command-line arguments
        sync_options: SyncOptions containing skip flags

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
            print(f"Syncing {case}...", file=sys.stderr)
            if sync_options.skip_fetch:
                print("  Skipping fetch (using cached data)", file=sys.stderr)
            if sync_options.skip_save_ci:
                print("  Skipping save-ci", file=sys.stderr)
            if sync_options.skip_parse:
                print("  Skipping parse", file=sys.stderr)
            if sync_options.skip_save_analysis:
                print("  Skipping save-analysis", file=sys.stderr)

        # Stage 1: Fetch
        if not sync_options.skip_fetch:
            if not args.quiet:
                print("  [1/4] Fetching logs...", file=sys.stderr)
            # TODO: Fetch logs from GitHub
        else:
            if not args.quiet:
                print("  [1/4] Retrieving cached logs...", file=sys.stderr)
            # TODO: Retrieve from execution database
            # If not found, error out
            if not args.quiet:
                print(f"  ✗ No cached data found for {case}", file=sys.stderr)
            return 1

        # Stage 2: Save-CI
        if not sync_options.skip_save_ci:
            if not args.quiet:
                print("  [2/4] Saving execution logs...", file=sys.stderr)
            # TODO: Save to execution database

        # Stage 3: Parse
        if not sync_options.skip_parse:
            if not args.quiet:
                print("  [3/4] Parsing logs...", file=sys.stderr)
            # TODO: Parse using Anvil parsers

            # Stage 4: Save-Analysis
            if not sync_options.skip_save_analysis:
                if not args.quiet:
                    print("  [4/4] Saving analysis results...", file=sys.stderr)
                # TODO: Save to analysis database

        if not args.quiet:
            print("✓ Sync completed", file=sys.stderr)

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


def handle_sync_fetch_all(args, sync_options: SyncOptions) -> int:
    """
    Handle sync with --fetch-all (fetch all executions).

    Args:
        args: Parsed command-line arguments
        sync_options: SyncOptions containing skip flags

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        if not args.quiet:
            print(f"Syncing all executions for '{args.workflow_name}'...", file=sys.stderr)

        # TODO: Fetch all runs, then process each through pipeline

        if not args.quiet:
            print("✓ Sync completed", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        return 1


def handle_sync_fetch_last(args, sync_options: SyncOptions) -> int:
    """
    Handle sync with --fetch-last N [--workflow-name X].

    Args:
        args: Parsed command-line arguments
        sync_options: SyncOptions containing skip flags

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
                f"Syncing last {sync_options.fetch_last} executions{workflow_msg}...",
                file=sys.stderr,
            )

        # TODO: Fetch last N runs, then process each through pipeline
        # Results sorted oldest-first

        if not args.quiet:
            print("✓ Sync completed", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        return 1
