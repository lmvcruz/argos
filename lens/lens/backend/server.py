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
import logging
import json
import subprocess
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from lens.backend.action_runner import ActionRunner, ActionInput, ActionType

try:
    from anvil.storage import CIStorageLayer
    from anvil.storage.execution_schema import ExecutionDatabase
    ANVIL_AVAILABLE = True
except ImportError:
    ANVIL_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    ):
        """
        Sync CI data from GitHub to Anvil database.

        Uses Scout to fetch CI workflow runs from GitHub and stores them in Anvil.

        Args:
            github_token: GitHub personal access token (or use GITHUB_TOKEN env var)
            owner: GitHub repository owner
            repo: GitHub repository name

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

            # Determine repo path
            repo_path = Path.cwd()

            # Run scout ci sync command
            cmd = [
                "python", "-m", "scout.cli", "ci", "sync",
                "--github-token", token,
            ]

            if owner:
                cmd.extend(["--owner", owner])
            if repo:
                cmd.extend(["--repo", repo])

            logger.info(f"Running Scout CI sync: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Scout sync failed: {error_msg}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Scout sync failed: {error_msg}"
                )

            # Broadcast sync completion
            message = json.dumps({
                "type": "ci_sync_completed",
                "status": "success",
                "output": result.stdout,
            })
            await app.connection_manager.broadcast(message)

            return {
                "status": "success",
                "message": "CI data synced successfully",
                "output": result.stdout,
            }

        except subprocess.TimeoutExpired:
            raise HTTPException(
                status_code=408,
                detail="Scout sync timed out after 5 minutes"
            )
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
