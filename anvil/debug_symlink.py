"""Debug script to test symlink detection logic."""
import os
import tempfile
from pathlib import Path

# Create a temporary directory structure
with tempfile.TemporaryDirectory() as tmpdir:
    tmp_path = Path(tmpdir)

    # Create main project directory
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "main.py").write_text("# main")

    # Create external directory with file
    external_dir = tmp_path / "external"
    external_dir.mkdir()
    (external_dir / "external.py").write_text("# external")

    # Create symlink
    try:
        symlink_path = project_dir / "linked"
        symlink_path.symlink_to(external_dir)
        print(f"✓ Created symlink: {symlink_path} -> {external_dir}")
    except OSError as e:
        print(f"✗ Cannot create symlink: {e}")
        exit(1)

    # Test different ways to check if it's a symlink
    print(f"\nChecking symlink: {symlink_path}")
    print(f"  symlink_path.exists(): {symlink_path.exists()}")
    print(f"  symlink_path.is_symlink(): {symlink_path.is_symlink()}")
    print(f"  symlink_path.is_dir(): {symlink_path.is_dir()}")
    print(f"  os.path.islink(symlink_path): {os.path.islink(symlink_path)}")

    # Now test os.walk behavior
    print(f"\nTesting os.walk with followlinks=False:")
    for dirpath, dirnames, filenames in os.walk(project_dir, followlinks=False):
        dir_path = Path(dirpath)
        print(f"  dirpath: {dirpath}")
        print(f"  dirnames: {dirnames}")
        print(f"  filenames: {filenames}")

        # Check each dirname
        for d in dirnames:
            full_path = dir_path / d
            is_symlink = full_path.is_symlink()
            print(f"    Checking {d}: is_symlink={is_symlink}, path={full_path}")

    print(f"\nTesting os.walk with followlinks=True:")
    for dirpath, dirnames, filenames in os.walk(project_dir, followlinks=True):
        dir_path = Path(dirpath)
        print(f"  dirpath: {dirpath}")
        print(f"  dirnames: {dirnames}")
        print(f"  filenames: {filenames}")
