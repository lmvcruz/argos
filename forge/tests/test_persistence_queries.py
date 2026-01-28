"""
Tests for data query methods (Step 6.5).

This module tests the get_recent_builds() and get_build_statistics() methods
that retrieve and aggregate persisted build data.
"""

from datetime import datetime, timedelta

import pytest

from forge.models.metadata import (
    BuildMetadata,
    BuildTarget,
    BuildWarning,
    ConfigureMetadata,
    Error,
)
from forge.models.results import BuildResult, ConfigureResult
from forge.storage.data_persistence import DataPersistence


@pytest.fixture
def persistence(tmp_path):
    """Create a DataPersistence instance with temporary database."""
    db_path = tmp_path / "test.db"
    return DataPersistence(db_path)


def create_sample_configuration(persistence, project_name="TestProject"):
    """Helper to create and save a configuration, return configuration_id."""
    result = ConfigureResult(
        success=True,
        exit_code=0,
        duration=3.5,
        stdout="Configure output",
        stderr="",
        start_time=datetime(2024, 1, 15, 10, 0, 0),
        end_time=datetime(2024, 1, 15, 10, 3, 30),
    )
    metadata = ConfigureMetadata(
        project_name=project_name,
        cmake_version="3.25.0",
        generator="Ninja",
        build_type="Release",
        compiler_c="gcc",
        compiler_cxx="g++",
        system_name="Linux",
        system_version="5.15.0",
        found_packages=["Boost", "Qt5"],
    )
    return persistence.save_configuration(result, metadata)


def create_sample_build(
    persistence,
    configuration_id=None,
    project_name="TestProject",
    success=True,
    warnings_count=0,
    errors_count=0,
    start_time=None,
    duration=5.0,
):
    """Helper to create and save a build, return build_id."""
    if start_time is None:
        start_time = datetime(2024, 1, 15, 14, 32, 0)

    result = BuildResult(
        success=success,
        exit_code=0 if success else 1,
        duration=duration,
        stdout="Build output",
        stderr="",
        start_time=start_time,
        end_time=start_time + timedelta(seconds=duration),
    )

    warnings = [
        BuildWarning(file=f"file{i}.cpp", line=i, column=1, message=f"Warning {i}")
        for i in range(warnings_count)
    ]

    errors = [
        Error(file=f"file{i}.cpp", line=i, column=1, message=f"Error {i}")
        for i in range(errors_count)
    ]

    metadata = BuildMetadata(
        project_name=project_name,
        targets=[BuildTarget(name="app", target_type="executable")],
        warnings=warnings,
        errors=errors,
    )

    return persistence.save_build(result, metadata, configuration_id)


class TestGetRecentBuildsBasic:
    """Test basic get_recent_builds() functionality."""

    def test_get_recent_builds_returns_empty_list_when_no_builds(self, persistence):
        """Test that get_recent_builds returns empty list when no builds exist."""
        builds = persistence.get_recent_builds()

        assert builds == []
        assert isinstance(builds, list)

    def test_get_recent_builds_returns_single_build(self, persistence):
        """Test retrieving a single build."""
        build_id = create_sample_build(persistence)

        builds = persistence.get_recent_builds()

        assert len(builds) == 1
        assert builds[0]["id"] == build_id
        assert builds[0]["project_name"] == "TestProject"
        assert builds[0]["success"] is True

    def test_get_recent_builds_returns_multiple_builds(self, persistence):
        """Test retrieving multiple builds."""
        build_id1 = create_sample_build(
            persistence, project_name="Project1", start_time=datetime(2024, 1, 15, 10, 0, 0)
        )
        build_id2 = create_sample_build(
            persistence, project_name="Project2", start_time=datetime(2024, 1, 15, 11, 0, 0)
        )
        build_id3 = create_sample_build(
            persistence, project_name="Project3", start_time=datetime(2024, 1, 15, 12, 0, 0)
        )

        builds = persistence.get_recent_builds()

        assert len(builds) == 3
        # Verify IDs are present (order will be tested separately)
        build_ids = [b["id"] for b in builds]
        assert build_id1 in build_ids
        assert build_id2 in build_ids
        assert build_id3 in build_ids


