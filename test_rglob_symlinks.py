"""
Test script to understand Path.rglob() behavior with symbolic links.

This script creates a test directory structure with symlinks and observes
how rglob() behaves in different scenarios.
"""

from pathlib import Path
import os
import tempfile
import shutil

def test_rglob_symlink_behavior():
    """Test how rglob() handles symbolic links."""

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create directory structure:
        # base/
        #   real_dir/
        #     file1.py
        #     file2.py
        #   project/
        #     actual.py
        #     linked_dir -> ../real_dir (symlink)

        real_dir = base / "real_dir"
        real_dir.mkdir()
        (real_dir / "file1.py").write_text("# file1")
        (real_dir / "file2.py").write_text("# file2")

        project = base / "project"
        project.mkdir()
        (project / "actual.py").write_text("# actual")

        # Create symlink (Windows may require admin privileges)
        symlink_path = project / "linked_dir"
        try:
            symlink_path.symlink_to(real_dir, target_is_directory=True)
        except OSError as e:
            print(f"Could not create symlink (may need admin privileges on Windows): {e}")
            return

        print("=" * 70)
        print("DIRECTORY STRUCTURE:")
        print("=" * 70)
        print(f"real_dir: {real_dir}")
        print(f"  - file1.py")
        print(f"  - file2.py")
        print(f"project: {project}")
        print(f"  - actual.py")
        print(f"  - linked_dir -> {real_dir} (symlink)")
        print()

        # Test 1: Does rglob() follow symlinks by default?
        print("=" * 70)
        print("TEST 1: Does rglob() follow symlinks by default?")
        print("=" * 70)
        all_py_files = list(project.rglob("*.py"))
        print(f"project.rglob('*.py') found {len(all_py_files)} files:")
        for f in all_py_files:
            print(f"  - {f}")
        print()

        # Test 2: What paths are returned when going through symlinks?
        print("=" * 70)
        print("TEST 2: Paths returned when traversing through symlinks")
        print("=" * 70)
        for f in all_py_files:
            print(f"Path: {f}")
            print(f"  - Relative to project: {f.relative_to(project)}")
            print(f"  - Is absolute: {f.is_absolute()}")
            print(f"  - Exists: {f.exists()}")
            print(f"  - Resolved: {f.resolve()}")

            # Check each parent to see if any are symlinks
            for parent in [f] + list(f.parents):
                if parent == base:
                    break
                if parent.is_symlink():
                    print(f"  - SYMLINK FOUND in path: {parent}")
            print()

        # Test 3: is_symlink() on intermediate directories
        print("=" * 70)
        print("TEST 3: Testing is_symlink() on path components")
        print("=" * 70)
        symlinked_file_path = project / "linked_dir" / "file1.py"
        print(f"Checking: {symlinked_file_path}")
        print(f"  - Full path exists: {symlinked_file_path.exists()}")
        print(f"  - (project / 'linked_dir').is_symlink(): {(project / 'linked_dir').is_symlink()}")
        print(f"  - symlinked_file_path.is_symlink(): {symlinked_file_path.is_symlink()}")
        print(f"  - symlinked_file_path.parent.is_symlink(): {symlinked_file_path.parent.is_symlink()}")
        print()

        # Test 4: Check Python version support for recurse_symlinks
        print("=" * 70)
        print("TEST 4: Checking for recurse_symlinks parameter (Python 3.13+)")
        print("=" * 70)
        import inspect
        sig = inspect.signature(Path.rglob)
        print(f"Path.rglob signature: {sig}")
        print(f"Parameters: {list(sig.parameters.keys())}")

        # Try to use recurse_symlinks if available
        try:
            # This will fail in Python < 3.13
            files_with_recurse = list(project.rglob("*.py", recurse_symlinks=False))
            print(f"\nrecurse_symlinks=False found {len(files_with_recurse)} files:")
            for f in files_with_recurse:
                print(f"  - {f}")
        except TypeError as e:
            print(f"\nrecurse_symlinks parameter not available: {e}")
        print()

        # Test 5: glob with ** wildcard
        print("=" * 70)
        print("TEST 5: Using glob('**/*.py') vs rglob('*.py')")
        print("=" * 70)
        glob_files = list(project.glob("**/*.py"))
        rglob_files = list(project.rglob("*.py"))
        print(f"glob('**/*.py'): {len(glob_files)} files")
        print(f"rglob('*.py'): {len(rglob_files)} files")
        print(f"Results identical: {set(glob_files) == set(rglob_files)}")
        print()

if __name__ == "__main__":
    import sys
    print(f"Python version: {sys.version}")
    print()
    test_rglob_symlink_behavior()
