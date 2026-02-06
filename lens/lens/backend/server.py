"""
Lens backend server with FastAPI.

Provides REST API and WebSocket endpoints for Lens UI to:
- Trigger selective execution actions
- Stream execution results
- Query CI data from Anvil
- Compare CI vs local execution
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import io
import json
import logging
import sys
import subprocess
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from lens.backend.action_runner import ActionRunner, ActionInput, ActionType
from lens.backend.scout_ci_endpoints import router as scout_router

try:
    from anvil.storage import CIStorageLayer
    from anvil.storage.execution_schema import ExecutionDatabase
    ANVIL_AVAILABLE = True
except ImportError:
    ANVIL_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _parse_pytest_results(
    result: subprocess.CompletedProcess, project_path: Path
) -> Dict[str, Any]:
    """
    Parse pytest output and convert to test results format.

    Args:
        result: Completed subprocess result from pytest
        project_path: Path where pytest was run

    Returns:
        Dictionary with tests list and summary statistics
    """
    tests = []
    summary = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "flaky": 0,
        "duration": 0.0,
    }

    logger.info(f"Parsing pytest results, return code: {result.returncode}")
    logger.info(f"Stdout length: {len(result.stdout) if result.stdout else 0}")
    logger.info(f"Stderr length: {len(result.stderr) if result.stderr else 0}")

    # Try to parse JSON report if available
    try:
        # Look for pytest-json-report output
        json_report_path = Path("/tmp/report.json")
        logger.info(f"Checking for JSON report at {json_report_path}")
        logger.info(f"JSON report exists: {json_report_path.exists()}")
        if json_report_path.exists():
            with open(json_report_path) as f:
                data = json.load(f)

            if "tests" in data:
                for i, test in enumerate(data["tests"]):
                    nodeid = test.get("nodeid", f"test_{i}")
                    outcome = test.get("outcome", "unknown").lower()
                    duration = test.get("duration", 0.0)

                    # Extract file and test name from nodeid
                    # Format: path/to/test_file.py::TestClass::test_method
                    parts = nodeid.split("::")
                    file_path = parts[0] if parts else "unknown"
                    test_name = "::".join(parts[1:]) if len(
                        parts) > 1 else "unknown"

                    test_obj = {
                        "id": f"test_{i}",
                        "name": test_name,
                        "status": outcome,
                        "file": file_path,
                        # Convert to milliseconds
                        "duration": int(duration * 1000),
                    }

                    # Add error message for failed tests
                    if outcome == "failed":
                        longrepr = test.get("longrepr", "Test failed")
                        # Extract just the last line or assertion
                        if longrepr:
                            lines = str(longrepr).split("\n")
                            test_obj["error"] = lines[-1] if lines else "Test failed"

                    tests.append(test_obj)

                    # Update summary counts
                    summary["total"] += 1
                    if outcome == "passed":
                        summary["passed"] += 1
                    elif outcome == "failed":
                        summary["failed"] += 1
                    elif outcome == "skipped":
                        summary["skipped"] += 1

                # Calculate total duration
                if "summary" in data:
                    summary["duration"] = data["summary"].get("total", 0.0)

        else:
            # Fallback: parse verbose pytest output
            logger.warning("JSON report not found, parsing text output")
            _parse_pytest_text_output(result.stdout, tests, summary)

    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.warning(
            f"Could not parse pytest JSON: {e}, falling back to text parsing")
        _parse_pytest_text_output(result.stdout, tests, summary)

    return {"tests": tests, "summary": summary}


def _parse_pytest_text_output(
    output: str, tests: List[Dict[str, Any]], summary: Dict[str, Any]
) -> None:
    """
    Parse pytest text output when JSON is not available.

    Args:
        output: Text output from pytest
        tests: List to append parsed tests to
        summary: Summary dict to update
    """
    import re

    if not output:
        return

    lines = output.split("\n")
    test_count = 0

    for line in lines:
        # Look for test result lines: "test_file.py::test_name PASSED/FAILED/SKIPPED"
        match = re.search(r"^(.*?::[^\s]+)\s+(PASSED|FAILED|SKIPPED)", line)
        if match:
            test_path = match.group(1)
            status_upper = match.group(2)
            status = status_upper.lower()

            # Extract file and test name
            if "::" in test_path:
                file_path, test_name = test_path.split("::", 1)
            else:
                file_path = test_path
                test_name = test_path

            tests.append({
                "id": f"test_{test_count}",
                "name": test_name,
                "status": status,
                "file": file_path,
                "duration": 0,
            })
            test_count += 1

            summary["total"] += 1
            if status == "passed":
                summary["passed"] += 1
            elif status == "failed":
                summary["failed"] += 1
            elif status == "skipped":
                summary["skipped"] += 1

        # Look for summary line: "X passed, Y failed in Zs"
        elif re.search(r"\d+\s+passed|failed|skipped", line) and "in" in line:
            # Extract counts
            passed_match = re.search(r"(\d+)\s+passed", line)
            failed_match = re.search(r"(\d+)\s+failed", line)
            skipped_match = re.search(r"(\d+)\s+skipped", line)
            time_match = re.search(r"(\d+\.?\d*)\s*s", line)

            if passed_match:
                summary["passed"] = int(passed_match.group(1))
            if failed_match:
                summary["failed"] = int(failed_match.group(1))
            if skipped_match:
                summary["skipped"] = int(skipped_match.group(1))
            if time_match:
                summary["duration"] = float(time_match.group(1))


class ConnectionManager:
    """Manage WebSocket connections for streaming results."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        """
        Accept and track WebSocket connection.

        Args:
            websocket: WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        """
        Remove WebSocket connection.

        Args:
            websocket: WebSocket connection to disconnect
        """
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        """
        Broadcast message to all connected clients.

        Args:
            message: JSON-formatted message to broadcast
        """
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message: {e}")

    async def send_personal(self, websocket: WebSocket, message: str):
        """
        Send message to specific client.

        Args:
            websocket: Target WebSocket connection
            message: JSON-formatted message to send
        """
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title="Lens Backend",
        description="Backend server for Lens UI with CI integration",
        version="0.7.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global state
    app.action_runner = ActionRunner()
    app.connection_manager = ConnectionManager()

    # Initialize Anvil integration if available
    app.ci_storage = None
    if ANVIL_AVAILABLE:
        try:
            anvil_db_path = Path.cwd() / ".anvil" / "execution.db"
            db = ExecutionDatabase(str(anvil_db_path))
            app.ci_storage = CIStorageLayer(db)
            logger.info(f"Anvil CI Storage initialized from {anvil_db_path}")
        except Exception as e:
            logger.warning(f"Could not initialize Anvil CI Storage: {e}")

    # ===== Health Check =====

    @app.get("/health")
    @app.get("/api/health")
    async def health_check():
        """Check server health."""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "0.7.0",
        }

    # ===== File Listing =====

    @app.get("/api/anvil/list-files")
    async def list_files(root: str = Query(...)):
        """
        List files in a directory recursively.

        Args:
            root: Root directory path to scan

        Returns:
            JSON with file tree structure
        """
        from pathlib import Path

        try:
            root_path = Path(root).resolve()

            if not root_path.exists():
                raise HTTPException(
                    status_code=400, detail=f"Path does not exist: {root}")

            if not root_path.is_dir():
                raise HTTPException(
                    status_code=400, detail=f"Path is not a directory: {root}")

            def build_tree(path: Path, max_depth: int = 10, current_depth: int = 0) -> Dict[str, Any]:
                """Build file tree recursively."""
                if current_depth >= max_depth:
                    return {"id": str(path), "name": path.name, "type": "folder", "children": []}

                try:
                    if path.is_file():
                        return {
                            "id": str(path),
                            "name": path.name,
                            "type": "file",
                        }

                    children = []
                    for item in sorted(path.iterdir()):
                        # Skip hidden files/folders and common ignored directories
                        if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules', '.git', 'dist', 'build']:
                            continue

                        children.append(build_tree(
                            item, max_depth, current_depth + 1))

                    return {
                        "id": str(path),
                        "name": path.name,
                        "type": "folder",
                        "children": children,
                    }
                except (PermissionError, OSError) as e:
                    logger.warning(f"Error scanning {path}: {e}")
                    return {
                        "id": str(path),
                        "name": path.name,
                        "type": "folder",
                        "children": [],
                    }

            file_tree = build_tree(root_path)
            return {
                "root": str(root_path),
                "tree": file_tree,
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error listing files: {str(e)}")

    # ===== Anvil Code Analysis =====

    @app.post("/api/anvil/analyze")
    async def analyze_code(request: Dict[str, Any]):
        """
        Run Anvil code analysis on a project.

        Args:
            request: JSON with projectPath and optional toolOptions

        Returns:
            Analysis results with issues and summary statistics
        """
        try:
            project_path = request.get("projectPath")
            if not project_path:
                raise HTTPException(
                    status_code=400, detail="projectPath is required")

            project_path = Path(project_path).resolve()
            if not project_path.exists():
                raise HTTPException(
                    status_code=400, detail=f"Project path does not exist: {project_path}")

            # Run anvil check command
            try:
                # Use Anvil's CLI to analyze the project with JSON output
                cmd = [
                    sys.executable,
                    "-m",
                    "anvil",
                    "check",
                    "--format",
                    "json",
                    str(project_path),
                ]

                logger.info(f"Running Anvil analysis on {project_path}")
                logger.info(f"Command: {' '.join(cmd)}")

                # Add anvil path to PYTHONPATH to ensure the module is found
                env = os.environ.copy()
                anvil_path = str(
                    Path(__file__).parent.parent.parent.parent / "anvil")
                if "PYTHONPATH" in env:
                    env["PYTHONPATH"] = f"{anvil_path}{os.pathsep}{env['PYTHONPATH']}"
                else:
                    env["PYTHONPATH"] = anvil_path

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(Path(project_path).parent),
                    timeout=300,  # 5 minute timeout for analysis
                    env=env,
                )

                logger.info(f"Anvil return code: {result.returncode}")
                logger.info(f"Anvil stdout length: {len(result.stdout)}")
                if result.stderr:
                    logger.info(f"Anvil stderr: {result.stderr[:500]}")

                # Parse the output - Anvil returns JSON
                # 0 = all pass, 1 = issues found
                if result.returncode not in [0, 1]:
                    logger.error(
                        f"Anvil analysis failed with code {result.returncode}")
                    logger.error(f"stderr: {result.stderr}")
                    logger.error(f"stdout: {result.stdout[:500]}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Anvil analysis failed: {result.stderr or result.stdout or 'Unknown error'}"
                    )

                # Parse analysis results from stdout
                analysis_data = {"issues": [], "summary": {
                    "total": 0, "errors": 0, "warnings": 0, "info": 0}}

                if result.stdout:
                    try:
                        analysis_data = json.loads(result.stdout)
                        logger.info(
                            f"Successfully parsed Anvil JSON output: {len(analysis_data.get('issues', []))} issues")
                    except json.JSONDecodeError as e:
                        logger.warning(
                            f"Could not parse Anvil JSON output: {e}")
                        logger.warning(f"Raw output: {result.stdout[:500]}")
                        # Try to parse line by line
                        lines = result.stdout.strip().split('\n')
                        for line in reversed(lines):
                            if line.strip().startswith('{'):
                                try:
                                    analysis_data = json.loads(line)
                                    if "issues" in analysis_data:
                                        logger.info("Found JSON in output")
                                        break
                                except json.JSONDecodeError:
                                    continue

                # Ensure we have the expected structure
                issues = analysis_data.get("issues", [])
                summary = analysis_data.get("summary", {})

                if not summary or summary.get("total") == 0:
                    summary = {
                        "total": len(issues),
                        "errors": len([i for i in issues if i.get("severity") == "error"]),
                        "warnings": len([i for i in issues if i.get("severity") == "warning"]),
                        "info": len([i for i in issues if i.get("severity") == "info"]),
                    }

                logger.info(
                    f"Analysis complete: {len(issues)} issues found, summary: {summary}")

                return {
                    "issues": issues,
                    "summary": summary,
                    "duration": analysis_data.get("duration", 0),
                    "timestamp": datetime.now().isoformat(),
                }

            except subprocess.TimeoutExpired:
                raise HTTPException(
                    status_code=408, detail="Analysis timeout (>300s)")
            except FileNotFoundError as e:
                logger.error(f"Anvil CLI not found: {e}")
                raise HTTPException(
                    status_code=500, detail="Anvil CLI not found")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during analysis: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Analysis error: {str(e)}")

    # ===== Verdict Test Execution =====

    @app.post("/api/verdict/execute")
    async def execute_tests(request: Dict[str, Any]):
        """
        Execute tests in a project.

        Args:
            request: JSON with projectPath and optional testPattern

        Returns:
            Test execution results with summary statistics
        """
        try:
            project_path = request.get("projectPath")
            if not project_path:
                raise HTTPException(
                    status_code=400, detail="projectPath is required")

            project_path = Path(project_path).resolve()
            if not project_path.exists():
                raise HTTPException(
                    status_code=400, detail=f"Project path does not exist: {project_path}")

            # Run pytest or test command
            try:
                # Try to discover and run pytest tests
                cmd = [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(project_path),
                    "--tb=short",
                    "-v",
                    "--json-report",
                    "--json-report-file=/tmp/report.json",
                ]

                logger.info(f"Running tests on {project_path}")
                logger.info(f"Command: {' '.join(cmd)}")

                # Add verdict path to PYTHONPATH
                env = os.environ.copy()
                verdict_path = str(
                    Path(__file__).parent.parent.parent.parent / "verdict")
                if "PYTHONPATH" in env:
                    env["PYTHONPATH"] = f"{verdict_path}{os.pathsep}{env['PYTHONPATH']}"
                else:
                    env["PYTHONPATH"] = verdict_path

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(project_path),
                    timeout=300,
                    env=env,
                )

                logger.info(f"Test return code: {result.returncode}")
                logger.info(
                    f"Test stdout length: {len(result.stdout) if result.stdout else 0}")
                logger.info(
                    f"Test stderr length: {len(result.stderr) if result.stderr else 0}")

                if result.stdout:
                    logger.info(
                        f"Test stdout (first 500 chars): {result.stdout[:500]}")
                if result.stderr:
                    logger.info(
                        f"Test stderr (first 500 chars): {result.stderr[:500]}")

                # Parse test results from pytest output
                test_results = _parse_pytest_results(result, project_path)

                logger.info(
                    f"Parsed test results: {test_results['summary']['total']} tests found")

                return {
                    **test_results,
                    "timestamp": datetime.now().isoformat(),
                }

            except subprocess.TimeoutExpired:
                raise HTTPException(
                    status_code=408, detail="Test execution timeout (>300s)")
            except FileNotFoundError as e:
                logger.error(f"Test runner not found: {e}")
                raise HTTPException(
                    status_code=500, detail="Test runner not found")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during test execution: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Test execution error: {str(e)}")

    # ===== Action Management =====

    @app.post("/api/actions")
    async def execute_action(action_request: Dict[str, Any]):
        """
        Execute an action from Lens UI.

        Args:
            action_request: JSON with action_type, project_path, and parameters

        Returns:
            ActionOutput with action_id and status
        """
        try:
            action_type = ActionType(action_request.get("action_type"))
            project_path = action_request.get("project_path")
            parameters = action_request.get("parameters", {})

            action_input = ActionInput(
                action_type=action_type, project_path=project_path, parameters=parameters
            )

            action_output = app.action_runner.run_action(action_input)

            # Broadcast action completion
            message = json.dumps(
                {
                    "type": "action_completed",
                    "action_id": action_output.action_id,
                    "status": action_output.status.value,
                    "result": action_output.result,
                }
            )
            await app.connection_manager.broadcast(message)

            return action_output.to_dict()

        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error executing action: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/actions/{action_id}")
    async def get_action_status(action_id: str):
        """
        Get status of an action.

        Args:
            action_id: ID of action to check

        Returns:
            ActionOutput with current status and results
        """
        action_output = app.action_runner.get_action_status(action_id)
        if not action_output:
            raise HTTPException(status_code=404, detail="Action not found")

        return action_output.to_dict()

    @app.delete("/api/actions/{action_id}")
    async def cancel_action(action_id: str):
        """
        Cancel a running action.

        Args:
            action_id: ID of action to cancel

        Returns:
            Confirmation of cancellation
        """
        success = app.action_runner.cancel_action(action_id)
        if not success:
            raise HTTPException(
                status_code=400, detail="Could not cancel action")

        return {"action_id": action_id, "status": "cancelled"}

    # ===== CI Data Sync =====

    @app.post("/api/ci/sync")
    async def sync_ci_data(
        github_token: Optional[str] = Query(None),
        owner: Optional[str] = Query(None),
        repo: Optional[str] = Query(None),
        limit: Optional[int] = Query(None),
        workflow: Optional[str] = Query(None),
        force_download: bool = Query(False),
        force_parse: bool = Query(False),
    ):
        """
        Sync CI data from GitHub to Anvil database.

        Uses Scout to fetch CI workflow runs from GitHub and stores them in Anvil.

        Args:
            github_token: GitHub personal access token (or use GITHUB_TOKEN env var)
            owner: GitHub repository owner
            repo: GitHub repository name
            limit: Maximum number of recent workflow runs to sync (e.g., 5, 10, 20)
            workflow: Filter by specific workflow name (e.g., "Anvil Tests")
            force_download: Force re-download of existing log files (not used by Scout)
            force_parse: Force re-parse and update of existing data (not used by Scout)

        Returns:
            Sync status with execution count
        """
        try:
            # Get token from parameter or environment
            token = github_token or os.environ.get("GITHUB_TOKEN")
            if not token:
                raise ValueError(
                    "GitHub token required. Pass github_token or set GITHUB_TOKEN env var"
                )

            # Build repo string in owner/repo format
            if not owner or not repo:
                raise ValueError("Both owner and repo are required")

            repo_full = f"{owner}/{repo}"

            # Get Anvil database path from storage layer
            anvil_db = ".anvil/execution.db"
            scout_db = ".anvil/scout.db"  # Temporary Scout database for storing fetched data

            # Log the inputs for debugging
            logger.info(f"GitHub Token: {token[:20]}...{token[-10:]}")
            logger.info(f"Repo Format: {repo_full}")
            logger.info(f"Limit: {limit}")
            logger.info(f"Scout DB: {scout_db}")
            logger.info(f"Anvil DB: {anvil_db}")

            # Import Scout CLI
            from scout.cli import main as scout_main

            # Determine which workflows to fetch
            # Scout's ci fetch requires the exact workflow name (as shown in GitHub UI)
            if workflow:
                workflows_to_fetch = [workflow]
            else:
                # Fetch from all known workflows in the argos repo
                # These are the exact workflow names as defined in the YAML files
                workflows_to_fetch = [
                    "Anvil Tests",
                    "Forge Tests",
                    "Scout Tests",
                    "Verdict Tests"
                ]

            all_fetch_output = []
            all_fetch_errors = []

            # Step 1: Fetch workflow runs into Scout database
            for wf in workflows_to_fetch:
                fetch_argv = [
                    "scout", "ci", "fetch",
                    "--token", token,
                    "--repo", repo_full,
                    "--workflow", wf,
                    "--db", scout_db,
                    "--verbose",  # Add verbose flag to see more details
                ]

                if limit:
                    fetch_argv.extend(["--limit", str(limit)])

                # Build debug message with masked token
                debug_args = []
                for arg in fetch_argv:
                    if arg.startswith("github_pat"):
                        debug_args.append("github_pat_***")
                    else:
                        debug_args.append(arg)
                logger.info(
                    f"Fetching workflow '{wf}' with args: {' '.join(debug_args)}")

                # Capture output
                old_stdout = sys.stdout
                old_stderr = sys.stderr
                stdout_capture = io.StringIO()
                stderr_capture = io.StringIO()

                try:
                    sys.stdout = stdout_capture
                    sys.stderr = stderr_capture

                    # Fetch workflow data
                    fetch_return_code = scout_main(argv=fetch_argv)
                    fetch_output = stdout_capture.getvalue()
                    fetch_errors = stderr_capture.getvalue()

                finally:
                    sys.stdout = old_stdout
                    sys.stderr = old_stderr

                if fetch_output:
                    all_fetch_output.append(
                        f"Workflow '{wf}':\n{fetch_output}")
                if fetch_errors:
                    all_fetch_errors.append(
                        f"Workflow '{wf}' errors:\n{fetch_errors}")
                    logger.warning(f"Fetch errors for {wf}: {fetch_errors}")
                logger.info(
                    f"Fetch result for '{wf}': return code {fetch_return_code}, output length: {len(fetch_output)}")

            fetch_combined_output = "\n".join(all_fetch_output)

            # Step 2: Sync fetched runs to Anvil
            sync_argv = [
                "scout", "ci", "sync",
                "--token", token,
                "--repo", repo_full,
                "--db", scout_db,
                "--anvil-db", anvil_db,
            ]

            if limit:
                sync_argv.extend(["--limit", str(limit)])
            if workflow:
                sync_argv.extend(["--workflow", workflow])

            logger.info(f"Step 2: Syncing to Anvil")

            # Capture output
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            try:
                sys.stdout = stdout_capture
                sys.stderr = stderr_capture

                # Sync to Anvil
                sync_return_code = scout_main(argv=sync_argv)
                sync_output = stdout_capture.getvalue()
                sync_errors = stderr_capture.getvalue()

            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

            if sync_return_code != 0:
                error_msg = sync_errors or sync_output
                logger.error(
                    f"Scout sync failed (return code {sync_return_code}): {error_msg}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Scout sync failed: {error_msg}"
                )

            # Combine outputs
            fetch_combined_output = "\n".join(
                all_fetch_output) if all_fetch_output else "(No output from fetch)"
            fetch_errors_output = "\n".join(
                all_fetch_errors) if all_fetch_errors else "(No errors)"
            combined_output = f"FETCH OUTPUT:\n{fetch_combined_output}\n\nFETCH ERRORS:\n{fetch_errors_output}\n\nSYNC OUTPUT:\n{sync_output}"

            # Broadcast sync completion
            message = json.dumps({
                "type": "ci_sync_completed",
                "status": "success",
                "output": combined_output,
            })
            await app.connection_manager.broadcast(message)

            return {
                "status": "success",
                "message": "CI data fetched and synced successfully",
                "output": combined_output,
            }

        except ImportError as e:
            logger.error(f"Failed to import Scout: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Scout module not available: {e}"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error syncing CI data: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ===== CI Execution Queries =====

    @app.get("/api/ci/executions")
    async def get_ci_executions(
        workflow: Optional[str] = Query(None),
        limit: int = Query(10),
        status: Optional[str] = Query(None),
    ):
        """
        Get CI execution results.

        Args:
            workflow: Filter by workflow name
            limit: Maximum number of results
            status: Filter by status (passed, failed, skipped)

        Returns:
            List of CI execution results
        """
        if not app.ci_storage:
            return {
                "executions": [],
                "total": 0,
                "message": "Anvil CI Storage not available. Run 'scout ci sync' to populate data.",
                "filters": {"workflow": workflow, "limit": limit, "status": status},
            }

        try:
            executions = app.ci_storage.get_ci_executions(
                entity_type="test", limit=limit
            )
            # Convert ExecutionHistory to dict format for API response
            execution_list = []
            for exec_history in executions:
                execution_list.append({
                    "id": exec_history.id,
                    "workflow": getattr(exec_history, 'workflow', 'unknown'),
                    "platform": getattr(exec_history, 'platform', 'unknown'),
                    "python_version": getattr(exec_history, 'python_version', 'unknown'),
                    "total_tests": getattr(exec_history, 'total_tests', 0),
                    "passed": getattr(exec_history, 'passed', 0),
                    "failed": getattr(exec_history, 'failed', 0),
                    "skipped": getattr(exec_history, 'skipped', 0),
                    "duration": getattr(exec_history, 'duration', 0.0),
                    "timestamp": getattr(exec_history, 'timestamp', datetime.now()).isoformat(),
                })

            return {
                "executions": execution_list,
                "total": len(execution_list),
                "filters": {"workflow": workflow, "limit": limit, "status": status},
            }
        except Exception as e:
            logger.error(f"Error fetching CI executions: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/ci/statistics")
    async def get_ci_statistics(workflow: Optional[str] = Query(None)):
        """
        Get CI health statistics.

        Args:
            workflow: Filter by workflow name

        Returns:
            CI statistics (pass rate, failure patterns, etc.)
        """
        if not app.ci_storage:
            return {
                "workflow": workflow,
                "total_runs": 0,
                "passed": 0,
                "failed": 0,
                "pass_rate": 0.0,
                "average_duration": 0.0,
                "message": "No CI data available",
            }

        try:
            executions = app.ci_storage.get_ci_executions(limit=None)

            total_runs = len(executions)
            passed = sum(
                getattr(e, 'passed', 0) for e in executions
            )
            failed = sum(
                getattr(e, 'failed', 0) for e in executions
            )
            total_tests = passed + failed
            pass_rate = (passed / total_tests *
                         100) if total_tests > 0 else 0.0
            avg_duration = (
                sum(getattr(e, 'duration', 0) for e in executions) / total_runs
                if total_runs > 0 else 0.0
            )

            return {
                "workflow": workflow,
                "total_runs": total_runs,
                "passed": passed,
                "failed": failed,
                "pass_rate": pass_rate,
                "average_duration": avg_duration,
            }
        except Exception as e:
            logger.error(f"Error fetching CI statistics: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # ===== Local vs CI Comparison =====

    @app.get("/api/comparison/entity/{entity_id}")
    async def compare_entity(
        entity_id: str,
        entity_type: str = Query("test"),
    ):
        """
        Compare entity (test/file) results between CI and local.

        Args:
            entity_id: ID of entity to compare (test node ID or file path)
            entity_type: Type of entity (test, file, coverage)

        Returns:
            Comparison analysis with platform differences
        """
        # Placeholder - will be connected to Anvil ComparisonStatistics
        return {
            "entity_id": entity_id,
            "entity_type": entity_type,
            "local_status": None,
            "ci_status": None,
            "platforms": [],
            "platform_specific": False,
        }

    @app.get("/api/comparison/flaky")
    async def get_flaky_tests(
        threshold: int = Query(3),
        lookback_runs: int = Query(10),
    ):
        """
        Get flaky tests detected from CI runs.

        Args:
            threshold: Minimum failure count to consider flaky
            lookback_runs: Number of CI runs to analyze

        Returns:
            List of flaky tests with failure patterns
        """
        # Placeholder - will be connected to Anvil CI queries
        return {
            "threshold": threshold,
            "lookback_runs": lookback_runs,
            "flaky_tests": [],
            "total_flaky": 0,
        }

    @app.get("/api/comparison/platform-specific-failures")
    async def get_platform_specific_failures():
        """
        Get failures that only occur on specific platforms.

        Returns:
            List of platform-specific failures with platform info
        """
        # Placeholder - will be connected to Anvil platform statistics
        return {
            "failures": [],
            "total": 0,
            "windows_only": [],
            "linux_only": [],
            "macos_only": [],
        }

    # ===== Reproduction =====

    @app.post("/api/reproduction/ci-failure")
    async def generate_ci_reproduction(failure_request: Dict[str, Any]):
        """
        Generate reproduction script for CI-specific failure.

        Args:
            failure_request: JSON with test_id, platform, python_version, etc.

        Returns:
            Reproduction script and environment setup instructions
        """
        test_id = failure_request.get("test_id")
        platform = failure_request.get("platform", "linux")
        python_version = failure_request.get("python_version", "3.11")

        return {
            "test_id": test_id,
            "platform": platform,
            "python_version": python_version,
            "docker_command": (
                f"docker run -it python:{python_version} "
                f"bash -c 'pip install -e . && pytest {test_id}'"
            ),
            "reproduction_steps": [
                f"Select Python {python_version}",
                f"Use {platform} environment (or Docker)",
                f"Run: pytest {test_id} -vvs",
                "Compare output with CI logs",
            ],
        }

    # ===== WebSocket =====

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """
        WebSocket endpoint for real-time result streaming.

        Clients can subscribe to action results and CI updates.
        """
        await app.connection_manager.connect(websocket)
        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                msg_type = message.get("type")

                if msg_type == "subscribe":
                    action_id = message.get("action_id")
                    response = json.dumps(
                        {
                            "type": "subscribed",
                            "action_id": action_id,
                            "message": f"Subscribed to {action_id}",
                        }
                    )
                    await app.connection_manager.send_personal(websocket, response)

                elif msg_type == "ping":
                    response = json.dumps(
                        {"type": "pong", "timestamp": datetime.now().isoformat()}
                    )
                    await app.connection_manager.send_personal(websocket, response)

                else:
                    logger.warning(f"Unknown message type: {msg_type}")

        except WebSocketDisconnect:
            app.connection_manager.disconnect(websocket)
            logger.info("Client disconnected")

    # ===== Scout CI Analytics =====
    app.include_router(scout_router)

    return app


# Create the app instance
app = create_app()


def main():
    """Run the Lens backend server."""
    uvicorn.run(
        "lens.backend.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
