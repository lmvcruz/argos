"""
Tests for Scout database schema and storage layer.

This module tests the SQLAlchemy ORM models and database operations
for storing GitHub Actions CI data.
"""

from datetime import datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from scout.storage import (
    Base,
    CIFailurePattern,
    DatabaseManager,
    WorkflowJob,
    WorkflowRun,
    WorkflowTestResult,
)


@pytest.fixture
def db_session():
    """Create an in-memory database session for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def sample_workflow_run():
    """Create a sample WorkflowRun for testing."""
    return WorkflowRun(
        run_id=123456789,
        workflow_name="CI Tests",
        run_number=42,
        event="push",
        status="completed",
        conclusion="success",
        branch="main",
        commit_sha="a" * 40,
        started_at=datetime(2026, 2, 1, 10, 0),
        completed_at=datetime(2026, 2, 1, 10, 15),
        duration_seconds=900,
        url="https://github.com/user/repo/actions/runs/123456789",
        extra_metadata={"actor": "user", "head_branch": "main"},
    )


@pytest.fixture
def sample_workflow_job():
    """Create a sample WorkflowJob for testing."""
    return WorkflowJob(
        job_id=987654321,
        run_id=123456789,
        job_name="test (ubuntu-latest, 3.10)",
        runner_os="ubuntu-latest",
        python_version="3.10",
        status="completed",
        conclusion="failure",
        started_at=datetime(2026, 2, 1, 10, 0),
        completed_at=datetime(2026, 2, 1, 10, 5),
        duration_seconds=300,
        logs_url="https://api.github.com/repos/.../actions/jobs/987654321/logs",
    )


class TestWorkflowRun:
    """Test WorkflowRun model."""

    def test_create_workflow_run(self, db_session, sample_workflow_run):
        """Test creating and persisting a WorkflowRun."""
        db_session.add(sample_workflow_run)
        db_session.commit()

        # Query back
        result = db_session.query(WorkflowRun).filter_by(run_id=123456789).first()
        assert result is not None
        assert result.workflow_name == "CI Tests"
        assert result.run_number == 42
        assert result.conclusion == "success"
        assert result.branch == "main"
        assert result.duration_seconds == 900

    def test_workflow_run_unique_constraint(self, db_session, sample_workflow_run):
        """Test that run_id must be unique."""
        db_session.add(sample_workflow_run)
        db_session.commit()

        # Try to add another with same run_id
        duplicate = WorkflowRun(
            run_id=123456789,  # Same run_id
            workflow_name="Other Workflow",
            status="completed",
        )
        db_session.add(duplicate)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_workflow_run_repr(self, sample_workflow_run):
        """Test WorkflowRun string representation."""
        repr_str = repr(sample_workflow_run)
        assert "WorkflowRun" in repr_str
        assert "123456789" in repr_str
        assert "CI Tests" in repr_str
        assert "success" in repr_str

    def test_workflow_run_relationship_to_jobs(
        self, db_session, sample_workflow_run, sample_workflow_job
    ):
        """Test relationship between WorkflowRun and WorkflowJob."""
        db_session.add(sample_workflow_run)
        db_session.commit()

        db_session.add(sample_workflow_job)
        db_session.commit()

        # Query run and check jobs
        run = db_session.query(WorkflowRun).filter_by(run_id=123456789).first()
        assert len(run.jobs) == 1
        assert run.jobs[0].job_id == 987654321

    def test_workflow_run_cascade_delete(
        self, db_session, sample_workflow_run, sample_workflow_job
    ):
        """Test that deleting a run cascades to its jobs."""
        db_session.add(sample_workflow_run)
        db_session.commit()

        db_session.add(sample_workflow_job)
        db_session.commit()

        # Delete the run
        db_session.delete(sample_workflow_run)
        db_session.commit()

        # Job should be deleted too
        job = db_session.query(WorkflowJob).filter_by(job_id=987654321).first()
        assert job is None


class TestWorkflowJob:
    """Test WorkflowJob model."""

    def test_create_workflow_job(self, db_session, sample_workflow_run, sample_workflow_job):
        """Test creating and persisting a WorkflowJob."""
        db_session.add(sample_workflow_run)
        db_session.commit()

        db_session.add(sample_workflow_job)
        db_session.commit()

        # Query back
        result = db_session.query(WorkflowJob).filter_by(job_id=987654321).first()
        assert result is not None
        assert result.job_name == "test (ubuntu-latest, 3.10)"
        assert result.runner_os == "ubuntu-latest"
        assert result.python_version == "3.10"
        assert result.conclusion == "failure"

    def test_workflow_job_unique_constraint(
        self, db_session, sample_workflow_run, sample_workflow_job
    ):
        """Test that job_id must be unique."""
        db_session.add(sample_workflow_run)
        db_session.commit()

        db_session.add(sample_workflow_job)
        db_session.commit()

        # Try to add another with same job_id
        duplicate = WorkflowJob(
            job_id=987654321,  # Same job_id
            run_id=123456789,
            job_name="Other Job",
            status="completed",
        )
        db_session.add(duplicate)

        with pytest.raises(Exception):  # IntegrityError
            db_session.commit()

    def test_workflow_job_repr(self, sample_workflow_job):
        """Test WorkflowJob string representation."""
        repr_str = repr(sample_workflow_job)
        assert "WorkflowJob" in repr_str
        assert "987654321" in repr_str
        assert "test (ubuntu-latest, 3.10)" in repr_str
        assert "failure" in repr_str

    def test_workflow_job_foreign_key(self, db_session, sample_workflow_run, sample_workflow_job):
        """Test that job can reference a workflow run."""
        # Add run first
        db_session.add(sample_workflow_run)
        db_session.commit()

        # Add job with valid run_id
        db_session.add(sample_workflow_job)
        db_session.commit()

        # Verify the relationship works
        job = db_session.query(WorkflowJob).filter_by(job_id=987654321).first()
        assert job is not None
        assert job.run_id == 123456789
        assert job.run.workflow_name == "CI Tests"


class TestWorkflowTestResult:
    """Test WorkflowTestResult model."""

    def test_create_test_result(self, db_session, sample_workflow_run, sample_workflow_job):
        """Test creating and persisting a WorkflowTestResult."""
        db_session.add(sample_workflow_run)
        db_session.commit()

        db_session.add(sample_workflow_job)
        db_session.commit()

        test_result = WorkflowTestResult(
            job_id=987654321,
            test_nodeid="tests/test_parser.py::test_extract_version",
            outcome="failed",
            duration=0.05,
            error_message="AssertionError: expected '1.0.0', got '1.0.1'",
            error_traceback="Traceback (most recent call last):\n  ...",
            runner_os="ubuntu-latest",
            python_version="3.10",
            timestamp=datetime(2026, 2, 1, 10, 3),
        )
        db_session.add(test_result)
        db_session.commit()

        # Query back
        result = (
            db_session.query(WorkflowTestResult)
            .filter_by(test_nodeid="tests/test_parser.py::test_extract_version")
            .first()
        )
        assert result is not None
        assert result.outcome == "failed"
        assert result.duration == 0.05
        assert "AssertionError" in result.error_message
        assert result.runner_os == "ubuntu-latest"

    def test_test_result_repr(self):
        """Test WorkflowTestResult string representation."""
        test_result = WorkflowTestResult(
            job_id=987654321,
            test_nodeid="tests/test_parser.py::test_extract_version",
            outcome="failed",
            runner_os="ubuntu-latest",
            timestamp=datetime(2026, 2, 1, 10, 3),
        )
        repr_str = repr(test_result)
        assert "WorkflowTestResult" in repr_str
        assert "test_parser.py::test_extract_version" in repr_str
        assert "failed" in repr_str
        assert "ubuntu-latest" in repr_str

    def test_test_result_cascade_delete(self, db_session, sample_workflow_run, sample_workflow_job):
        """Test that deleting a job cascades to its test results."""
        db_session.add(sample_workflow_run)
        db_session.commit()

        db_session.add(sample_workflow_job)
        db_session.commit()

        test_result = WorkflowTestResult(
            job_id=987654321,
            test_nodeid="tests/test_parser.py::test_extract_version",
            outcome="passed",
            timestamp=datetime(2026, 2, 1, 10, 3),
        )
        db_session.add(test_result)
        db_session.commit()

        # Delete the job
        db_session.delete(sample_workflow_job)
        db_session.commit()

        # Test result should be deleted too
        result = (
            db_session.query(WorkflowTestResult)
            .filter_by(test_nodeid="tests/test_parser.py::test_extract_version")
            .first()
        )
        assert result is None


class TestCIFailurePattern:
    """Test CIFailurePattern model."""

    def test_create_failure_pattern(self, db_session):
        """Test creating and persisting a CIFailurePattern."""
        pattern = CIFailurePattern(
            pattern_type="platform-specific",
            test_nodeid="tests/test_symlinks.py::test_create_symlink",
            runner_os="windows-latest",
            failure_count=15,
            first_seen=datetime(2026, 1, 1),
            last_seen=datetime(2026, 2, 1),
            description="Symlink test fails on Windows due to permission issues",
            suggested_fix="Skip test on Windows or use pytest.mark.skipif",
            extra_metadata={"error_type": "PermissionError"},
        )
        db_session.add(pattern)
        db_session.commit()

        # Query back
        result = (
            db_session.query(CIFailurePattern)
            .filter_by(test_nodeid="tests/test_symlinks.py::test_create_symlink")
            .first()
        )
        assert result is not None
        assert result.pattern_type == "platform-specific"
        assert result.runner_os == "windows-latest"
        assert result.failure_count == 15
        assert "Symlink test fails" in result.description

    def test_failure_pattern_repr(self):
        """Test CIFailurePattern string representation."""
        pattern = CIFailurePattern(
            pattern_type="flaky",
            failure_count=5,
            runner_os="ubuntu-latest",
        )
        repr_str = repr(pattern)
        assert "CIFailurePattern" in repr_str
        assert "flaky" in repr_str
        assert "5" in repr_str
        assert "ubuntu-latest" in repr_str


class TestDatabaseManager:
    """Test DatabaseManager class."""

    def test_create_database_manager(self, tmp_path):
        """Test creating a DatabaseManager with custom path."""
        db_path = str(tmp_path / "test.db")
        db = DatabaseManager(db_path=db_path)
        assert db.db_path == db_path
        assert not db.echo

    def test_initialize_database(self, tmp_path):
        """Test initializing database and creating tables."""
        db_path = str(tmp_path / "test.db")
        db = DatabaseManager(db_path=db_path)
        db.initialize()

        # Check that database file was created
        assert (tmp_path / "test.db").exists()

        # Check that we can get a session
        session = db.get_session()
        assert isinstance(session, Session)
        session.close()
        db.close()

    def test_get_session_without_initialize(self, tmp_path):
        """Test that get_session raises error if not initialized."""
        db_path = str(tmp_path / "test.db")
        db = DatabaseManager(db_path=db_path)

        with pytest.raises(RuntimeError, match="not initialized"):
            db.get_session()

    def test_reset_database(self, tmp_path):
        """Test resetting database (drop and recreate tables)."""
        db_path = str(tmp_path / "test.db")
        db = DatabaseManager(db_path=db_path)
        db.initialize()

        # Add some data
        session = db.get_session()
        run = WorkflowRun(
            run_id=123456789,
            workflow_name="Test",
            status="completed",
        )
        session.add(run)
        session.commit()

        # Verify data exists
        result = session.query(WorkflowRun).filter_by(run_id=123456789).first()
        assert result is not None
        session.close()

        # Reset database
        db.reset()

        # Verify data is gone
        session = db.get_session()
        result = session.query(WorkflowRun).filter_by(run_id=123456789).first()
        assert result is None
        session.close()
        db.close()

    def test_context_manager(self, tmp_path):
        """Test DatabaseManager as context manager."""
        db_path = str(tmp_path / "test.db")

        with DatabaseManager(db_path=db_path) as db:
            db.initialize()
            session = db.get_session()
            session.close()

        # Database should be closed after context exit

    def test_in_memory_database(self):
        """Test using in-memory database."""
        db = DatabaseManager(db_path=":memory:")
        db.initialize()

        session = db.get_session()
        run = WorkflowRun(
            run_id=123456789,
            workflow_name="Test",
            status="completed",
        )
        session.add(run)
        session.commit()

        result = session.query(WorkflowRun).filter_by(run_id=123456789).first()
        assert result is not None
        session.close()
        db.close()


class TestDatabaseManagerEdgeCases:
    """Test edge cases and error paths for DatabaseManager."""

    def test_database_manager_default_path_creation(self, tmp_path, monkeypatch):
        """Test that DatabaseManager creates default path when none provided."""
        # Set HOME to a temporary directory
        home_dir = tmp_path / "test_home"
        home_dir.mkdir()
        monkeypatch.setenv("HOME", str(home_dir))

        # Mock Path.home() to return our test directory
        from pathlib import Path
        from unittest.mock import patch

        with patch.object(Path, "home", return_value=home_dir):
            db = DatabaseManager()
            db.initialize()

            # Verify the default path was created
            assert ".scout" in db.db_path
            scout_dir = home_dir / ".scout"
            assert scout_dir.exists()

            db.close()

    def test_engine_property_before_initialization_raises(self):
        """Test that accessing engine before initialize() raises RuntimeError."""
        db = DatabaseManager(":memory:")

        with pytest.raises(RuntimeError, match="Database not initialized"):
            _ = db.engine

    def test_database_reset_drops_and_recreates_tables(self):
        """Test that reset() drops all tables and recreates them."""
        db = DatabaseManager(":memory:")
        db.initialize()

        # Add some data
        session = db.get_session()
        run = WorkflowRun(
            run_id=999,
            workflow_name="Test",
            status="completed",
        )
        session.add(run)
        session.commit()

        # Verify data exists
        result = session.query(WorkflowRun).filter_by(run_id=999).first()
        assert result is not None
        session.close()

        # Reset database
        db.reset()

        # Verify data is gone
        session = db.get_session()
        result = session.query(WorkflowRun).filter_by(run_id=999).first()
        assert result is None
        session.close()

        db.close()

    def test_database_manager_with_echo_enabled(self):
        """Test DatabaseManager with SQL echo enabled."""
        db = DatabaseManager(":memory:", echo=True)
        db.initialize()

        # Verify engine has echo enabled
        assert db.engine.echo is True

        db.close()

    def test_database_context_manager(self):
        """Test DatabaseManager as context manager."""
        with DatabaseManager(":memory:") as db:
            db.initialize()
            session = db.get_session()
            assert session is not None
            session.close()

        # After exiting context, engine should be disposed
        assert db._engine is None

    def test_close_without_initialization(self):
        """Test that close() works even if database wasn't initialized."""
        db = DatabaseManager(":memory:")
        db.close()  # Should not raise an error
        assert db._engine is None
