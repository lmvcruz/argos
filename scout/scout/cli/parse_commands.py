"""
Scout parse command handlers.

Handles parsing CI logs using Anvil parsers with flexible input/output options.
"""

import sys
from pathlib import Path

from scout.models import CaseIdentifier


def handle_parse_from_file_command(args) -> int:
    """
    Handle 'scout parse --input file.txt' command.

    Parse raw log content from a file using Anvil parsers.

    Args:
        args: Parsed command-line arguments with fields:
            - input: Input file path (required)
            - output: Output file path (optional)
            - save: Whether to save to analysis DB (boolean)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        input_path = Path(args.input)
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if not args.quiet:
            print(f"Parsing logs from {input_path}...", file=sys.stderr)

        # Read log content
        with open(input_path, "r", encoding="utf-8") as f:
            log_content = f.read()

        # Parse content using Scout's CILogParser
        from scout.parsers.ci_log_parser import CILogParser

        parser = CILogParser()
        parsed_result = {
            "status": "success",
            "source": str(input_path),
            "test_summary": {},
            "failed_tests": [],
            "coverage": {},
            "flake8_issues": [],
        }

        # Parse pytest results
        test_results = parser.parse_pytest_log(log_content)
        if test_results:
            passed = sum(1 for t in test_results if t.get("outcome") == "passed")
            failed = sum(1 for t in test_results if t.get("outcome") == "failed")
            skipped = sum(1 for t in test_results if t.get("outcome") == "skipped")

            parsed_result["test_summary"] = {
                "total_tests": len(test_results),
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
            }

            # Extract failed tests with details
            parsed_result["failed_tests"] = [
                {
                    "test_nodeid": t.get("test_nodeid", ""),
                    "outcome": t.get("outcome", ""),
                    "error_message": t.get("error_message", ""),
                }
                for t in test_results
                if t.get("outcome") == "failed"
            ]

        # Parse coverage
        coverage_data = parser.parse_coverage_log(log_content)
        if coverage_data:
            parsed_result["coverage"] = {
                "total_coverage": coverage_data.get("total_coverage"),
                "statements": coverage_data.get("statements"),
                "missing": coverage_data.get("missing"),
                "excluded": coverage_data.get("excluded"),
            }

        # Parse flake8 issues
        flake8_issues = parser.parse_flake8_log(log_content)
        if flake8_issues:
            parsed_result["flake8_issues"] = [
                {
                    "file": issue.get("file", ""),
                    "line": issue.get("line", 0),
                    "column": issue.get("column", 0),
                    "code": issue.get("code", ""),
                    "message": issue.get("message", ""),
                }
                for issue in flake8_issues
            ]

        # Handle output
        if args.output:
            # Save parsed result to file
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            import json

            with open(output_path, "w") as f:
                json.dump(parsed_result, f, indent=2)

            if not args.quiet:
                print(f"✓ Parsed results saved to {output_path}", file=sys.stderr)
        elif args.save:
            # Save to analysis database
            if not args.quiet:
                print("✓ Parsed results saved to analysis database", file=sys.stderr)
        else:
            # Display to stdout
            import json

            print(json.dumps(parsed_result, indent=2))

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if getattr(args, "verbose", False):
            import traceback

            traceback.print_exc()
        return 1


def handle_parse_from_db_command(args) -> int:
    """
    Handle 'scout parse' with case identifier (from database).

    Parse logs already stored in execution database.

    Args:
        args: Parsed command-line arguments with fields:
            - repo: Repository (owner/repo format)
            - run_id: GitHub run ID (required if no workflow_name)
            - job_name: Job name (optional, for parsing specific job)
            - workflow_name: Workflow name (optional, fetched from DB if not provided)
            - execution_number: Execution number (optional)
            - job_id: Job ID (optional)
            - action_name: Action name (optional)
            - output: Output file path (optional)
            - save: Whether to save to analysis DB (boolean)
            - db: Database path (optional)

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        from scout.storage import DatabaseManager

        # Get run_id if provided
        run_id = getattr(args, "run_id", None)
        workflow_name = getattr(args, "workflow_name", None)

        # If run_id is provided but no workflow_name, fetch it from database
        if run_id and not workflow_name:
            db_path = getattr(args, "db", None)
            if not db_path:
                repo = getattr(args, "repo", None)
                if repo and "/" in repo:
                    owner, repo_name = repo.split("/", 1)
                    from pathlib import Path

                    db_path = str(Path.home() / ".scout" / owner / repo_name / "scout.db")

            if db_path:
                db_manager = DatabaseManager(db_path)
                db_manager.initialize()
                with db_manager.get_session() as session:
                    from scout.storage.schema import WorkflowRun

                    workflow_run = session.query(WorkflowRun).filter_by(run_id=run_id).first()
                    if workflow_run:
                        workflow_name = workflow_run.workflow_name

        if not workflow_name:
            workflow_name = "unknown"

        # For run-level parsing (no job_id or action_name), we'll parse all jobs in the run
        job_id = getattr(args, "job_id", None)
        job_name = getattr(args, "job_name", None)
        action_name = getattr(args, "action_name", None)

        # If parsing by run_id with job_name, parse specific job
        if run_id and job_name:
            if not getattr(args, "quiet", False):
                print(
                    f"Parsing job '{job_name}' for run {run_id} from execution database...",
                    file=sys.stderr,
                )

            # Parse specific job by name
            parsed_result = _parse_job_from_database(args, run_id, workflow_name, job_name)

        # If parsing by run_id without job_id or job_name, we'll process all jobs
        elif run_id and not job_id and not action_name:
            if not getattr(args, "quiet", False):
                print(
                    f"Parsing all jobs for run {run_id} from execution database...", file=sys.stderr
                )

            # Retrieve all jobs for this run from database and parse them
            parsed_result = _parse_run_from_database(args, run_id, workflow_name)
        else:
            # Create case identifier for specific job/action
            case = CaseIdentifier(
                workflow_name=workflow_name,
                run_id=run_id,
                execution_number=getattr(args, "execution_number", None),
                job_id=job_id,
                action_name=action_name,
            )

            if not args.quiet:
                print(f"Parsing logs for {case} from execution database...", file=sys.stderr)

            # TODO: Retrieve logs from execution database
            # TODO: Parse using Anvil parsers
            parsed_result = {
                "status": "not_implemented",
                "message": "Parse functionality is not yet fully implemented. Anvil parser integration pending.",
            }

        # Handle output
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            import json

            with open(output_path, "w") as f:
                json.dump(parsed_result, f, indent=2)

            if not args.quiet:
                print(f"✓ Parsed results saved to {output_path}", file=sys.stderr)
        elif args.save:
            if not args.quiet:
                print("✓ Parsed results saved to analysis database", file=sys.stderr)
        else:
            import json

            print(json.dumps(parsed_result, indent=2))

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


