"""
Lens backend server with FastAPI.

Provides REST API and WebSocket endpoints for Lens UI to:
- Trigger selective execution actions
- Stream execution results
- Query CI data from Anvil
- Compare CI vs local execution
"""

from lens.backend.models.project import Project
from lens.backend.database import ProjectDatabase
from lens.backend.logging_config import initialize_logging, get_logger
from lens.backend.scout_ci_endpoints import router as scout_router
from lens.backend.action_runner import ActionRunner, ActionInput, ActionType
import uvicorn
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query, Body
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import io
import json
import logging
import sys
import subprocess
import os

# CRITICAL: Add local anvil directory to sys.path FIRST (before site-packages)
# This ensures we use the development version, not any installed version
# d:/playground/argos
_workspace_root = Path(__file__).parent.parent.parent.parent
_anvil_dir = _workspace_root / 'anvil'
if str(_anvil_dir) not in sys.path and _anvil_dir.exists():
    sys.path.insert(0, str(_anvil_dir))
    # Also add the parent of anvil
    sys.path.insert(0, str(_workspace_root))


try:
    from anvil.storage import CIStorageLayer
    from anvil.storage.execution_schema import ExecutionDatabase
    ANVIL_AVAILABLE = True
except ImportError:
    ANVIL_AVAILABLE = False

# Initialize logging
initialize_logging(logging.DEBUG)
logger = get_logger(__name__)

