import os
import tempfile
from pathlib import Path

# Create temp structure
td = Path(tempfile.mkdtemp())
real_dir = td / 'real'
real_dir.mkdir()
(real_dir / 'file.txt').write_text('test')

try:
    link_dir = td / 'link'
    link_dir.symlink_to(real_dir)
    
    print(f"Created structure in {td}:")
    print(f"  real/file.txt")
    print(f"  link -> real/")
    print()
    
    print("With followlinks=False:")
    for root, dirs, files in os.walk(td, followlinks=False):
        print(f"  root: {root}")
        print(f"  dirs: {dirs}")
        print(f"  files: {files}")
    print()
    
    print("With followlinks=True:")
    for root, dirs, files in os.walk(td, followlinks=True):
        print(f"  root: {root}")
        print(f"  dirs: {dirs}")
        print(f"  files: {files}")
except OSError as e:
    print(f'No symlink support: {e}')
