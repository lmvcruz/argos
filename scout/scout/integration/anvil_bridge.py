"""
Bridge between Scout (CI data) and Anvil (validation history).

This module syncs CI test results from Scout's database to Anvil's
validation history database, enabling local vs CI comparisons and
CI-specific failure analysis.
"""

import sys
from datetime import datetime
from typing import Dict, List, Optional

from scout.storage import DatabaseManager
from scout.storage.schema import WorkflowJob, WorkflowRun, WorkflowTestResult


class AnvilBridge:
    """
    Bridge between Scout (CI data) and Anvil (validation history).

    Syncs CI test results to Anvil's database format, enabling:
    - Local vs CI test result comparison
    - CI-specific failure identification
    - Cross-platform test analysis
    - Historical CI trends
    """

    def __init__(self, scout_db_path: str, anvil_db_path: str):
        """
        Initialize the Scout-Anvil bridge.

        Args:
            scout_db_path: Path to Scout's SQLite database
            anvil_db_path: Path to Anvil's SQLite database
        """
        # Import Anvil's database here to avoid hard dependency
        try:
            from anvil.storage.statistics_database import StatisticsDatabase
        except ImportError:
            print(
                "Error: Anvil not installed. Install with: pip install -e path/to/anvil",
                file=sys.stderr,
            )
            raise

        self.scout_db = DatabaseManager(scout_db_path)
        self.scout_db.initialize()

        self.anvil_db = StatisticsDatabase(anvil_db_path)

    def sync_ci_run_to_anvil(self, run_id: int, verbose: bool = False) -> Dict[str, int]:
        """
        Sync a CI workflow run to Anvil's validation history.

        Converts Scout's WorkflowRun and WorkflowTestResults to Anvil's
        ValidationRun and TestCaseRecord format.

        Args:
            run_id: GitHub Actions run ID to sync
            verbose: Print progress information

        Returns:
            Dictionary with sync statistics:
            {
                "validation_run_id": Anvil database ID,
                "tests_synced": Number of test results synced,
                "jobs_synced": Number of jobs processed
            }

        Raises:
            ValueError: If run_id not found in Scout database
        """
        from anvil.storage.statistics_database import TestCaseRecord, ValidationRun

        session = self.scout_db.get_session()

        try:
            # Fetch the workflow run
            workflow_run = session.query(WorkflowRun).filter_by(run_id=run_id).first()
            if not workflow_run:
                raise ValueError(f"Workflow run {run_id} not found in Scout database")

            if verbose:
                print(f"Syncing run {run_id}: {workflow_run.workflow_name}")

            # Create Anvil ValidationRun
            validation_run = ValidationRun(
                timestamp=workflow_run.started_at or datetime.now(),
                git_commit=workflow_run.commit_sha,
                git_branch=workflow_run.branch,
                incremental=False,  # CI runs are always full
                passed=(workflow_run.conclusion == "success"),
                duration_seconds=workflow_run.duration_seconds or 0,
            )

            # Insert into Anvil database
            anvil_run_id = self.anvil_db.insert_validation_run(validation_run)

            if verbose:
                print(f"  Created Anvil validation run: {anvil_run_id}")

            # Fetch all test results for this run's jobs
            jobs = session.query(WorkflowJob).filter_by(run_id=run_id).all()

            tests_synced = 0
            jobs_synced = 0

            for job in jobs:
                test_results = session.query(WorkflowTestResult).filter_by(job_id=job.job_id).all()

                if not test_results:
                    continue

                jobs_synced += 1

                if verbose:
                    print(f"  Processing job {job.job_name}: {len(test_results)} tests")

                for test_result in test_results:
                    # Extract test suite and name from nodeid
                    # Format: path/to/test_file.py::TestClass::test_method
                    # or: path/to/test_file.py::test_function
                    parts = test_result.test_nodeid.split("::")
                    if len(parts) >= 2:
                        test_suite = parts[-2] if len(parts) == 3 else parts[0]
                        test_name = parts[-1]
                    else:
                        test_suite = "unknown"
                        test_name = test_result.test_nodeid

                    # Create Anvil TestCaseRecord with platform info in test_suite
                    platform_suite = f"{test_suite} [{job.runner_os or 'unknown'}]"

                    test_record = TestCaseRecord(
                        run_id=anvil_run_id,
                        test_name=test_name,
                        test_suite=platform_suite,
                        passed=(test_result.outcome == "passed"),
                        skipped=(test_result.outcome == "skipped"),
                        duration_seconds=test_result.duration or 0.0,
                        failure_message=test_result.error_message,
                    )

                    self.anvil_db.insert_test_case_record(test_record)
                    tests_synced += 1

            if verbose:
                print(f"✓ Synced {tests_synced} tests from {jobs_synced} jobs")

            return {
                "validation_run_id": anvil_run_id,
                "tests_synced": tests_synced,
                "jobs_synced": jobs_synced,
            }

        finally:
            session.close()

    def sync_recent_runs(
        self, limit: int = 10, workflow_name: Optional[str] = None, verbose: bool = False
    ) -> List[Dict[str, int]]:
        """
        Sync recent CI runs to Anvil.

        Args:
            limit: Maximum number of runs to sync
            workflow_name: Filter by workflow name (None = all workflows)
            verbose: Print progress information

        Returns:
            List of sync statistics for each run
        """
        session = self.scout_db.get_session()

        try:
            query = session.query(WorkflowRun).order_by(WorkflowRun.started_at.desc())

            if workflow_name:
                query = query.filter_by(workflow_name=workflow_name)

            runs = query.limit(limit).all()

            if verbose:
                print(f"Syncing {len(runs)} workflow runs to Anvil...")

            results = []
            for run in runs:
                try:
                    result = self.sync_ci_run_to_anvil(run.run_id, verbose=verbose)
                    results.append(result)
                except Exception as e:
                    if verbose:
                        print(f"  Error syncing run {run.run_id}: {e}")
                    results.append({"error": str(e), "run_id": run.run_id})

            return results

        finally:
            session.close()

    def compare_local_vs_ci(self, anvil_run_id: int, ci_run_id: int) -> Dict[str, List[str]]:
        """
        Compare local Anvil run with CI run.

        Identifies tests that:
        - Pass locally but fail in CI
        - Fail locally but pass in CI
        - Only exist in one environment

        Args:
            anvil_run_id: Anvil ValidationRun ID (local execution)
            ci_run_id: Scout WorkflowRun ID (CI execution)

        Returns:
            Dictionary with comparison results:
            {
                "pass_local_fail_ci": List of test names,
                "fail_local_pass_ci": List of test names,
                "only_local": List of test names,
                "only_ci": List of test names
            }
        """
        # Get local test results from Anvil
        local_tests = self.anvil_db.query_test_cases_for_run(anvil_run_id)
        local_map = {test.test_name: test for test in local_tests}

        # Get CI test results from Scout
        session = self.scout_db.get_session()
        try:
            jobs = session.query(WorkflowJob).filter_by(run_id=ci_run_id).all()

            ci_map = {}
            for job in jobs:
                test_results = session.query(WorkflowTestResult).filter_by(job_id=job.job_id).all()
                for test in test_results:
                    # Extract test name from nodeid
                    parts = test.test_nodeid.split("::")
                    test_name = parts[-1] if parts else test.test_nodeid
                    ci_map[test_name] = test

        finally:
            session.close()

        # Compare results
        pass_local_fail_ci = []
        fail_local_pass_ci = []
        only_local = []
        only_ci = []

        # Check local tests
        for name, local_test in local_map.items():
            if name in ci_map:
                ci_test = ci_map[name]
                local_passed = local_test.passed
                ci_passed = ci_test.outcome == "passed"

                if local_passed and not ci_passed:
                    pass_local_fail_ci.append(name)
                elif not local_passed and ci_passed:
                    fail_local_pass_ci.append(name)
            else:
                only_local.append(name)

        # Check for CI-only tests
        for name in ci_map:
            if name not in local_map:
                only_ci.append(name)

        return {
            "pass_local_fail_ci": sorted(pass_local_fail_ci),
            "fail_local_pass_ci": sorted(fail_local_pass_ci),
            "only_local": sorted(only_local),
            "only_ci": sorted(only_ci),
        }

    def identify_ci_specific_failures(
        self, days: int = 30, min_failures: int = 2
    ) -> List[Dict[str, any]]:
        """
        Identify tests that consistently fail in CI but not locally.

        Args:
            days: Look back this many days
            min_failures: Minimum CI failures to report

        Returns:
            List of dictionaries with test failure information:
            [{
                "test_name": str,
                "ci_failures": int,
                "platforms": List[str],
                "last_failure": datetime
            }]
        """
        session = self.scout_db.get_session()

        try:
            from datetime import timedelta

            cutoff_date = datetime.now() - timedelta(days=days)

            # Get all CI test failures in time window
            query = (
                session.query(WorkflowTestResult)
                .filter(WorkflowTestResult.outcome == "failed")
                .filter(WorkflowTestResult.timestamp >= cutoff_date)
            )

            failures = query.all()

            # Group by test name
            failure_map = {}
            for failure in failures:
                parts = failure.test_nodeid.split("::")
                test_name = parts[-1] if parts else failure.test_nodeid

                if test_name not in failure_map:
                    failure_map[test_name] = {
                        "test_name": test_name,
                        "ci_failures": 0,
                        "platforms": set(),
                        "last_failure": failure.timestamp,
                    }

                failure_map[test_name]["ci_failures"] += 1
                if failure.runner_os:
                    failure_map[test_name]["platforms"].add(failure.runner_os)
                if failure.timestamp > failure_map[test_name]["last_failure"]:
                    failure_map[test_name]["last_failure"] = failure.timestamp

            # Filter by minimum failures and convert sets to lists
            result = []
            for test_info in failure_map.values():
                if test_info["ci_failures"] >= min_failures:
                    test_info["platforms"] = sorted(list(test_info["platforms"]))
                    result.append(test_info)

            # Sort by failure count descending
            result.sort(key=lambda x: x["ci_failures"], reverse=True)

            return result

        finally:
            session.close()

    def close(self):
        """Close database connections."""
        if hasattr(self, "scout_db"):
            # Scout's DatabaseManager doesn't have a close method
            pass
        if hasattr(self, "anvil_db") and hasattr(self.anvil_db, "connection"):
            self.anvil_db.connection.close()
