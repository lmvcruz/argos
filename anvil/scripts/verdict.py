#!/usr/bin/env python
"""
Verdict CLI - Custom test discovery and validation tool.

Usage:
    python verdict.py --list [validator]          List test cases
    python verdict.py [validator] [--cases path]   Run test cases
"""

from anvil.testing.verdict_runner import VerdictCLI
import sys
from pathlib import Path

# Add anvil to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point."""
    config_path = project_root / "tests" / "validation" / "config.yaml"

    cli = VerdictCLI(config_path)
    return cli.run(sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
