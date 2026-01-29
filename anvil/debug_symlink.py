"""Debug script to understand symlink test failure."""

from pathlib import Path
import tempfile
import shutil

# Create test structure
with tempfile.TemporaryDirectory() as tmpdir:
    tmppath = Path(tmpdir)
    
    # Create external directory with file
    external_dir = tmppath / "external"
    external_dir.mkdir()
    (external_dir / "external.py").write_text("# external")
    
    # Create project directory
    project = tmppath / "project"
    project.mkdir()
    (project / "main.py").write_text("# main")
    
    # Create symlink to external directory
    try:
        symlink_path = project / "linked"
        symlink_path.symlink_to(external_dir)
        
        print(f"Project root: {project}")
        print(f"Symlink: {symlink_path}")
        print(f"Symlink target: {external_dir}")
        print(f"Symlink is_symlink: {symlink_path.is_symlink()}")
        
        # Find all Python files
        all_files = list(project.rglob("**/*.py"))
        print(f"\nAll Python files found by rglob:")
        for f in all_files:
            print(f"  {f}")
            print(f"    is_file: {f.is_file()}")
            print(f"    is_symlink (file): {f.is_symlink()}")
            print(f"    parents: {list(f.parents)}")
            
            # Check each parent
            for parent in f.parents:
                if parent == project or parent in project.parents:
                    print(f"    Stopping at: {parent}")
                    break
                print(f"    Parent {parent}: is_symlink={parent.is_symlink()}")
                
    except OSError as e:
        print(f"Cannot create symlink: {e}")
