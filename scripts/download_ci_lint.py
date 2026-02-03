"""
Download and process lint artifacts from GitHub Actions CI runs.

This script downloads flake8, black, and isort output files from GitHub Actions
artifacts OR parses workflow logs, then stores the results in the Anvil database
with space="ci".

Supports two modes:
1. Artifact mode: Downloads uploaded artifact files (faster, cleaner)
2. Log mode: Downloads and parses workflow logs (works for older runs)
"""

import argparse
import io
import os
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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


def download_workflow_logs(repo_owner: str, repo_name: str, run_id: str, token: str, output_dir: Path) -> Optional[Path]:
    """
    Download workflow logs from a GitHub Actions run.

    Args:
        repo_owner: GitHub repository owner
        repo_name: GitHub repository name
        run_id: GitHub Actions run ID
        token: GitHub personal access token
        output_dir: Directory to save downloaded logs

    Returns:
        Path to extracted logs directory or None if failed
    """
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Get logs
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{run_id}/logs"
    print(f"Downloading workflow logs...")

    response = requests.get(url, headers=headers, stream=True)

    if response.status_code != 200:
        print(f"   Failed to download logs: {response.status_code}")
        return None

    # Save zip file
    zip_path = output_dir / f"logs-{run_id}.zip"
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"   Downloaded to {zip_path}")

    # Extract zip file
    extract_dir = output_dir / f"logs-{run_id}"
    extract_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_dir)

    print(f"   Extracted {len(list(extract_dir.glob('*')))} log files")

    # Remove zip file
    zip_path.unlink()

    return extract_dir


def extract_lint_output_from_log(log_content: str, tool: str) -> Optional[str]:
    """
    Extract lint tool output from workflow log content.

    Args:
        log_content: Raw log file content
        tool: Tool name (flake8, black, isort)

    Returns:
        Extracted tool output or None if not found
    """
    # Remove timestamps and GitHub Actions formatting
    # Format: 2024-01-15T10:30:45.1234567Z ##[group]Run flake8
    lines = []
    in_tool_section = False
    tool_patterns = {
        'flake8': [
            r'Lint with flake8',
            r'Run flake8',
            r'flake8 \.',
        ],
        'black': [
            r'Check formatting with black',
            r'black --check',
            r'Run black',
        ],
        'isort': [
            r'Check import.*isort',
            r'isort --check',
            r'Run isort',
        ],
    }

    patterns = tool_patterns.get(tool, [])
    end_patterns = [
        r'##\[group\]',  # Next GitHub Actions group
        r'Post ',  # Post-job cleanup steps
        r'Uploading',  # Artifact upload
    ]

    for line in log_content.split('\n'):
        # Remove timestamp prefix: 2024-01-15T10:30:45.1234567Z
        clean_line = re.sub(r'^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s*', '', line)

        # Check if we're entering the tool section
        if not in_tool_section:
            for pattern in patterns:
                if re.search(pattern, clean_line, re.IGNORECASE):
                    in_tool_section = True
                    break
        else:
            # Check if we're leaving the tool section
            stop = False
            for pattern in end_patterns:
                if re.search(pattern, clean_line):
                    stop = True
                    break

            if stop:
                break

            # Skip GitHub Actions formatting lines
            if clean_line.startswith('##['):
                continue

            # Collect actual output
            if clean_line.strip():
                lines.append(clean_line)

    if not lines:
        return None

    return '\n'.join(lines)


def parse_logs_for_project(logs_dir: Path, project: str) -> Dict[str, str]:
    """
    Parse workflow logs to extract lint outputs for a project.

    Args:
        logs_dir: Directory containing extracted log files
        project: Project name (forge, anvil, scout)

    Returns:
        Dictionary mapping tool name to output text
    """
    outputs = {}

    # Map project to job name patterns
    job_patterns = {
        'forge': ['lint', 'forge'],
        'anvil': ['lint', 'anvil', 'quality'],
        'scout': ['quality', 'scout', 'Code Quality'],
    }

    patterns = job_patterns.get(project, [project])

    # Find the log file for this project's lint/quality job
    log_file = None
    for pattern in patterns:
        # Try exact match first
        candidates = list(logs_dir.glob(f"*{pattern}*.txt"))

        # Filter out 'test' jobs - we want lint/quality jobs only
        candidates = [c for c in candidates if 'test' not in c.name.lower() or 'quality' in c.name.lower() or 'lint' in c.name.lower()]

        if candidates:
            log_file = candidates[0]
            break

        # Try case-insensitive
        for f in logs_dir.glob("*.txt"):
            if pattern.lower() in f.name.lower():
                log_file = f
                break

        if log_file:
            break

    if not log_file:
        print(f"   WARNING: No log file found for {project}")
        return outputs

    print(f"   Parsing {log_file.name}")

    try:
        log_content = log_file.read_text(encoding='utf-8', errors='ignore')

        # Extract output for each tool
        for tool in ['flake8', 'black', 'isort']:
            output = extract_lint_output_from_log(log_content, tool)
            if output:
                outputs[tool] = output
                print(f"      Found {tool} output ({len(output)} chars)")

    except Exception as e:
        print(f"   ERROR parsing log: {e}")

    return outputs


