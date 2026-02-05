"""
Additional tests for Scout models to improve coverage.

Tests for CaseIdentifier error cases and edge conditions.
"""

import pytest

from scout.models import CaseIdentifier, FetchOptions


class TestCaseIdentifierValidation:
    """Test CaseIdentifier validation in __post_init__."""

    def test_missing_workflow_name(self):
        """Test CaseIdentifier with missing workflow_name."""
        with pytest.raises(ValueError, match="workflow_name is required"):
            CaseIdentifier(workflow_name="", run_id=123, job_id="job1")

    def test_missing_both_execution_ids(self):
        """Test CaseIdentifier with neither run_id nor execution_number."""
        with pytest.raises(ValueError, match="Either run_id or execution_number"):
            CaseIdentifier(workflow_name="test-workflow", job_id="job1")

    def test_missing_both_job_ids(self):
        """Test CaseIdentifier with neither job_id nor action_name."""
        with pytest.raises(ValueError, match="Either job_id or action_name"):
            CaseIdentifier(workflow_name="test-workflow", run_id=123)

    def test_valid_with_run_id_and_job_id(self):
        """Test CaseIdentifier with valid run_id and job_id."""
        case = CaseIdentifier(workflow_name="test-workflow", run_id=123, job_id="job1")
        assert case.workflow_name == "test-workflow"
        assert case.run_id == 123
        assert case.job_id == "job1"

    def test_valid_with_execution_number_and_action_name(self):
        """Test CaseIdentifier with valid execution_number and action_name."""
        case = CaseIdentifier(
            workflow_name="test-workflow", execution_number=5, action_name="action1"
        )
        assert case.workflow_name == "test-workflow"
        assert case.execution_number == 5
        assert case.action_name == "action1"


class TestCaseIdentifierGetExecutionId:
    """Test CaseIdentifier.get_execution_id() method."""

    def test_get_execution_id_with_run_id(self):
        """Test get_execution_id when run_id is set."""
        case = CaseIdentifier(workflow_name="test-workflow", run_id=123, job_id="job1")
        assert case.get_execution_id() == 123

    def test_get_execution_id_with_execution_number_only(self):
        """Test get_execution_id when only execution_number is set."""
        case = CaseIdentifier(workflow_name="test-workflow", execution_number=5, job_id="job1")
        with pytest.raises(ValueError, match="run_id not set"):
            case.get_execution_id()

    def test_get_execution_id_raises_on_missing_both(self):
        """Test that __post_init__ prevents creating case without execution ID."""
        # __post_init__ validation ensures we can't reach the defensive check
        # This test documents the invariant
        with pytest.raises(ValueError, match="Either run_id or execution_number"):
            CaseIdentifier(workflow_name="test-workflow", job_id="job1")

    def test_get_execution_id_no_ids_available(self):
        """Test the defensive check when neither execution ID is set."""
        # Create a valid case first, then manually break the invariant
        # This tests the "raise ValueError('No execution ID available')" line 72
        case = CaseIdentifier(workflow_name="test-workflow", run_id=123, job_id="job1")
        # Remove both IDs to test the defensive clause
        object.__setattr__(case, "run_id", None)
        object.__setattr__(case, "execution_number", None)

        with pytest.raises(ValueError, match="No execution ID available"):
            case.get_execution_id()


class TestCaseIdentifierGetJobId:
    """Test CaseIdentifier.get_job_id() method."""

    def test_get_job_id_with_job_id(self):
        """Test get_job_id when job_id is set."""
        case = CaseIdentifier(workflow_name="test-workflow", run_id=123, job_id="job1")
        assert case.get_job_id() == "job1"

    def test_get_job_id_with_action_name_only(self):
        """Test get_job_id when only action_name is set."""
        case = CaseIdentifier(workflow_name="test-workflow", run_id=123, action_name="action1")
        with pytest.raises(ValueError, match="job_id not set"):
            case.get_job_id()

    def test_get_job_id_raises_on_missing_both(self):
        """Test that __post_init__ prevents creating case without job ID."""
        # __post_init__ validation ensures we can't reach the defensive check
        # This test documents the invariant
        with pytest.raises(ValueError, match="Either job_id or action_name"):
            CaseIdentifier(workflow_name="test-workflow", run_id=123)

    def test_get_job_id_no_ids_available(self):
        """Test the defensive check when neither job ID is set."""
        # Create a valid case first, then manually break the invariant
        # This tests the "raise ValueError('No job ID available')" line 89
        case = CaseIdentifier(workflow_name="test-workflow", run_id=123, job_id="job1")
        # Remove both IDs to test the defensive clause
        object.__setattr__(case, "job_id", None)
        object.__setattr__(case, "action_name", None)

        with pytest.raises(ValueError, match="No job ID available"):
            case.get_job_id()


class TestCaseIdentifierTriple:
    """Test CaseIdentifier.triple property."""

    def test_triple_with_all_ids(self):
        """Test triple property returns correct tuple."""
        case = CaseIdentifier(workflow_name="test-workflow", run_id=123, job_id="job1")
        assert case.triple == ("test-workflow", 123, "job1")

    def test_triple_with_execution_number(self):
        """Test triple property with execution_number."""
        case = CaseIdentifier(workflow_name="test-workflow", execution_number=5, job_id="job1")
        assert case.triple == ("test-workflow", None, "job1")


class TestCaseIdentifierRepr:
    """Test CaseIdentifier.__repr__() method."""

    def test_repr_with_run_id_and_job_id(self):
        """Test string representation with run_id and job_id."""
        case = CaseIdentifier(workflow_name="test-workflow", run_id=123, job_id="job1")
        repr_str = repr(case)
        assert "test-workflow" in repr_str
        assert "123" in repr_str
        assert "job1" in repr_str

    def test_repr_with_execution_number_and_action_name(self):
        """Test string representation with execution_number and action_name."""
        case = CaseIdentifier(
            workflow_name="test-workflow", execution_number=5, action_name="action1"
        )
        repr_str = repr(case)
        assert "test-workflow" in repr_str
        assert "5" in repr_str
        assert "action1" in repr_str


class TestFetchOptions:
    """Test FetchOptions dataclass."""

    def test_fetch_options_defaults(self):
        """Test FetchOptions with default values."""
        opts = FetchOptions()
        assert opts.output_file is None
        assert opts.save_execution is False

    def test_fetch_options_custom(self):
        """Test FetchOptions with custom values."""
        opts = FetchOptions(output_file="results.json", save_execution=True)
        assert opts.output_file == "results.json"
        assert opts.save_execution is True
