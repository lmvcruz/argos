"""
Download and process lint artifacts from GitHub Actions CI runs.

This script downloads flake8, black, and isort output files from GitHub Actions
artifacts, parses them, and stores the results in the Anvil database with space="ci".
"""

import argparse
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests

# Add anvil to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "anvil"))

from anvil.storage.execution_schema import ExecutionDatabase
from anvil.parsers.lint_parser import LintParser
from scripts.run_local_tests import store_lint_data


def download_artifact(repo_owner: str, repo_name: str, run_id: str, artifact_name: str, token: str, output_dir: Path) -> Optional[Path]:
    """
    Download a specific artifact from a GitHub Actions run.

    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        run_id: GitHub Actions run ID
        artifact_name: Name of the artifact to download
        token: GitHub personal access token
        output_dir: Directory to save downloaded artifacts

    Returns:
        Path to extracted artifact directory or None if failed
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get list of artifacts for this run
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{run_id}/artifacts"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Failed to get artifacts: {response.status_code}")
        print(f"   {response.text}")
        return None

    artifacts = response.json().get("artifacts", [])

    # Find the specific artifact
    artifact = None
    for a in artifacts:
        if a["name"] == artifact_name:
            artifact = a
            break

    if not artifact:
        print(f"WARNING: Artifact '{artifact_name}' not found")
        return None

    # Download the artifact
    download_url = artifact["archive_download_url"]
    print(f"Downloading {artifact_name}...")

    response = requests.get(download_url, headers=headers, stream=True)

    if response.status_code != 200:
        print(f"❌ Failed to download artifact: {response.status_code}")
        return None

    # Save zip file
    zip_path = output_dir / f"{artifact_name}.zip"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"   Downloaded to {zip_path}")

    # Extract zip file
    extract_dir = output_dir / artifact_name
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    print(f"   Extracted to {extract_dir}")

    # Remove zip file
    zip_path.unlink()

    return extract_dir


def process_lint_artifacts(artifact_dir: Path, db: ExecutionDatabase, execution_id: str, project: str):
    """
    Process lint artifacts and store in database.

    Args:
        artifact_dir: Directory containing lint output files
        db: ExecutionDatabase instance
        execution_id: Unique execution identifier
        project: Project name (forge, anvil, scout)
    """
    timestamp = datetime.now()
    total_violations = 0

    # Process flake8 output
    flake8_file = artifact_dir / "flake8-output.txt"
    if flake8_file.exists():
        print(f"\nProcessing flake8 output for {project}...")
        output = flake8_file.read_text(encoding='utf-8')

        if output.strip():
            violations = store_lint_data(
                db, execution_id, output, "flake8", "ci", timestamp
            )
            total_violations += violations
            print(f"   Stored {violations} flake8 violations")
        else:
            print(f"   No flake8 violations found")

    # Process black output
    black_file = artifact_dir / "black-output.txt"
    if black_file.exists():
        print(f"\nProcessing black output for {project}...")
        output = black_file.read_text(encoding='utf-8')

        if "would reformat" in output:
            violations = store_lint_data(
                db, execution_id, output, "black", "ci", timestamp
            )
            total_violations += violations
            print(f"   Stored {violations} black violations")
        else:
            print(f"   No black violations found")

    # Process isort output
    isort_file = artifact_dir / "isort-output.txt"
    if isort_file.exists():
        print(f"\nProcessing isort output for {project}...")
        output = isort_file.read_text(encoding='utf-8')

        if "ERROR:" in output or "would be reformatted" in output:
            violations = store_lint_data(
                db, execution_id, output, "isort", "ci", timestamp
            )
            total_violations += violations
            print(f"   Stored {violations} isort violations")
        else:
            print(f"   No isort violations found")

    return total_violations


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download and process lint artifacts from GitHub Actions"
    )
    parser.add_argument("run_id", help="GitHub Actions run ID")
    parser.add_argument(
        "--repo", default="lmvcruz/argos", help="GitHub repository (owner/name)"
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub personal access token (or set GITHUB_TOKEN env var)",
    )
    parser.add_argument("--db", default=".anvil/history.db", help="Database path")
    parser.add_argument(
        "--output-dir", default=".ci-artifacts", help="Directory to save artifacts"
    )
    parser.add_argument(
        "--projects",
        nargs="+",
        default=["forge", "anvil", "scout"],
        help="Projects to process (default: forge anvil scout)",
    )

    args = parser.parse_args()

    if not args.token:
        print("❌ GitHub token required. Set GITHUB_TOKEN env var or use --token")
        return 1

    # Parse repository
    try:
        repo_owner, repo_name = args.repo.split("/")
    except ValueError:
        print(f"❌ Invalid repository format: {args.repo}")
        print("   Expected format: owner/name")
        return 1

    # Setup
    output_dir = Path(args.output_dir)
    db = ExecutionDatabase(args.db)
    execution_id = f"ci-{args.run_id}"

    print("=" * 80)
    print("DOWNLOADING CI LINT ARTIFACTS")
    print("=" * 80)
    print(f"Repository: {args.repo}")
    print(f"Run ID: {args.run_id}")
    print(f"Projects: {', '.join(args.projects)}")
    print(f"Database: {args.db}")
    print()

    total_all_violations = 0
    processed_projects = []

    # Download and process artifacts for each project
    for project in args.projects:
        artifact_name = f"lint-{project}-ubuntu-py3.11"

        print(f"\n{'=' * 80}")
        print(f"Processing {project.upper()}")
        print(f"{'=' * 80}")

        artifact_dir = download_artifact(
            repo_owner, repo_name, args.run_id, artifact_name, args.token, output_dir
        )

        if not artifact_dir:
            print(f"WARNING: Skipping {project} - artifact not found")
            continue

        # Process lint files
        violations = process_lint_artifacts(
            artifact_dir, db, f"{execution_id}-{project}", project
        )

        total_all_violations += violations
        processed_projects.append(project)

        print(f"\nSUCCESS: {project}: {violations} total violations stored")

    db.close()

    # Summary
    print("\n" + "=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)
    print(f"\nSummary:")
    print(f"  Execution ID: {execution_id}")
    print(f"  Projects processed: {', '.join(processed_projects)}")
    print(f"  Total violations: {total_all_violations}")
    print(f"  Database: {args.db}")

    print("\nGenerate CI quality report:")
    print(f"  python scripts/generate_quality_report.py --db {args.db} --space ci --format html")

    print("\nCompare local vs CI:")
    print(f"  python scripts/generate_quality_report.py --db {args.db} --space local --format html -o local-quality.html")
    print(f"  python scripts/generate_quality_report.py --db {args.db} --space ci --format html -o ci-quality.html")

    return 0


if __name__ == "__main__":
    sys.exit(main())
