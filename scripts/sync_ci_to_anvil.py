"""
Proof of Concept: Parse CI test results and store in Anvil database.

This script demonstrates the Scout → Anvil → Lens integration for CI test data.
"""

import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

# Add project roots to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "scout"))
sys.path.insert(0, str(project_root / "anvil"))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✓ Loaded environment from {env_file}")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("   Falling back to system environment variables only.")

from scout.providers.github_actions import GitHubActionsProvider
from anvil.storage.execution_schema import ExecutionDatabase, ExecutionHistory


class CITestResultParser:
    """Parse pytest results from CI logs."""

    @staticmethod
    def parse_pytest_output(log_content: str) -> List[Dict]:
        """
        Parse pytest output from CI logs.

        Looks for patterns like:
        - forge/tests/test_models.py::test_func PASSED [1.23s]
        - forge/tests/test_models.py::test_func FAILED [1.23s]
        """
        results = []

        # Pattern: path/to/file.py::test_name STATUS [duration]
        pattern = r'([\w/]+\.py::\S+)\s+(PASSED|FAILED|SKIPPED|ERROR)(?:\s+\[(\d+\.?\d*)s\])?'

        for match in re.finditer(pattern, log_content):
            test_id = match.group(1)
            status = match.group(2)
            duration = float(match.group(3)) if match.group(3) else None

            results.append({
                'entity_id': test_id,
                'status': status,
                'duration': duration
            })

        return results

    @staticmethod
    def parse_pytest_summary(log_content: str) -> Dict:
        """
        Parse pytest summary line.

        Example: "===== 100 passed, 2 failed in 45.67s ====="
        """
        summary = {}

        # Pattern: === X passed, Y failed, Z skipped in W.Ws ===
        pattern = r'=+\s*(?:(\d+)\s+passed)?.*?(?:(\d+)\s+failed)?.*?(?:(\d+)\s+skipped)?.*?(?:in\s+(\d+\.?\d*)s)?'

        match = re.search(pattern, log_content)
        if match:
            summary['passed'] = int(match.group(1)) if match.group(1) else 0
            summary['failed'] = int(match.group(2)) if match.group(2) else 0
            summary['skipped'] = int(match.group(3)) if match.group(3) else 0
            summary['duration'] = float(match.group(4)) if match.group(4) else None

        return summary


