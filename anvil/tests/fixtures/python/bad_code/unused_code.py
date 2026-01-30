"""
Python file with unused imports and variables.

This fixture has unused code that should be detected by autoflake.
"""

import json  # Unused import
import os  # Used
import sys  # Unused import
from pathlib import Path  # Unused import
from typing import Dict, List, Optional, Tuple  # Only Dict is used


def process_data(data: Dict[str, str]) -> None:
    """Process some data."""

    # Only this variable is actually used
    used_var = data.get("key", "default")
    print(f"Processing: {used_var}")


def helper_function():
    """This function is never called."""
    return "Unused function"


UNUSED_CONSTANT = "This constant is never referenced"
USED_CONSTANT = "env"


def main():
    """Main function."""
    env = os.getenv(USED_CONSTANT, "default")
    process_data({"key": env})


if __name__ == "__main__":
    main()