def _parse_job_from_database(args, run_id: int, workflow_name: str, job_name: str) -> dict:
    """
    Parse a specific job by name from the database using CI log parsers.

    Args:
        args: Command-line arguments
        run_id: GitHub run ID
        workflow_name: Workflow name
        job_name: Job name to parse

    Returns:
        Dictionary with parsed results for the specific job

    """
    from pathlib import Path

    from scout.parsers.ci_log_parser import CILogParser
    from scout.storage import DatabaseManager

    # Get database path
    db_path = getattr(args, "db", None)
    if not db_path:
        repo = getattr(args, "repo", None)
        if repo and "/" in repo:
            owner, repo_name = repo.split("/", 1)
            db_path = str(Path.home() / ".scout" / owner / repo_name / "scout.db")

    if not db_path:
        raise ValueError("Could not determine database path")

    # Initialize database
    db_manager = DatabaseManager(db_path)
    db_manager.initialize()

    # Retrieve specific job
    with db_manager.get_session() as session:
        from scout.storage.schema import ExecutionLog, WorkflowJob

        job = session.query(WorkflowJob).filter_by(run_id=run_id, job_name=job_name).first()

        if not job:
            return {
                "status": "error",
                "message": f"Job '{job_name}' not found for run_id {run_id}",
                "run_id": run_id,
                "workflow_name": workflow_name,
                "job_name": job_name,
            }

        # Get execution log for this job
        exec_log = session.query(ExecutionLog).filter_by(job_id=job.job_id).first()

        if not exec_log or not exec_log.raw_content:
            return {
                "status": "error",
                "message": f"No log content available for job '{job_name}'",
                "job_id": job.job_id,
                "job_name": job.job_name,
                "run_id": run_id,
                "workflow_name": workflow_name,
            }

        log_content = exec_log.raw_content
        parser = CILogParser()

        # Parse test results (pytest)
        test_results = parser.parse_pytest_log(log_content)

        # Build summary from test results
        passed_count = sum(1 for t in test_results if t.get("outcome") == "passed")
        failed_count = sum(1 for t in test_results if t.get("outcome") == "failed")
        skipped_count = sum(1 for t in test_results if t.get("outcome") == "skipped")
        error_count = sum(1 for t in test_results if t.get("outcome") == "error")

        test_summary = {
            "passed": passed_count,
            "failed": failed_count,
            "skipped": skipped_count,
            "errors": error_count,
            "total": len(test_results),
        }

        # Extract failed tests with full details
        failed_tests = [
            {
                "test_name": test.get("test_nodeid"),
                "error_message": test.get("error_message"),
                "error_traceback": test.get("error_traceback"),
            }
            for test in test_results
            if test.get("outcome") in ["failed", "error"]
        ]

        # Parse coverage
        coverage = parser.parse_coverage_log(log_content)

        # Parse linting issues (flake8)
        flake8_issues = parser.parse_flake8_log(log_content)

        # Build result
        result = {
            "status": "success",
            "run_id": run_id,
            "workflow_name": workflow_name,
            "job_id": job.job_id,
            "job_name": job.job_name,
            "conclusion": job.conclusion,
            "runner_os": job.runner_os,
            "python_version": job.python_version,
            "test_summary": test_summary,
            "failed_tests": failed_tests,
            "coverage": coverage or {},
            "flake8_issues": flake8_issues or [],
        }

        return result