def sync_ci_run_to_anvil(
    run_id: int,
    github_token: Optional[str] = None,
    db_path: str = ".anvil/history.db"
):
    """
    Sync a GitHub Actions run to Anvil database.

    Args:
        run_id: GitHub Actions workflow run ID
        github_token: GitHub personal access token (optional, reads from env)
        db_path: Path to Anvil database
    """
    print("=" * 80)
    print(f"SYNCING CI RUN {run_id} TO ANVIL DATABASE")
    print("=" * 80)

    # Get token from environment if not provided
    if not github_token:
        github_token = os.getenv('GITHUB_TOKEN')
        if not github_token:
            print("\n❌ GITHUB_TOKEN not found!")
            print("   Please add GITHUB_TOKEN to .env file or set as environment variable")
            print("   Example .env file:")
            print("     GITHUB_TOKEN=ghp_your_token_here")
            return

    # Initialize GitHub Actions provider
    print("\n1. Connecting to GitHub Actions...")
    provider = GitHubActionsProvider(
        owner="lmvcruz",
        repo="argos",
        token=github_token
    )

    # Get workflow run details
    print(f"\n2. Fetching run {run_id} details...")
    run = provider.get_workflow_run(run_id)

    if not run:
        print(f"❌ Run {run_id} not found")
        return

    print(f"   Workflow: {run.workflow_name}")
    print(f"   Status: {run.status}")
    print(f"   Conclusion: {run.conclusion}")
    print(f"   Branch: {run.branch}")
    print(f"   Created: {run.created_at}")

    # Get jobs for this run
    print(f"\n3. Fetching jobs for run {run_id}...")
    jobs = provider.get_jobs(str(run_id))
    print(f"   Found {len(jobs)} jobs")

    # Initialize Anvil database
    print(f"\n4. Connecting to Anvil database: {db_path}")
    db = ExecutionDatabase(db_path)

    execution_count = 0
    test_count = 0

    # Process each job
    for job in jobs:
        print(f"\n5. Processing job: {job.name}")
        print(f"   Job ID: {job.id}")
        print(f"   Status: {job.status}")
        print(f"   Conclusion: {job.conclusion}")

        # Get job logs
        print("   Downloading logs...")
        log_entries = provider.get_logs(str(job.id))

        # Convert log entries to single string
        log_content = "\n".join([entry.content for entry in log_entries]) if log_entries else ""

        if not log_content:
            print("   ⚠️  No logs available")
            continue

        print(f"   Log size: {len(log_content)} bytes")

        # Parse test results
        print("   Parsing pytest output...")
        parser = CITestResultParser()
        test_results = parser.parse_pytest_output(log_content)

        print(f"   Found {len(test_results)} test results")

        if not test_results:
            print("   ℹ️  No pytest output found in logs")
            continue

        # Store in Anvil database
        execution_id = f"ci-{run_id}-{job.id}"

        # Handle timestamp - it's already a datetime object
        if isinstance(job.started_at, datetime):
            timestamp = job.started_at
        elif isinstance(job.started_at, str):
            timestamp = datetime.fromisoformat(job.started_at.replace('Z', '+00:00'))
        else:
            timestamp = datetime.now()  # Fallback

        # Extract platform and Python version from job name
        # Example: "test (ubuntu-latest, 3.11)"
        platform_match = re.search(r'\(([\w-]+),\s*([\d.]+)\)', job.name)
        platform = platform_match.group(1) if platform_match else "unknown"
        python_version = platform_match.group(2) if platform_match else "unknown"

        for test_result in test_results:
            history = ExecutionHistory(
                execution_id=execution_id,
                entity_id=test_result['entity_id'],
                entity_type="test",
                timestamp=timestamp,
                status=test_result['status'],
                duration=test_result['duration'],
                space="ci",  # ← Marks as CI execution
                metadata={
                    "run_id": run_id,
                    "job_id": job.id,
                    "job_name": job.name,
                    "run_url": run.url,
                }
            )

            db.insert_execution_history(history)
            test_count += 1

        execution_count += 1
        print(f"   ✓ Stored {len(test_results)} test results")

    # Update statistics
    print(f"\n6. Updating entity statistics...")
    from anvil.core.statistics_calculator import StatisticsCalculator
    calculator = StatisticsCalculator(db)

    # Calculate stats for CI tests
    ci_stats = calculator.calculate_all_stats(entity_type="test", window=None)
    for stats in ci_stats:
        db.update_entity_statistics(stats)

    print(f"   ✓ Updated statistics for {len(ci_stats)} entities")

    # Close database
    db.close()

    # Print summary
    print("\n" + "=" * 80)
    print("SYNC COMPLETE")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  CI Run: {run_id}")
    print(f"  Jobs Processed: {execution_count}")
    print(f"  Test Results Stored: {test_count}")
    print(f"  Database: {db_path}")

    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    print("\n1. View CI test statistics:")
    print(f"   cd anvil")
    print(f"   anvil stats show --type test")
    print("\n2. Generate Lens report with CI data:")
    print(f"   cd lens")
    print(f"   lens report test-execution --db ../.anvil/history.db --format html")
    print("\n3. (Future) Compare local vs CI:")
    print(f"   lens report comparison --local-vs-ci --format html")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python sync_ci_to_anvil.py <run_id>")
        print("\nExample:")
        print("  python sync_ci_to_anvil.py 21589120797")
        print("\nAuthentication:")
        print("  - Add GITHUB_TOKEN to .env file (recommended)")
        print("  - Or set GITHUB_TOKEN environment variable")
        print("  - Or pass token as second argument")
        return 1

    run_id = int(sys.argv[1])
    github_token = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        sync_ci_run_to_anvil(run_id, github_token)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
