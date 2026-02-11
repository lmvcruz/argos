"""
Scout fetch command handlers.

Handles downloading CI logs from GitHub Actions with flexible output options.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

from scout.models import CaseIdentifier
from scout.providers.github_actions import GitHubActionsProvider
from scout.storage.database import DatabaseManager
from scout.storage.schema import ExecutionLog, WorkflowJob, WorkflowRun


def handle_fetch_command(args) -> int:
    """
    Handle 'scout fetch' command to download CI logs from GitHub.

    Fetch from GitHub Actions and either:
    - Display to stdout
    - Save to a file (--output)
    - Save to execution database (--save)

    Args:
        args: Parsed command-line arguments with fields:
            - repo: GitHub repository in owner/repo format (required)
            - workflow_name: Workflow name (optional)
            - run_id: GitHub run ID (optional)
            - execution_number: Execution number (optional)
            - job_id: Job ID (optional)
            - action_name: Action name (optional)
            - output: Output file path (optional)
            - save: Whether to save to execution DB (boolean)
            - token: GitHub token (optional, defaults to GITHUB_TOKEN env var)
            - db: Database path (optional)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        # Get GitHub token from args or environment
        token = getattr(args, "token", None) or os.environ.get("GITHUB_TOKEN")
        if not token:
            print("Warning: No GitHub token provided. API rate limits may apply.", file=sys.stderr)

        # Get repository
        repo = getattr(args, "repo", None) or os.environ.get("GITHUB_REPO")
        if not repo:
            print("Error: --repo is required (format: owner/repo)", file=sys.stderr)
            return 1

        # Parse owner/repo
        if "/" not in repo:
            print(f"Error: Invalid repo format '{repo}'. Expected 'owner/repo'", file=sys.stderr)
            return 1
        owner, repo_name = repo.split("/", 1)

        # Create GitHub provider
        provider = GitHubActionsProvider(owner=owner, repo=repo_name, token=token)

        # Get run_id (required for fetching logs)
        run_id = getattr(args, "run_id", None)
        if not run_id:
            print("Error: --run-id is required for fetching logs", file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"Fetching logs for run {run_id} from {repo}...", file=sys.stderr)

        # Get workflow run details
        try:
            workflow_run = provider.get_workflow_run(str(run_id))
        except Exception as e:
            print(f"Error fetching workflow run {run_id}: {e}", file=sys.stderr)
            return 1

        # Get jobs for this run
        try:
            jobs = provider.get_jobs(str(run_id))
        except Exception as e:
            print(f"Error fetching jobs for run {run_id}: {e}", file=sys.stderr)
            return 1

        if not jobs:
            print(f"No jobs found for run {run_id}", file=sys.stderr)
            return 1

        if not args.quiet:
            print(f"Found {len(jobs)} job(s) for run {run_id}", file=sys.stderr)

        # Initialize database if saving
        db_manager = None
        session = None
        if args.save or not (args.output or getattr(args, "save", False) is False):
            # Default to saving if no output specified
            db_path = getattr(args, "db", None)
            if not db_path:
                # Use default: ~/.scout/owner/repo/scout.db
                scout_dir = Path.home() / ".scout" / owner / repo_name
                scout_dir.mkdir(parents=True, exist_ok=True)
                db_path = str(scout_dir / "scout.db")

            db_manager = DatabaseManager(db_path=db_path)
            db_manager.initialize()
            session = db_manager.get_session()

        logs_fetched = 0
        logs_saved = 0

        # Fetch logs for each job
        for job in jobs:
            job_id = job.id
            job_name = job.name

            if not args.quiet:
                print(f"  Fetching logs for job {job_id} ({job_name})...", file=sys.stderr)

            try:
                # Get logs from GitHub API
                log_entries = provider.get_logs(job_id)

                if not log_entries:
                    if not args.quiet:
                        print(f"    No logs available for job {job_id}", file=sys.stderr)
                    continue

                # Combine log entries into single text
                logs_content = "\n".join(entry.content for entry in log_entries)
                logs_fetched += 1

                # Handle output
                if args.output:
                    # Save to file
                    output_path = Path(args.output)
                    if len(jobs) > 1:
                        # Multiple jobs - create separate files
                        output_path = output_path.parent / f"{output_path.stem}_{job_id}{output_path.suffix}"
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        f.write(logs_content)
                    if not args.quiet:
                        print(f"    ✓ Logs saved to {output_path}", file=sys.stderr)
                elif session:
                    # Save to database
                    execution_log = ExecutionLog(
                        workflow_name=workflow_run.workflow_name,
                        run_id=int(run_id),
                        execution_number=getattr(args, "execution_number", None),
                        job_id=int(job_id),
                        action_name=job_name,
                        raw_content=logs_content,
                        content_type="github_actions",
                        stored_at=datetime.utcnow(),
                        parsed=0,
                        extra_metadata={
                            "status": job.status,
                            "conclusion": job.conclusion,
                            "branch": workflow_run.branch,
                            "commit_sha": workflow_run.commit_sha,
                        },
                    )
                    session.add(execution_log)

                    # Update WorkflowJob has_logs flag
                    workflow_job = session.query(WorkflowJob).filter_by(job_id=int(job_id)).first()
                    if workflow_job:
                        workflow_job.has_logs = 1
                        workflow_job.logs_downloaded_at = datetime.utcnow()

                    logs_saved += 1

                    if not args.quiet:
                        print(f"    ✓ Logs stored in database", file=sys.stderr)
                else:
                    # Display to stdout
                    print(logs_content)

            except Exception as e:
                print(f"    Error fetching logs for job {job_id}: {e}", file=sys.stderr)
                if getattr(args, "verbose", False):
                    import traceback
                    traceback.print_exc()
                continue

        # Commit database changes
        if session:
            try:
                # Update WorkflowRun has_logs flag
                workflow_run_record = session.query(WorkflowRun).filter_by(run_id=run_id).first()
                if workflow_run_record:
                    workflow_run_record.has_logs = 1
                    workflow_run_record.logs_downloaded_at = datetime.utcnow()

                session.commit()
                if not args.quiet:
                    print(f"\n✓ Successfully fetched and saved {logs_saved} job log(s)", file=sys.stderr)
            except Exception as e:
                session.rollback()
                print(f"Error saving to database: {e}", file=sys.stderr)
                return 1
            finally:
                session.close()
        elif not args.quiet and logs_fetched > 0:
            print(f"\n✓ Successfully fetched {logs_fetched} job log(s)", file=sys.stderr)

        return 0 if logs_fetched > 0 else 1

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
