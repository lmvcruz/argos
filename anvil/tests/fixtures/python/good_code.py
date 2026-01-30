"""
Good Python code sample.

This module demonstrates well-formatted, PEP 8 compliant Python code
that should pass all validators.
"""

import sys
from pathlib import Path
from typing import List, Optional


def calculate_sum(numbers: List[int]) -> int:
    """
    Calculate the sum of a list of numbers.

    Args:
        numbers: List of integers to sum

    Returns:
        The sum of all numbers in the list
    """
    return sum(numbers)


def process_file(file_path: str) -> Optional[str]:
    """
    Read and process a file.

    Args:
        file_path: Path to the file to process

    Returns:
        File contents if successful, None otherwise
    """
    path = Path(file_path)
    if not path.exists():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content.strip()
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        return None


class DataProcessor:
    """Process data with configurable options."""

    def __init__(self, name: str, debug: bool = False):
        """
        Initialize the processor.

        Args:
            name: Name of the processor
            debug: Enable debug output
        """
        self.name = name
        self.debug = debug
        self._data: List[str] = []

    def add_data(self, item: str) -> None:
        """Add an item to the data list."""
        self._data.append(item)
        if self.debug:
            print(f"Added item: {item}")

    def get_count(self) -> int:
        """Get the number of items."""
        return len(self._data)


if __name__ == "__main__":
    # Example usage
    processor = DataProcessor("example", debug=True)
    processor.add_data("item1")
    processor.add_data("item2")
    print(f"Total items: {processor.get_count()}")