class TestGetRecentBuildsOrdering:
    """Test ordering of get_recent_builds() results."""

    def test_get_recent_builds_ordered_by_timestamp_newest_first(self, persistence):
        """Test that builds are ordered by timestamp, newest first."""
        # Create builds with different timestamps
        build_id1 = create_sample_build(persistence, start_time=datetime(2024, 1, 15, 10, 0, 0))
        build_id2 = create_sample_build(persistence, start_time=datetime(2024, 1, 15, 12, 0, 0))
        build_id3 = create_sample_build(persistence, start_time=datetime(2024, 1, 15, 11, 0, 0))

        builds = persistence.get_recent_builds()

        # Should be ordered: build_id2 (12:00), build_id3 (11:00), build_id1 (10:00)
        assert len(builds) == 3
        assert builds[0]["id"] == build_id2
        assert builds[1]["id"] == build_id3
        assert builds[2]["id"] == build_id1


class TestGetRecentBuildsLimit:
    """Test limit parameter of get_recent_builds()."""

    def test_get_recent_builds_with_default_limit(self, persistence):
        """Test default limit (should return at most 10 builds)."""
        # Create 15 builds
        for i in range(15):
            create_sample_build(
                persistence,
                start_time=datetime(2024, 1, 15, 10, 0, 0) + timedelta(minutes=i),
            )

        builds = persistence.get_recent_builds()

        # Default limit should be 10
        assert len(builds) == 10

    def test_get_recent_builds_with_custom_limit(self, persistence):
        """Test custom limit parameter."""
        # Create 10 builds
        for i in range(10):
            create_sample_build(
                persistence,
                start_time=datetime(2024, 1, 15, 10, 0, 0) + timedelta(minutes=i),
            )

        builds = persistence.get_recent_builds(limit=5)

        assert len(builds) == 5

    def test_get_recent_builds_limit_larger_than_available(self, persistence):
        """Test limit larger than number of available builds."""
        # Create 3 builds
        for i in range(3):
            create_sample_build(
                persistence,
                start_time=datetime(2024, 1, 15, 10, 0, 0) + timedelta(minutes=i),
            )

        builds = persistence.get_recent_builds(limit=10)

        # Should return all 3 builds
        assert len(builds) == 3


class TestGetRecentBuildsFiltering:
    """Test filtering of get_recent_builds() by project name."""

    def test_get_recent_builds_filter_by_project_name(self, persistence):
        """Test filtering by project name."""
        create_sample_build(persistence, project_name="ProjectA")
        create_sample_build(persistence, project_name="ProjectB")
        create_sample_build(persistence, project_name="ProjectA")
        create_sample_build(persistence, project_name="ProjectC")

        builds = persistence.get_recent_builds(project_name="ProjectA")

        assert len(builds) == 2
        for build in builds:
            assert build["project_name"] == "ProjectA"

    def test_get_recent_builds_filter_returns_empty_when_no_match(self, persistence):
        """Test filtering with project name that doesn't exist."""
        create_sample_build(persistence, project_name="ProjectA")
        create_sample_build(persistence, project_name="ProjectB")

        builds = persistence.get_recent_builds(project_name="NonExistent")

        assert builds == []

    def test_get_recent_builds_filter_respects_limit(self, persistence):
        """Test that filtering and limit work together."""
        # Create 5 builds for ProjectA
        for i in range(5):
            create_sample_build(
                persistence,
                project_name="ProjectA",
                start_time=datetime(2024, 1, 15, 10, 0, 0) + timedelta(minutes=i),
            )

        # Create 3 builds for ProjectB
        for i in range(3):
            create_sample_build(
                persistence,
                project_name="ProjectB",
                start_time=datetime(2024, 1, 15, 10, 0, 0) + timedelta(minutes=i),
            )

        builds = persistence.get_recent_builds(project_name="ProjectA", limit=3)

        assert len(builds) == 3
        for build in builds:
            assert build["project_name"] == "ProjectA"