def process_lint_from_logs(logs_dir: Path, db: ExecutionDatabase, execution_id: str, project: str) -> int:
    """
    Process lint data from workflow logs and store in database.

    Args:
        logs_dir: Directory containing log files
        db: ExecutionDatabase instance
        execution_id: Unique execution identifier
        project: Project name (forge, anvil, scout)

    Returns:
        Total number of violations stored
    """
    outputs = parse_logs_for_project(logs_dir, project)

    if not outputs:
        print(f"   No lint outputs found in logs for {project}")
        return 0

    timestamp = datetime.now()
    total_violations = 0

    for tool, output in outputs.items():
        print(f"\n   Processing {tool} output from logs for {project}...")

        try:
            violations = store_lint_data(
                db, execution_id, output, tool, "ci", timestamp
            )
            total_violations += violations

            if violations > 0:
                print(f"      Stored {violations} {tool} violations")
            else:
                print(f"      No {tool} violations found")

        except Exception as e:
            print(f"      ERROR processing {tool}: {e}")

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
    parser.add_argument(
        "--mode",
        choices=["artifact", "log", "auto"],
        default="auto",
        help="Data source mode: artifact (uploaded files), log (workflow logs), auto (try artifact first, fallback to log)",
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

    print("=" * 80)
    print("DOWNLOADING CI LINT DATA")
    print("=" * 80)
    print(f"Repository: {repo_owner}/{repo_name}")
    print(f"Run ID: {args.run_id}")
    print(f"Mode: {args.mode}")
    print(f"Projects: {', '.join(args.projects)}")
    print(f"Database: {args.db}")
    print()

    # Initialize database
    db = ExecutionDatabase(args.db)
    execution_id = f"ci-{args.run_id}"
    total_violations = 0
    processed_projects = []

    # Determine which mode to use
    use_logs = args.mode == "log"
    logs_dir = None

    # Process each project
    for project in args.projects:
        print()
        print("=" * 80)
        print(f"Processing {project.upper()}")
        print("=" * 80)

        violations = 0

        # Try artifact mode first (if not log-only)
        if not use_logs:
            artifact_name = f"lint-{project}-ubuntu-py3.11"

            # Download artifact
            artifact_dir = download_artifact(
                repo_owner, repo_name, args.run_id, artifact_name, args.token, output_dir
            )

            if artifact_dir:
                # Process lint artifacts
                violations = process_lint_artifacts(
                    artifact_dir, db, execution_id, project
                )
                total_violations += violations
                processed_projects.append(project)
            elif args.mode == "auto":
                # Artifact not found, try logs
                print(f"   Artifact not found, falling back to logs...")
                use_logs = True

        # Try log mode if needed
        if use_logs and violations == 0:
            # Download logs once for all projects
            if logs_dir is None:
                logs_dir = download_workflow_logs(
                    repo_owner, repo_name, args.run_id, args.token, output_dir
                )

            if logs_dir:
                violations = process_lint_from_logs(
                    logs_dir, db, f"{execution_id}-{project}", project
                )
                total_violations += violations
                if violations > 0:
                    processed_projects.append(project)
            else:
                print(f"WARNING: Could not get lint data for {project}")

    db.close()

    # Summary
    print()
    print("=" * 80)
    print("DOWNLOAD COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  Execution ID: {execution_id}")
    print(f"  Mode used: {args.mode}")
    print(f"  Projects processed: {', '.join(processed_projects) if processed_projects else 'none'}")
    print(f"  Total violations: {total_violations}")
    print(f"  Database: {args.db}")
    print()
    print("Generate CI quality report:")
    print(f"  python scripts/generate_quality_report.py --db {args.db} --space ci --format html")
    print()
    print("Compare local vs CI:")
    print(f"  python scripts/generate_quality_report.py --compare")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
