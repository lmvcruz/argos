"""Test what paths rglob returns."""
from pathlib import Path
import tempfile

# Create a temporary directory
with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)
    
    # Create a simple file
    (tmpdir / "test.txt").write_text("hi")
    
    # See what rglob returns
    for p in tmpdir.rglob("*.txt"):
        print(f"Path: {p}")
        print(f"  Type: {type(p)}")
        print(f"  Is resolved: {p == p.resolve()}")
        print(f"  Resolved: {p.resolve()}")