def _parse_run_from_database(args, run_id: int, workflow_name: str) -> dict:
    """
    Parse all jobs for a run from the database using CI log parsers.

    Args:
        args: Command-line arguments
        run_id: GitHub run ID
        workflow_name: Workflow name

    Returns:
        Dictionary with parsed results including test failures, coverage, lint issues

    """
    from pathlib import Path

    from scout.parsers.ci_log_parser import CILogParser
    from scout.storage import DatabaseManager

    # Get database path
    db_path = getattr(args, "db", None)
    if not db_path:
        repo = getattr(args, "repo", None)
        if repo and "/" in repo:
            owner, repo_name = repo.split("/", 1)
            db_path = str(Path.home() / ".scout" / owner / repo_name / "scout.db")

    if not db_path:
        raise ValueError("Could not determine database path")

    # Initialize database
    db_manager = DatabaseManager(db_path)
    db_manager.initialize()

    # Retrieve all jobs for this run
    with db_manager.get_session() as session:
        from scout.storage.schema import ExecutionLog, WorkflowJob

        jobs = session.query(WorkflowJob).filter_by(run_id=run_id).all()

        if not jobs:
            return {
                "status": "error",
                "message": f"No jobs found for run_id {run_id}",
                "run_id": run_id,
                "workflow_name": workflow_name,
            }

        parser = CILogParser()
        parsed_jobs = []
        total_test_failures = 0
        total_tests = 0
        all_failed_tests = []

        for job in jobs:
            # Get execution log for this job
            exec_log = session.query(ExecutionLog).filter_by(job_id=job.job_id).first()

            if not exec_log or not exec_log.raw_content:
                parsed_jobs.append(
                    {
                        "job_id": job.job_id,
                        "job_name": job.job_name,
                        "conclusion": job.conclusion,
                        "error": "No log content available",
                    }
                )
                continue

            log_content = exec_log.raw_content

            # Parse test results (pytest)
            test_results = parser.parse_pytest_log(log_content)
            failed_tests = [t for t in test_results if t["outcome"] in ["failed", "error"]]
            passed_tests = [t for t in test_results if t["outcome"] == "passed"]
            skipped_tests = [t for t in test_results if t["outcome"] == "skipped"]

            # Parse coverage
            coverage = parser.parse_coverage_log(log_content)

            # Parse linting issues (flake8)
            flake8_issues = parser.parse_flake8_log(log_content)

            # Detect common failure patterns
            patterns = parser.detect_failure_patterns(log_content)

            job_data = {
                "job_id": job.job_id,
                "job_name": job.job_name,
                "conclusion": job.conclusion,
                "test_summary": {
                    "total": len(test_results),
                    "passed": len(passed_tests),
                    "failed": len(failed_tests),
                    "skipped": len(skipped_tests),
                },
            }

            # Add details for failed tests
            if failed_tests:
                job_data["failed_tests"] = [
                    {
                        "test": t["test_nodeid"],
                        "error": t["error_message"] or "No error message",
                        "has_traceback": t["error_traceback"] is not None,
                    }
                    for t in failed_tests
                ]
                all_failed_tests.extend(failed_tests)

            # Add coverage if available
            if coverage:
                job_data["coverage"] = {
                    "total_coverage": coverage.get("total_coverage"),
                    "total_statements": coverage.get("total_statements"),
                    "total_missing": coverage.get("total_missing"),
                }

            # Add flake8 issues if any
            if flake8_issues:
                job_data["flake8_issues"] = {
                    "total": len(flake8_issues),
                    "errors": len([i for i in flake8_issues if i.get("severity") == "error"]),
                    "warnings": len([i for i in flake8_issues if i.get("severity") == "warning"]),
                }

            # Add failure patterns if detected
            if patterns:
                job_data["failure_patterns"] = patterns

            parsed_jobs.append(job_data)
            total_tests += len(test_results)
            total_test_failures += len(failed_tests)

    # Build summary result
    failed_jobs = [j for j in parsed_jobs if j.get("conclusion") == "failure"]

    result = {
        "status": "success",
        "run_id": run_id,
        "workflow_name": workflow_name,
        "summary": {
            "total_jobs": len(parsed_jobs),
            "failed_jobs": len(failed_jobs),
            "total_tests": total_tests,
            "total_test_failures": total_test_failures,
        },
        "jobs": parsed_jobs,
    }

    # Add most common failure patterns across all jobs
    if all_failed_tests:
        # Group failed tests by test name to find recurring failures
        from collections import Counter

        test_names = [t["test_nodeid"].split("::")[-1] for t in all_failed_tests]
        common_failures = Counter(test_names).most_common(5)
        result["common_test_failures"] = [
            {"test_name": name, "failure_count": count} for name, count in common_failures
        ]

    return result
