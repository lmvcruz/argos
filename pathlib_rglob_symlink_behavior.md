# Path.rglob() Behavior with Symbolic Links

## Summary of Findings (Authoritative Documentation)

Based on the official Python documentation for versions 3.8-3.13:

---

## 1. Does rglob() follow symbolic links by default?

**Answer: YES, but with a critical exception**

From Python 3.13 documentation:
> "By default, or when the recurse_symlinks keyword-only argument is set to `False`, this method **follows symlinks except when expanding "**" wildcards**. Set recurse_symlinks to `True` to always follow symlinks."

**Key Behavior:**
- **Python 3.8-3.12**: `rglob()` DOES follow symlinks when traversing directories
  - No parameter exists to control this behavior
  - It follows symlinks to directories and continues the traversal
- **Python 3.13+**: Added `recurse_symlinks` parameter
  - Default is `recurse_symlinks=False`: follows symlinks except for `**` wildcards
  - Set to `True` to always follow symlinks

**Comparison to glob module** (from Python 3.13 docs):
> ""`**`" pattern components do not follow symlinks by default in pathlib. This behaviour has no equivalent in glob.glob(), but you can pass `recurse_symlinks=True` to Path.glob() for compatible behaviour."

---

## 2. What paths are returned when going through symlinked directories?

**Answer: The path through the symlink (NOT the resolved real path)**

When `rglob()` finds a file through a symlinked directory, it returns:
- **The path AS TRAVERSED** (e.g., `/project/linked_dir/file.py` where `linked_dir` is a symlink)
- **NOT the resolved path** (e.g., `/external/real_dir/file.py`)

The returned `Path` object preserves the symlink in its path components. To get the real path, you must explicitly call `.resolve()`:

```python
# If linked_dir -> /real/dir
for path in Path('/project').rglob('*.py'):
    # path might be: /project/linked_dir/file.py (contains symlink)
    resolved = path.resolve()  # /real/dir/file.py (real path)
```

**Evidence from documentation:**
The example in the docs shows `Path('/etc/init.d/reboot').resolve()` returns a different path, demonstrating that paths can contain unresolved symlinks until `.resolve()` is explicitly called.

---

## 3. Can you control symlink following in Python 3.8-3.12?

**Answer: NO - No direct control exists**

**Python 3.8-3.12:**
- `rglob(pattern)` and `glob(pattern)` have NO `recurse_symlinks` parameter
- Signature: `Path.rglob(pattern, *, case_sensitive=None)`
- Symlinks are ALWAYS followed during directory traversal
- No workaround exists within pathlib itself

**Python 3.13+:**
- Added `recurse_symlinks` parameter to both `glob()` and `rglob()`
- Signature: `Path.rglob(pattern, *, case_sensitive=None, recurse_symlinks=False)`
- Documentation states: "Changed in version 3.13: The recurse_symlinks parameter was added"

**Workarounds for Python 3.8-3.12:**
If you need to avoid following symlinks, you must:
1. Use `Path.walk(follow_symlinks=False)` (added in Python 3.12)
2. Manually filter results using `.is_symlink()` on parent directories
3. Use the lower-level `os.walk(followlinks=False)`

---

## 4. If a path contains a symlink component, will is_symlink() detect it?

**Answer: NO - is_symlink() only checks the FINAL component**

**Critical Understanding:**
- `Path("/project/linked_dir").is_symlink()` → **True** (the path itself is a symlink)
- `Path("/project/linked_dir/file.py").is_symlink()` → **False** (file.py is a regular file)
- `Path("/project/linked_dir/file.py").parent.is_symlink()` → **True** (parent is symlink)

**From the documentation:**
> "`Path.is_symlink()`: Return `True` if the path points to a symbolic link, `False` otherwise."

The method only checks if the **final path component** (the path itself) is a symlink. It does NOT check intermediate components in the path.

**To detect symlinks in the path:**
```python
def has_symlink_in_path(path: Path) -> bool:
    """Check if any component in the path is a symlink."""
    for parent in path.parents:
        if parent.is_symlink():
            return True
    return path.is_symlink()

# Example:
path = Path("/project/linked_dir/file.py")
print(path.is_symlink())  # False (file.py itself is not a symlink)
print(has_symlink_in_path(path))  # True (linked_dir is a symlink)
```

---

## Code Examples

### Example 1: Basic rglob behavior (Python 3.8-3.12)

