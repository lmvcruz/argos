"""Debug script to test anvil check command."""
import sys

# Add the package to path
sys.path.insert(0, ".")

# Simple test of CLI
from anvil.cli.main import main

try:
    result = main(["check", "--verbose"])
    print(f"\nExit code: {result}")
except Exception as e:
    import traceback
    print(f"\nException: {e}")
    traceback.print_exc()