class TestGetRecentBuildsReturnedFields:
    """Test fields returned by get_recent_builds()."""

    def test_get_recent_builds_includes_all_required_fields(self, persistence):
        """Test that returned builds include all necessary fields."""
        build_id = create_sample_build(
            persistence,
            success=False,
            warnings_count=5,
            errors_count=3,
            duration=12.5,
        )

        builds = persistence.get_recent_builds()

        assert len(builds) == 1
        build = builds[0]

        # Check required fields
        assert "id" in build
        assert "project_name" in build
        assert "success" in build
        assert "duration" in build
        assert "warning_count" in build
        assert "error_count" in build
        assert "build_time" in build

        # Check values
        assert build["id"] == build_id
        assert build["success"] is False
        assert build["duration"] == 12.5
        assert build["warning_count"] == 5
        assert build["error_count"] == 3

    def test_get_recent_builds_includes_timestamp_as_string(self, persistence):
        """Test that build_time is returned as ISO format string."""
        create_sample_build(persistence, start_time=datetime(2024, 1, 15, 14, 32, 0))

        builds = persistence.get_recent_builds()

        assert len(builds) == 1
        assert isinstance(builds[0]["build_time"], str)
        assert "2024-01-15" in builds[0]["build_time"]


class TestGetBuildStatisticsBasic:
    """Test basic get_build_statistics() functionality."""

    def test_get_build_statistics_returns_empty_stats_when_no_builds(self, persistence):
        """Test statistics with no builds in database."""
        stats = persistence.get_build_statistics()

        assert stats is not None
        assert stats["total_builds"] == 0
        assert stats["successful_builds"] == 0
        assert stats["failed_builds"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["average_duration"] == 0.0
        assert stats["total_warnings"] == 0
        assert stats["total_errors"] == 0

    def test_get_build_statistics_single_successful_build(self, persistence):
        """Test statistics with a single successful build."""
        create_sample_build(
            persistence,
            success=True,
            duration=10.0,
            warnings_count=2,
            errors_count=0,
        )

        stats = persistence.get_build_statistics()

        assert stats["total_builds"] == 1
        assert stats["successful_builds"] == 1
        assert stats["failed_builds"] == 0
        assert stats["success_rate"] == 100.0
        assert stats["average_duration"] == 10.0
        assert stats["total_warnings"] == 2
        assert stats["total_errors"] == 0

    def test_get_build_statistics_single_failed_build(self, persistence):
        """Test statistics with a single failed build."""
        create_sample_build(
            persistence,
            success=False,
            duration=5.0,
            warnings_count=1,
            errors_count=3,
        )

        stats = persistence.get_build_statistics()

        assert stats["total_builds"] == 1
        assert stats["successful_builds"] == 0
        assert stats["failed_builds"] == 1
        assert stats["success_rate"] == 0.0
        assert stats["average_duration"] == 5.0
        assert stats["total_warnings"] == 1
        assert stats["total_errors"] == 3


class TestGetBuildStatisticsCalculations:
    """Test statistics calculations with multiple builds."""

    def test_get_build_statistics_multiple_builds(self, persistence):
        """Test statistics with multiple builds."""
        # 3 successful builds
        create_sample_build(persistence, success=True, duration=10.0, warnings_count=2)
        create_sample_build(persistence, success=True, duration=15.0, warnings_count=1)
        create_sample_build(persistence, success=True, duration=5.0, warnings_count=0)

        # 2 failed builds
        create_sample_build(persistence, success=False, duration=8.0, errors_count=2)
        create_sample_build(persistence, success=False, duration=12.0, errors_count=1)

        stats = persistence.get_build_statistics()

        assert stats["total_builds"] == 5
        assert stats["successful_builds"] == 3
        assert stats["failed_builds"] == 2
        assert stats["success_rate"] == 60.0  # 3/5 = 60%
        assert stats["average_duration"] == 10.0  # (10+15+5+8+12)/5 = 50/5 = 10
        assert stats["total_warnings"] == 3  # 2+1+0
        assert stats["total_errors"] == 3  # 2+1

    def test_get_build_statistics_success_rate_precision(self, persistence):
        """Test success rate calculation precision."""
        # 2 successful, 1 failed = 66.67%
        create_sample_build(persistence, success=True)
        create_sample_build(persistence, success=True)
        create_sample_build(persistence, success=False)

        stats = persistence.get_build_statistics()

        assert stats["success_rate"] == pytest.approx(66.67, rel=0.01)

    def test_get_build_statistics_average_duration_precision(self, persistence):
        """Test average duration calculation precision."""
        create_sample_build(persistence, duration=3.7)
        create_sample_build(persistence, duration=5.2)
        create_sample_build(persistence, duration=4.1)

        stats = persistence.get_build_statistics()

        # Average: (3.7 + 5.2 + 4.1) / 3 = 13.0 / 3 = 4.333...
        assert stats["average_duration"] == pytest.approx(4.33, rel=0.01)


class TestGetBuildStatisticsFiltering:
    """Test filtering of get_build_statistics() by project name."""

    def test_get_build_statistics_filter_by_project_name(self, persistence):
        """Test statistics filtered by project name."""
        # ProjectA: 2 successful, 1 failed
        create_sample_build(persistence, project_name="ProjectA", success=True, duration=10.0)
        create_sample_build(persistence, project_name="ProjectA", success=True, duration=15.0)
        create_sample_build(persistence, project_name="ProjectA", success=False, duration=5.0)

        # ProjectB: 1 successful, 1 failed
        create_sample_build(persistence, project_name="ProjectB", success=True, duration=8.0)
        create_sample_build(persistence, project_name="ProjectB", success=False, duration=12.0)

        stats = persistence.get_build_statistics(project_name="ProjectA")

        assert stats["total_builds"] == 3
        assert stats["successful_builds"] == 2
        assert stats["failed_builds"] == 1
        assert stats["success_rate"] == pytest.approx(66.67, rel=0.01)
        assert stats["average_duration"] == 10.0  # (10+15+5)/3

    def test_get_build_statistics_filter_returns_empty_when_no_match(self, persistence):
        """Test statistics with project name that doesn't exist."""
        create_sample_build(persistence, project_name="ProjectA")
        create_sample_build(persistence, project_name="ProjectB")

        stats = persistence.get_build_statistics(project_name="NonExistent")

        assert stats["total_builds"] == 0
        assert stats["success_rate"] == 0.0


class TestGetBuildStatisticsEdgeCases:
    """Test edge cases for get_build_statistics()."""

    def test_get_build_statistics_with_zero_duration_builds(self, persistence):
        """Test statistics when some builds have zero duration."""
        create_sample_build(persistence, duration=0.0)
        create_sample_build(persistence, duration=10.0)

        stats = persistence.get_build_statistics()

        assert stats["average_duration"] == 5.0  # (0+10)/2

    def test_get_build_statistics_with_large_numbers(self, persistence):
        """Test statistics with large warning/error counts."""
        create_sample_build(persistence, warnings_count=1000, errors_count=500)
        create_sample_build(persistence, warnings_count=2000, errors_count=1500)

        stats = persistence.get_build_statistics()

        assert stats["total_warnings"] == 3000
        assert stats["total_errors"] == 2000


class TestQueryPerformance:
    """Test query performance with larger datasets."""

    def test_get_recent_builds_performance_with_many_builds(self, persistence):
        """Test query performance with 100 builds."""
        # Create 100 builds
        for i in range(100):
            create_sample_build(
                persistence,
                project_name=f"Project{i % 5}",  # 5 different projects
                start_time=datetime(2024, 1, 1, 0, 0, 0) + timedelta(minutes=i),
            )

        # Query should complete quickly
        builds = persistence.get_recent_builds(limit=20)

        assert len(builds) == 20
        # Verify ordering (newest first)
        for i in range(len(builds) - 1):
            assert builds[i]["build_time"] >= builds[i + 1]["build_time"]

    def test_get_build_statistics_performance_with_many_builds(self, persistence):
        """Test statistics calculation performance with 100 builds."""
        # Create 100 builds (80 successful, 20 failed)
        for i in range(100):
            create_sample_build(
                persistence,
                success=(i % 5 != 0),  # Every 5th build fails
                duration=float(i % 10 + 1),  # Duration 1-10
                warnings_count=i % 3,  # 0-2 warnings
                errors_count=(1 if i % 5 == 0 else 0),  # Errors only on failed builds
            )

        stats = persistence.get_build_statistics()

        assert stats["total_builds"] == 100
        assert stats["successful_builds"] == 80
        assert stats["failed_builds"] == 20
        assert stats["success_rate"] == 80.0
