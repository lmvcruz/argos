"""Reports module for generating CI health and test execution reports."""

from lens.reports.html_generator import HTMLReportGenerator
from lens.reports.test_execution_report import TestExecutionReportGenerator

__all__ = ["HTMLReportGenerator", "TestExecutionReportGenerator"]
