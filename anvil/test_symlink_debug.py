"""Test to reproduce the symlink issue."""

import tempfile
from pathlib import Path
import sys

# Add anvil to path
sys.path.insert(0, str(Path(__file__).parent))

from anvil.core.language_detector import LanguageDetector


def test_symlink_issue():
    """Reproduce the symlink test failure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Create temp_project
        temp_project = tmp_path / "project"
        temp_project.mkdir()
        (temp_project / "main.py").write_text("# main")
        
        # Create external directory with Python file
        external_dir = tmp_path / "external"
        external_dir.mkdir()
        (external_dir / "external.py").write_text("# external")
        
        # Create symlink (skip on Windows if fails)
        try:
            symlink_path = temp_project / "linked"
            symlink_path.symlink_to(external_dir)
            
            print(f"Created symlink: {symlink_path} -> {external_dir}")
            print(f"Symlink is_symlink(): {symlink_path.is_symlink()}")
            print(f"Symlink exists(): {symlink_path.exists()}")
            print()
            
            # Test with follow_symlinks=False
            detector = LanguageDetector(temp_project, follow_symlinks=False)
            files = detector.get_files_for_language("python")
            
            print("Files found:")
            for f in files:
                print(f"  {f}")
                print(f"    Relative: {f.relative_to(temp_project)}")
                contains = detector._contains_symlink(f)
                print(f"    Contains symlink: {contains}")
            print()
            
            # Check the assertion
            has_external = any(f.name == "external.py" for f in files)
            print(f"Has 'external.py': {has_external}")
            print(f"Expected: False (should NOT include symlinked files)")
            print(f"Test {'PASS' if not has_external else 'FAIL'}")
            
        except OSError as e:
            print(f"Cannot create symlink (Windows admin required): {e}")


if __name__ == "__main__":
    test_symlink_issue()