# Configure anvil logging to use our logger
anvil_logger = get_logger('anvil')
anvil_logger.setLevel(logging.DEBUG)


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

    # Initialize projects database
    app.projects_db = ProjectDatabase()
    logger.info("Projects database initialized")

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

    # ===== File Inspection =====

    @app.get("/api/inspection/files")
    async def inspection_get_files(path: str = Query(...)):
        """
        Get file tree for inspection.

        Args:
            path: Project root path

        Returns:
            JSON with file tree structure
        """
        try:
            logger.debug(f"[GET_FILES] Request path: {path}")
            root_path = Path(path).resolve()
            logger.debug(f"[GET_FILES] Resolved to: {root_path}")

            if not root_path.exists():
                logger.warning(f"[GET_FILES] Path does not exist: {root_path}")
                raise HTTPException(
                    status_code=400, detail=f"Path does not exist: {path}")

            if not root_path.is_dir():
                logger.warning(
                    f"[GET_FILES] Path is not a directory: {root_path}")
                raise HTTPException(
                    status_code=400, detail=f"Path is not a directory: {path}")

            def build_tree(p: Path, max_depth: int = 10, current_depth: int = 0) -> Dict[str, Any]:
                """Build file tree recursively."""
                if current_depth >= max_depth:
                    return {
                        "id": str(p),
                        "name": p.name,
                        "type": "folder",
                        "children": []
                    }

                try:
                    if p.is_file():
                        return {
                            "id": str(p),
                            "name": p.name,
                            "type": "file",
                        }

                    children = []
                    for item in sorted(p.iterdir()):
                        # Skip hidden files/folders and common ignored directories
                        if item.name.startswith('.') or item.name in ['__pycache__', 'node_modules', '.git', 'dist', 'build']:
                            continue

                        children.append(build_tree(
                            item, max_depth, current_depth + 1))

                    return {
                        "id": str(p),
                        "name": p.name,
                        "type": "folder",
                        "children": children,
                    }
                except (PermissionError, OSError) as e:
                    logger.debug(f"[GET_FILES] Error scanning {p}: {e}")
                    return {
                        "id": str(p),
                        "name": p.name,
                        "type": "folder",
                        "children": [],
                    }

            file_tree = build_tree(root_path)
            logger.info(f"[GET_FILES] Built file tree for {root_path}")
            return {"files": [file_tree]}
        except Exception as e:
            logger.error(f"[GET_FILES] Error: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Error listing files: {str(e)}")

    @app.get("/api/inspection/languages")
    async def inspection_get_languages():
        """Get supported programming languages for inspection."""
        return {
            "languages": ["python", "javascript", "cpp", "java", "c", "rust"]
        }

    @app.get("/api/inspection/validators")
    async def inspection_get_validators():
        """Get available validators for inspection."""
        return {
            "validators": [
                {
                    "id": "flake8",
                    "name": "flake8",
                    "description": "Python linter for style guide enforcement",
                    "language": "python"
                },
                {
                    "id": "pylint",
                    "name": "pylint",
                    "description": "Python static code analyzer",
                    "language": "python"
                },
                {
                    "id": "mypy",
                    "name": "mypy",
                    "description": "Python static type checker",
                    "language": "python"
                },
                {
                    "id": "eslint",
                    "name": "ESLint",
                    "description": "JavaScript linter",
                    "language": "javascript"
                },
                {
                    "id": "prettier",
                    "name": "Prettier",
                    "description": "JavaScript code formatter",
                    "language": "javascript"
                },
                {
                    "id": "clang-format",
                    "name": "clang-format",
                    "description": "C++ code formatter",
                    "language": "cpp"
                },
                {
                    "id": "cppcheck",
                    "name": "cppcheck",
                    "description": "C++ static analysis",
                    "language": "cpp"
                },
                {
                    "id": "black",
                    "name": "black",
                    "description": "Python code formatter",
                    "language": "python"
                },
                {
                    "id": "isort",
                    "name": "isort",
                    "description": "Python import sorter",
                    "language": "python"
                },
            ]
        }

    @app.post("/api/inspection/validate")
    async def inspection_validate(request: Dict[str, Any] = Body(...)):
        """
        Run validation on target file/folder using Anvil validators.

        Args:
            request: JSON with path, language, validator, target, fix (optional)

        Returns:
            JSON with validation results and report summary
        """
        try:
            path = request.get("path")
            language = request.get("language")
            validator_name = request.get("validator")
            target = request.get("target")
            fix = request.get("fix", False)  # New parameter for auto-fixing

            logger.debug(
                f"[VALIDATE] Received request: path={path}, language={language}, validator={validator_name}, target={target}, fix={fix}")
            logger.info(
                f"Validation request: {validator_name} on {target} (fix={fix})")

            if not all([path, language, validator_name, target]):
                missing = []
                if not path:
                    missing.append("path")
                if not language:
                    missing.append("language")
                if not validator_name:
                    missing.append("validator")
                if not target:
                    missing.append("target")
                error_msg = f"Missing required fields: {', '.join(missing)}"
                logger.error(f"[VALIDATE] Validation failed - {error_msg}")
                raise HTTPException(
                    status_code=400,
                    detail=error_msg
                )

            # Import Anvil validators dynamically
            try:
                logger.debug(
                    f"[VALIDATE] Importing validator {validator_name} for language {language}")
                if language == "python":
                    if validator_name == "flake8":
                        from anvil.validators.flake8_validator import Flake8Validator
                        validator_class = Flake8Validator
                    elif validator_name == "pylint":
                        from anvil.validators.pylint_validator import PylintValidator
                        validator_class = PylintValidator
                    elif validator_name == "black":
                        from anvil.validators.black_validator import BlackValidator
                        validator_class = BlackValidator
                    elif validator_name == "isort":
                        from anvil.validators.isort_validator import IsortValidator
                        validator_class = IsortValidator
                    else:
                        # Default to flake8
                        from anvil.validators.flake8_validator import Flake8Validator
                        validator_class = Flake8Validator
                elif language == "cpp":
                    if validator_name == "clang-tidy":
                        from anvil.validators.clang_tidy_validator import ClangTidyValidator
                        validator_class = ClangTidyValidator
                    elif validator_name == "cppcheck":
                        from anvil.validators.cppcheck_validator import CppcheckValidator
                        validator_class = CppcheckValidator
                    else:
                        # Default to cppcheck
                        from anvil.validators.cppcheck_validator import CppcheckValidator
                        validator_class = CppcheckValidator
                else:
                    logger.error(
                        f"[VALIDATE] Unsupported language: {language}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported language: {language}"
                    )
                logger.debug(
                    f"[VALIDATE] Successfully imported {validator_name} validator")
            except ImportError as e:
                logger.error(
                    f"[VALIDATE] Failed to import validator {validator_name}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Validator not available: {str(e)}"
                )

            # Initialize validator
            logger.debug(f"[VALIDATE] Initializing validator instance")
            validator = validator_class()

            # Check if validator is available
            if not validator.is_available():
                logger.warn(
                    f"[VALIDATE] Validator {validator_name} is not installed")
                raise HTTPException(
                    status_code=400,
                    detail=f"Validator {validator_name} is not installed or available"
                )
            logger.debug(f"[VALIDATE] Validator {validator_name} is available")

            # Determine files to validate
            target_path = Path(target)
            logger.debug(
                f"[VALIDATE] Target: {target_path} (exists={target_path.exists()}, is_file={target_path.is_file()}, is_dir={target_path.is_dir()})")
            files_to_validate = []

            if target_path.is_file():
                files_to_validate = [str(target_path)]
                logger.debug(f"[VALIDATE] Single file target: {target_path}")
            elif target_path.is_dir():
                # Find files matching language extension
                logger.debug(
                    f"[VALIDATE] Directory target, scanning for {language} files")
                extensions = {
                    "python": [".py"],
                    "cpp": [".cpp", ".cc", ".cxx", ".h", ".hpp"],
                    "c": [".c", ".h"],
                    "javascript": [".js", ".jsx", ".ts", ".tsx"],
                    "java": [".java"],
                    "rust": [".rs"],
                }
                exts = extensions.get(language, [])
                files_to_validate = [
                    str(f) for f in target_path.rglob("*")
                    if f.is_file() and f.suffix in exts
                ]

                # Skip hidden directories and common build dirs
                skip_dirs = {".git", "__pycache__",
                             ".pytest_cache", "node_modules", "build", "dist"}
                files_to_validate = [
                    f for f in files_to_validate
                    if not any(skip in Path(f).parts for skip in skip_dirs)
                ]
                logger.debug(
                    f"[VALIDATE] Found {len(files_to_validate)} files to validate")
            else:
                logger.error(f"[VALIDATE] Target path not found: {target}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Target path not found: {target}"
                )

            if not files_to_validate:
                logger.info(
                    f"[VALIDATE] No files found to validate in {target}")
                return {
                    "results": [],
                    "report": {
                        "timestamp": datetime.now().isoformat(),
                        "target": target,
                        "language": language,
                        "validator": validator_name,
                        "total_issues": 0,
                        "errors": 0,
                        "warnings": 0,
                        "infos": 0,
                        "status": "completed",
                        "message": "No files found to validate"
                    }
                }

            # Run validation
            try:
                logger.debug(
                    f"[VALIDATE] Starting validation with options: {{'fix': {fix}}}")
                logger.debug(
                    f"[VALIDATE] Files to validate: {files_to_validate}")
                logger.debug(
                    f"[VALIDATE] Calling anvil validator: {type(validator).__name__}")

                # For fix mode, pass the fix parameter to the validator
                # Some validators (black, isort) support fixing via options
                validator_options = {}
                if fix:
                    # Enable fix mode for validators that support it
                    validator_options["fix"] = True

                logger.debug(
                    f"[VALIDATE] Validator options: {validator_options}")
                validation_result = validator.validate(
                    files_to_validate, validator_options)

                logger.debug(
                    f"[VALIDATE] Validation completed - errors={len(validation_result.errors)}, warnings={len(validation_result.warnings)}")
                logger.debug(f"[VALIDATE] Anvil result: {validation_result}")
            except Exception as e:
                logger.error(
                    f"[VALIDATE] Validation error: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Validation failed: {str(e)}"
                )

            # Convert Anvil validation results to Lens format
            logger.debug(
                f"[VALIDATE] Converting {len(validation_result.errors)} errors and {len(validation_result.warnings)} warnings to Lens format")
            results = []
            for error in validation_result.errors:
                logger.debug(
                    f"[VALIDATE] Processing error: file={error.file_path}, has_diff={hasattr(error, 'diff')}, diff_value={'<present>' if (hasattr(error, 'diff') and error.diff) else 'None or missing'}")

                result_item = {
                    "file": error.file_path or target,
                    "line": error.line_number or 0,
                    "column": error.column_number or 0,
                    "severity": "error",
                    "message": error.message,
                    "rule": error.error_code or error.rule_name or ""
                }
                # Include diff if available (for formatters like black, isort)
                if hasattr(error, 'diff') and error.diff:
                    result_item["diff"] = error.diff
                    logger.debug(
                        f"[VALIDATE] Error includes diff: {error.file_path} (length={len(error.diff)})")
                results.append(result_item)

            for warning in validation_result.warnings:
                result_item = {
                    "file": warning.file_path or target,
                    "line": warning.line_number or 0,
                    "column": warning.column_number or 0,
                    "severity": "warning",
                    "message": warning.message,
                    "rule": warning.error_code or warning.rule_name or ""
                }
                # Include diff if available
                if hasattr(warning, 'diff') and warning.diff:
                    result_item["diff"] = warning.diff
                    logger.debug(
                        f"[VALIDATE] Warning includes diff: {warning.file_path}")
                results.append(result_item)

            # Calculate report summary
            error_count = len(validation_result.errors)
            warning_count = len(validation_result.warnings)
            total_issues = error_count + warning_count

            logger.info(
                f"[VALIDATE] Completed: total_issues={total_issues}, errors={error_count}, warnings={warning_count}, files_checked={len(files_to_validate)}")

            response = {
                "results": results,
                "report": {
                    "timestamp": datetime.now().isoformat(),
                    "target": target,
                    "language": language,
                    "validator": validator_name,
                    "total_issues": total_issues,
                    "errors": error_count,
                    "warnings": warning_count,
                    "infos": 0,
                    "status": "completed",
                    "files_checked": len(files_to_validate)
                }
            }

            logger.debug(f"[VALIDATE] Response to frontend: {response}")
            return response
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            raise HTTPException(
                status_code=500, detail=f"Validation error: {str(e)}")

    # ===== Projects Management =====

    @app.post("/api/projects")
    async def create_project(request: Dict[str, Any]):
        """
        Create a new project.

        Args:
            request: JSON with name, local_folder, repo, token, storage_location

        Returns:
            Created project with ID

        Raises:
            HTTPException: If project data is invalid or name already exists
        """
        try:
            logger.debug(
                f"[CREATE_PROJECT] Request: name={request.get('name')}, folder={request.get('local_folder')}, repo={request.get('repo')}")

            # Validate required fields
            required_fields = {'name', 'local_folder', 'repo'}
            if not required_fields.issubset(request.keys()):
                missing = required_fields - set(request.keys())
                logger.error(f"[CREATE_PROJECT] Missing fields: {missing}")
                raise ValueError(f"Missing required fields: {missing}")

            project = Project(
                name=request['name'],
                local_folder=request['local_folder'],
                repo=request['repo'],
                token=request.get('token'),
                storage_location=request.get('storage_location')
            )

            created = app.projects_db.create_project(project)
            logger.info(
                f"[CREATE_PROJECT] Created project '{created.name}' with ID {created.id}")
            logger.debug(
                f"[CREATE_PROJECT] Project details: {created.to_dict()}")

            return created.to_dict()

        except ValueError as e:
            logger.warning(f"[CREATE_PROJECT] Validation error: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"[CREATE_PROJECT] Error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/projects")
    async def list_projects():
        """
        List all projects.

        Returns:
            List of all projects
        """
        try:
            projects = app.projects_db.list_projects()
            logger.info(f"[LIST_PROJECTS] Listed {len(projects)} projects")
            logger.debug(
                f"[LIST_PROJECTS] Project IDs: {[p.id for p in projects]}")
            return {
                "projects": [p.to_dict() for p in projects],
                "total": len(projects),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/projects/active")
    async def get_active_project():
        """
        Get the currently active project.

        Returns:
            Active project or null if none set
        """
        try:
            project = app.projects_db.get_active_project()
            logger.info(
                f"Retrieved active project: {project.name if project else 'None'}")
            return {
                "active_project": project.to_dict() if project else None,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting active project: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/projects/{project_id}")
    async def get_project(project_id: int):
        """
        Get a specific project by ID.

        Args:
            project_id: Project ID

        Returns:
            Project details

        Raises:
            HTTPException: If project not found
        """
        try:
            project = app.projects_db.get_project(project_id)
            if not project:
                raise HTTPException(
                    status_code=404, detail="Project not found")

            return project.to_dict()
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.put("/api/projects/{project_id}")
    async def update_project(project_id: int, request: Dict[str, Any]):
        """
        Update an existing project.

        Args:
            project_id: Project ID to update
            request: JSON with fields to update

        Returns:
            Updated project

        Raises:
            HTTPException: If project not found or update fails
        """
        try:
            # Get existing project
            project = app.projects_db.get_project(project_id)
            if not project:
                raise HTTPException(
                    status_code=404, detail="Project not found")

            # Update fields
            if 'name' in request:
                project.name = request['name']
            if 'local_folder' in request:
                project.local_folder = request['local_folder']
            if 'repo' in request:
                project.repo = request['repo']
            if 'token' in request:
                project.token = request['token']
            if 'storage_location' in request:
                project.storage_location = request['storage_location']

            updated = app.projects_db.update_project(project)
            logger.info(f"Updated project: {updated.name}")

            return updated.to_dict()

        except ValueError as e:
            logger.warning(f"Validation error updating project: {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating project: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.delete("/api/projects/{project_id}")
    async def delete_project(project_id: int):
        """
        Delete a project.

        Args:
            project_id: Project ID to delete

        Returns:
            Confirmation of deletion

        Raises:
            HTTPException: If project not found
        """
        try:
            deleted = app.projects_db.delete_project(project_id)
            if not deleted:
                raise HTTPException(
                    status_code=404, detail="Project not found")

            logger.info(f"Deleted project ID: {project_id}")
            return {
                "status": "deleted",
                "project_id": project_id,
                "timestamp": datetime.now().isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/projects/{project_id}/select")
    async def set_active_project(project_id: int):
        """
        Set the active project.

        Args:
            project_id: Project ID to set as active

        Returns:
            Confirmation of active project selection

        Raises:
            HTTPException: If project not found
        """
        try:
            app.projects_db.set_active_project(project_id)
            project = app.projects_db.get_project(project_id)
            logger.info(f"Set active project: {project.name}")

            return {
                "status": "active",
                "project": project.to_dict(),
                "timestamp": datetime.now().isoformat()
            }

        except ValueError as e:
            logger.warning(f"Project not found: {e}")
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error setting active project: {e}")
            raise HTTPException(status_code=500, detail=str(e))

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

    @app.get("/api/verdict/discover")
    async def discover_tests(project_path: Optional[str] = Query(None)):
        """
        Discover tests in a project without executing them.

        Args:
            project_path: Path to project root

        Returns:
            List of discovered tests organized by file
        """
        try:
            if not project_path:
                raise HTTPException(
                    status_code=400, detail="project_path is required")

            project_path = Path(project_path).resolve()
            if not project_path.exists():
                raise HTTPException(
                    status_code=400, detail=f"Project path does not exist: {project_path}")

            # Discover pytest tests
            try:
                cmd = [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(project_path),
                    "--collect-only",
                    "-q",
                ]

                logger.info(f"Discovering tests in {project_path}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(project_path),
                    timeout=30,
                )

                # Parse collected tests
                tests = []
                if result.stdout:
                    for line in result.stdout.split('\n'):
                        if '::' in line and ('.py' in line or 'test_' in line):
                            parts = line.split('::')
                            if len(parts) >= 2:
                                file_path = parts[0].strip()
                                test_name = '::'.join(parts[1:]).strip()
                                if test_name:
                                    tests.append({
                                        'file': file_path,
                                        'name': test_name,
                                        'id': f"{file_path}::{test_name}",
                                        'status': 'not-run'
                                    })

                logger.info(f"Discovered {len(tests)} tests")

                return {
                    "tests": tests,
                    "total": len(tests),
                    "timestamp": datetime.now().isoformat(),
                }

            except subprocess.TimeoutExpired:
                raise HTTPException(
                    status_code=408, detail="Test discovery timeout (>30s)")
            except FileNotFoundError:
                # pytest not installed, try to discover manually
                logger.warning(
                    "pytest not available, falling back to file discovery")
                test_files = list(project_path.glob("**/test_*.py")) + \
                    list(project_path.glob("**/*_test.py"))

                tests = []
                for test_file in test_files:
                    tests.append({
                        'file': str(test_file.relative_to(project_path)),
                        'name': test_file.stem,
                        'id': str(test_file.relative_to(project_path)),
                        'status': 'not-run'
                    })

                return {
                    "tests": tests,
                    "total": len(tests),
                    "timestamp": datetime.now().isoformat(),
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error discovering tests: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Test discovery error: {str(e)}")

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

    # ===== Scout Workflow Endpoints =====

    @app.get("/api/scout/workflows")
    async def get_scout_workflows(
        status: Optional[str] = Query(None),
        limit: int = Query(10),
        offset: int = Query(0),
    ):
        """
        Get Scout CI workflows (maps to CI executions).

        Args:
            status: Filter by status (completed, in_progress, queued)
            limit: Maximum number of results
            offset: Number of results to skip

        Returns:
            List of workflows with execution details
        """
        try:
            # Get CI executions and map to Scout workflow format
            if not app.ci_storage:
                return {
                    "workflows": [],
                    "sync_status": {
                        "last_sync": datetime.now().isoformat(),
                        "is_syncing": False,
                        "next_sync": datetime.now().isoformat(),
                    },
                    "total": 0,
                    "timestamp": datetime.now().isoformat(),
                }

            executions = app.ci_storage.get_ci_executions(
                entity_type="test", limit=limit)

            workflows = []
            for exec_history in executions:
                workflow = {
                    "id": str(getattr(exec_history, 'id', 'unknown')),
                    "name": getattr(exec_history, 'workflow', 'unknown'),
                    "run_number": getattr(exec_history, 'id', 0),
                    "branch": "main",
                    "status": "completed",
                    "result": "passed" if getattr(exec_history, 'failed', 0) == 0 else "failed",
                    "duration": getattr(exec_history, 'duration', 0.0),
                    "started_at": getattr(exec_history, 'timestamp', datetime.now()).isoformat(),
                    "url": "",
                    "jobs": [
                        {
                            "id": f"job-{i}",
                            "name": f"Test {i+1}",
                            "status": "completed",
                            "duration": getattr(exec_history, 'duration', 0.0),
                        }
                        for i in range(max(1, getattr(exec_history, 'total_tests', 1)))
                    ],
                }
                workflows.append(workflow)

            return {
                "workflows": workflows,
                "sync_status": {
                    "last_sync": datetime.now().isoformat(),
                    "is_syncing": False,
                    "next_sync": datetime.now().isoformat(),
                },
                "total": len(workflows),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error fetching Scout workflows: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/scout/workflows/{workflow_id}")
    async def get_scout_workflow(workflow_id: str):
        """
        Get details for a specific Scout workflow.

        Args:
            workflow_id: ID of the workflow

        Returns:
            Workflow details with job information
        """
        try:
            if not app.ci_storage:
                raise HTTPException(
                    status_code=404, detail="Workflow not found")

            executions = app.ci_storage.get_ci_executions(limit=None)

            for exec_history in executions:
                if str(getattr(exec_history, 'id', '')) == workflow_id:
                    return {
                        "id": workflow_id,
                        "name": getattr(exec_history, 'workflow', 'unknown'),
                        "run_number": getattr(exec_history, 'id', 0),
                        "branch": "main",
                        "status": "completed",
                        "result": "passed" if getattr(exec_history, 'failed', 0) == 0 else "failed",
                        "duration": getattr(exec_history, 'duration', 0.0),
                        "started_at": getattr(exec_history, 'timestamp', datetime.now()).isoformat(),
                        "url": "",
                        "jobs": [
                            {
                                "id": f"job-{i}",
                                "name": f"Test {i+1}",
                                "status": "completed",
                                "duration": getattr(exec_history, 'duration', 0.0),
                            }
                            for i in range(max(1, getattr(exec_history, 'total_tests', 1)))
                        ],
                    }

            raise HTTPException(
                status_code=404, detail=f"Workflow {workflow_id} not found")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error fetching workflow {workflow_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/scout/sync-status")
    async def get_scout_sync_status():
        """
        Get Scout CI sync status.

        Returns:
            Current sync status and next scheduled sync
        """
        return {
            "last_sync": datetime.now().isoformat(),
            "is_syncing": False,
            "next_sync": datetime.now().isoformat(),
        }

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

    # ===== Logging API =====
    @app.get("/api/logs/config")
    async def get_logs_config() -> Dict[str, Any]:
        """Get logging configuration."""
        from lens.backend.logging_config import LoggerManager
        log_dir = LoggerManager.get_log_dir()
        return {
            "log_dir": str(log_dir),
            "backend_log": str(log_dir / 'backend.log'),
            "frontend_log": str(log_dir / 'frontend.log'),
        }

    @app.get("/api/logs/list")
    async def list_logs() -> Dict[str, Any]:
        """List available log files."""
        from lens.backend.logging_config import LoggerManager
        log_dir = LoggerManager.get_log_dir()
        logs = []
        if log_dir.exists():
            for log_file in log_dir.glob('*.log*'):
                try:
                    stat = log_file.stat()
                    logs.append({
                        'name': log_file.name,
                        'path': str(log_file),
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    })
                except Exception as e:
                    logger.error(f"Error reading log file {log_file}: {e}")
        return {'logs': sorted(logs, key=lambda x: x['modified'], reverse=True)}

    @app.get("/api/logs/read/{log_name}")
    async def read_log(log_name: str, lines: int = Query(100, ge=1, le=10000)) -> Dict[str, Any]:
        """Read log file contents (last N lines)."""
        from lens.backend.logging_config import LoggerManager
        log_dir = LoggerManager.get_log_dir()
        log_file = log_dir / log_name
        if not log_file.parent == log_dir:
            raise HTTPException(
                status_code=400, detail="Invalid log file name")
        if not log_file.exists():
            raise HTTPException(
                status_code=404, detail=f"Log file not found: {log_name}")
        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                all_lines = f.readlines()
                tail_lines = all_lines[-lines:] if len(
                    all_lines) > lines else all_lines
                content = ''.join(tail_lines)
            return {
                'name': log_name,
                'path': str(log_file),
                'total_lines': len(all_lines),
                'returned_lines': len(tail_lines),
                'content': content,
            }
        except Exception as e:
            logger.error(f"Error reading log file {log_file}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error reading log file: {str(e)}")

    @app.post("/api/logs/frontend")
    async def log_frontend_message(message: Dict[str, Any]) -> Dict[str, str]:
        """Log a message from frontend."""
        from lens.backend.logging_config import LoggerManager
        level = message.get('level', 'info').lower()
        msg = message.get('message', '')
        timestamp = message.get('timestamp', datetime.now().isoformat())
        log_dir = LoggerManager.get_log_dir()
        log_dir.mkdir(parents=True, exist_ok=True)
        frontend_log = log_dir / 'frontend.log'
        try:
            with open(frontend_log, 'a', encoding='utf-8') as f:
                f.write(f'[{timestamp}] [{level.upper()}] {msg}\n')
            log_level = getattr(logging, level.upper(), logging.INFO)
            logger.log(log_level, f"[FRONTEND] {msg}")
            return {'status': 'logged', 'file': str(frontend_log)}
        except Exception as e:
            logger.error(f"Error logging frontend message: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error logging message: {str(e)}")

    @app.delete("/api/logs/{log_name}")
    async def delete_log(log_name: str) -> Dict[str, str]:
        """Delete a log file."""
        from lens.backend.logging_config import LoggerManager
        log_dir = LoggerManager.get_log_dir()
        log_file = log_dir / log_name
        if not log_file.parent == log_dir:
            raise HTTPException(
                status_code=400, detail="Invalid log file name")
        if not log_file.exists():
            raise HTTPException(
                status_code=404, detail=f"Log file not found: {log_name}")
        try:
            log_file.unlink()
            logger.info(f"Deleted log file: {log_name}")
            return {'status': 'deleted', 'file': log_name}
        except Exception as e:
            logger.error(f"Error deleting log file {log_file}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error deleting log file: {str(e)}")

    @app.post("/api/logs/clear/{log_name}")
    async def clear_log(log_name: str) -> Dict[str, str]:
        """Clear (truncate) a log file."""
        from lens.backend.logging_config import LoggerManager
        log_dir = LoggerManager.get_log_dir()
        log_file = log_dir / log_name
        if not log_file.parent == log_dir:
            raise HTTPException(
                status_code=400, detail="Invalid log file name")
        if not log_file.exists():
            raise HTTPException(
                status_code=404, detail=f"Log file not found: {log_name}")
        try:
            # Truncate the file (clear it while keeping the file)
            log_file.write_text("")
            logger.info(f"Cleared log file: {log_name}")
            return {'status': 'cleared', 'file': log_name}
        except Exception as e:
            logger.error(f"Error clearing log file {log_file}: {e}")
            raise HTTPException(
                status_code=500, detail=f"Error clearing log file: {str(e)}")

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

    # ===== Local Tests Discovery and Execution =====
    @app.get("/api/tests/discover")
    async def discover_local_tests(path: Optional[str] = Query(None)):
        """
        Discover tests in a project directory.

        Args:
            path: Path to project directory

        Returns:
            List of test suites with their test cases
        """
        try:
            if not path:
                raise HTTPException(
                    status_code=400, detail="path parameter is required")

            project_path = Path(path).resolve()
            if not project_path.exists():
                raise HTTPException(
                    status_code=400, detail=f"Project path does not exist: {project_path}")

            # Discover pytest tests using pytest collect-only
            try:
                cmd = [
                    sys.executable,
                    "-m",
                    "pytest",
                    str(project_path),
                    "--collect-only",
                    "-q",
                    "--quiet",
                ]

                logger.info(f"Discovering tests in {project_path}")
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(project_path),
                    timeout=30,
                )

                # Parse collected tests and organize by suite (file)
                suites_dict: Dict[str, Any] = {}
                
                if result.stdout:
                    for line in result.stdout.split('\n'):
                        if '::' in line and '.py' in line:
                            # Parse pytest node ID: path/to/test_file.py::TestClass::test_method
                            parts = line.strip().split('::')
                            if len(parts) >= 2:
                                file_path = parts[0].strip()
                                test_parts = parts[1:]
                                
                                # Create suite entry if not exists
                                if file_path not in suites_dict:
                                    suites_dict[file_path] = {
                                        'id': file_path,
                                        'name': Path(file_path).stem,
                                        'file': file_path,
                                        'tests': [],
                                        'status': 'not-run',
                                    }
                                
                                # Add test case
                                test_name = '::'.join(test_parts)
                                test_id = f"{file_path}::{test_name}"
                                suites_dict[file_path]['tests'].append({
                                    'id': test_id,
                                    'name': test_name,
                                    'status': 'not-run',
                                })

                suites = list(suites_dict.values())
                logger.info(f"Discovered {len(suites)} test suites with {sum(len(s['tests']) for s in suites)} tests")

                return {
                    "suites": suites,
                    "total_suites": len(suites),
                    "total_tests": sum(len(s['tests']) for s in suites),
                    "timestamp": datetime.now().isoformat(),
                }

            except subprocess.TimeoutExpired:
                logger.warning("Test discovery timeout, falling back to file-based discovery")
                # Fallback: discover test files manually
                test_files = list(project_path.glob("**/test_*.py")) + \
                    list(project_path.glob("**/*_test.py"))

                suites = []
                for test_file in test_files:
                    rel_path = str(test_file.relative_to(project_path))
                    suites.append({
                        'id': rel_path,
                        'name': test_file.stem,
                        'file': rel_path,
                        'tests': [],
                        'status': 'not-run',
                    })

                return {
                    "suites": suites,
                    "total_suites": len(suites),
                    "total_tests": 0,
                    "timestamp": datetime.now().isoformat(),
                }

            except FileNotFoundError:
                logger.warning("pytest not available, using file-based discovery")
                test_files = list(project_path.glob("**/test_*.py")) + \
                    list(project_path.glob("**/*_test.py"))

                suites = []
                for test_file in test_files:
                    rel_path = str(test_file.relative_to(project_path))
                    suites.append({
                        'id': rel_path,
                        'name': test_file.stem,
                        'file': rel_path,
                        'tests': [],
                        'status': 'not-run',
                    })

                return {
                    "suites": suites,
                    "total_suites": len(suites),
                    "total_tests": 0,
                    "timestamp": datetime.now().isoformat(),
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error discovering tests: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Test discovery error: {str(e)}")

    @app.post("/api/tests/execute")
    async def execute_local_tests(request: Dict[str, Any]):
        """
        Execute selected tests.

        Args:
            request: JSON with test_ids to execute

        Returns:
            Test execution results
        """
        try:
            test_ids = request.get("test_ids", [])
            if not test_ids:
                raise HTTPException(
                    status_code=400, detail="test_ids is required")

            # For now, return mock results
            # TODO: Implement actual test execution
            results = []
            for test_id in test_ids:
                results.append({
                    'id': test_id,
                    'name': test_id.split('::')[-1],
                    'status': 'passed',
                    'duration': 100,
                    'error': None,
                    'output': '',
                })

            return {
                "results": results,
                "total": len(results),
                "passed": len(results),
                "failed": 0,
                "timestamp": datetime.now().isoformat(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error executing tests: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Test execution error: {str(e)}")

    @app.get("/api/tests/statistics")
    async def get_test_statistics():
        """
        Get test execution statistics.

        Returns:
            Historical test statistics and trends
        """
        try:
            # TODO: Implement statistics retrieval from database
            # For now, return empty statistics
            statistics = [
                {
                    'date': datetime.now().isoformat(),
                    'total_tests': 0,
                    'passed_tests': 0,
                    'failed_tests': 0,
                    'skipped_tests': 0,
                    'average_duration': 0,
                    'total_duration': 0,
                    'pass_rate': 0,
                }
            ]

            return {
                "statistics": statistics,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Statistics retrieval error: {str(e)}")

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
