"""
Anvil - Code Quality Gate Tool

Entry point for running Anvil as a module: python -m anvil
"""

import sys

from anvil.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
