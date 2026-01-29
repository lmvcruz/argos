"""Debug script to understand symlink behavior."""
from pathlib import Path
import tempfile
import os

# Create a temporary directory
with tempfile.TemporaryDirectory() as tmpdir:
    tmpdir = Path(tmpdir)

    # Create project structure
    project = tmpdir / "project"
    project.mkdir()

    # Create external directory
    external = tmpdir / "external"
    external.mkdir()
    (external / "external.py").write_text("# external")

    # Create symlink
    try:
        linked = project / "linked"
        linked.symlink_to(external)
        print(f"Created symlink: {linked} -> {external}")
        print(f"Is linked a symlink? {linked.is_symlink()}")
        print(f"Does linked exist? {linked.exists()}")

        # Now use rglob to find Python files
        print("\nUsing rglob to find *.py files:")
        for file_path in project.rglob("*.py"):
            print(f"  Found: {file_path}")
            print(f"    Is file a symlink? {file_path.is_symlink()}")
            print(f"    Parent: {file_path.parent}")
            print(f"    Is parent a symlink? {file_path.parent.is_symlink()}")

            # Check if any parent is a symlink
            current = file_path.parent
            while current != project:
                print(f"    Checking {current}: is_symlink={current.is_symlink()}")
                try:
                    current.relative_to(project)
                    print(f"      {current} is within {project}")
                except ValueError:
                    print(f"      {current} is OUTSIDE {project}")
                    break
                current = current.parent

    except OSError as e:
        print(f"Cannot create symlink: {e}")
