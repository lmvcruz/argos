"""
CI data collection module.

This module provides clients for fetching CI data from various providers
and storing it in the Scout database.
"""

from scout.ci.github_actions_client import GitHubActionsClient

__all__ = ["GitHubActionsClient"]