```python
from pathlib import Path

# Directory structure:
# project/
#   actual.py
#   linked_dir -> /real/dir  (symlink to external directory)
# /real/dir/
#   file1.py
#   file2.py

project = Path('/project')

# rglob() WILL follow the symlink and find files
all_files = list(project.rglob('*.py'))
# Returns: [
#   PosixPath('/project/actual.py'),
#   PosixPath('/project/linked_dir/file1.py'),  # Path through symlink!
#   PosixPath('/project/linked_dir/file2.py'),  # Path through symlink!
# ]

# The paths contain the symlink, not the resolved path
for f in all_files:
    print(f"Path: {f}")
    print(f"  Resolved: {f.resolve()}")  # Show real path
    print(f"  Parent is symlink: {f.parent.is_symlink()}")
```

### Example 2: Detecting symlinks in path components

```python
from pathlib import Path

def analyze_path_symlinks(path: Path):
    """Analyze which components of a path are symlinks."""
    print(f"Analyzing: {path}")
    print(f"  Path itself is symlink: {path.is_symlink()}")

    # Check each component
    for ancestor in [path] + list(path.parents):
        if ancestor.is_symlink():
            print(f"  SYMLINK FOUND: {ancestor}")
            print(f"    Points to: {ancestor.resolve()}")

# Usage:
path = Path('/project/linked_dir/subdir/file.py')
analyze_path_symlinks(path)
```

### Example 3: Python 3.13+ with recurse_symlinks

```python
from pathlib import Path

project = Path('/project')

# Default behavior (3.13+): follows symlinks except for ** wildcards
files_default = list(project.rglob('*.py'))

# Explicitly disable symlink following (3.13+)
files_no_symlinks = list(project.rglob('*.py', recurse_symlinks=False))

# Explicitly enable symlink following (3.13+)
files_with_symlinks = list(project.rglob('*.py', recurse_symlinks=True))
```

### Example 4: Python 3.12 alternative using walk()

```python
from pathlib import Path

def rglob_no_symlinks(root: Path, pattern: str):
    """
    Alternative to rglob() that doesn't follow symlinks (Python 3.12+).
    Uses Path.walk() which has follow_symlinks parameter.
    """
    for dirpath, dirnames, filenames in root.walk(follow_symlinks=False):
        for filename in filenames:
            file_path = dirpath / filename
            # Check if matches pattern (simple approach)
            if file_path.match(pattern):
                yield file_path

# Usage:
project = Path('/project')
files = list(rglob_no_symlinks(project, '*.py'))
```

---

## Version Compatibility Table

| Python Version | rglob() follows symlinks? | recurse_symlinks parameter? | Workaround |
|----------------|---------------------------|----------------------------|-----------|
| 3.8-3.11 | YES (always) | ❌ No | Use `os.walk(followlinks=False)` |
| 3.12 | YES (always) | ❌ No | Use `Path.walk(follow_symlinks=False)` |
| 3.13+ | YES (except ** wildcards) | ✅ Yes | Use `recurse_symlinks=False` |

---

## References

1. **Python 3.13 Documentation**: https://docs.python.org/3.13/library/pathlib.html#pathlib.Path.rglob
   - Added `recurse_symlinks` parameter

2. **Python 3.12 Documentation**: https://docs.python.org/3.12/library/pathlib.html#pathlib.Path.rglob
   - No `recurse_symlinks` parameter
   - Added `Path.walk(follow_symlinks=...)` as alternative

3. **Comparison to glob module**: Python docs explicitly state:
   > ""`**`" pattern components do not follow symlinks by default in pathlib."

4. **Path.is_symlink() documentation**:
   > "Return `True` if the path points to a symbolic link, `False` otherwise."
   - Only checks the final component, not intermediate directories

---

## Key Takeaways

1. ✅ **rglob() DOES follow symlinks by default** in Python 3.8-3.12 (no way to disable)
2. ✅ **Returns paths through the symlink**, not resolved real paths
3. ❌ **NO control in Python 3.8-3.12**, workarounds needed
4. ✅ **is_symlink() only checks the final path component**, not parents
5. ✅ **Python 3.13+ adds `recurse_symlinks` parameter** for control
6. ✅ **Use `.resolve()` to get real paths** from symlink-containing paths
7. ✅ **Check parent directories separately** to detect symlinks in path components

---

## Practical Implications

**For Python 3.8-3.12 users:**
- Be aware that `rglob()` will traverse into symlinked directories
- This can cause:
  - **Duplicates**: Same files found through multiple symlink paths
  - **Infinite loops**: If symlinks create cycles (though pathlib handles this)
  - **Performance issues**: Traversing external large directory trees

**Recommended approach for Python 3.8-3.11:**
```python
from pathlib import Path

def safe_rglob(root: Path, pattern: str):
    """rglob that tracks visited real paths to avoid duplicates."""
    seen_inodes = set()

    for path in root.rglob(pattern):
        try:
            stat = path.stat()
            inode = (stat.st_dev, stat.st_ino)

            if inode not in seen_inodes:
                seen_inodes.add(inode)
                yield path
        except OSError:
            # Handle broken symlinks gracefully
            pass
```
