"""
Pytest configuration for Scout tests.
"""

import sys
from pathlib import Path

# Add scout package to path for imports
scout_root = Path(__file__).parent.parent
sys.path.insert(0, str(scout_root))
