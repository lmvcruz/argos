# Documentation Guide

This directory contains comprehensive documentation for the Forge project.

## Quick Start

**Running Forge from source:**

```bash
# Clone and navigate to repository
git clone https://github.com/lmvcruz/argos.git
cd argos

# Run Forge
python -m forge --help

# Use Forge with your project
cd /path/to/your/cmake/project
python -m forge --build-dir build --configure
python -m forge --build-dir build
```

**Installing Forge:**

```bash
cd argos/forge
pip install -e .

# Now you can use 'forge' from anywhere
forge --version
```

## Available Documentation

### User Documentation

- **[USER_GUIDE.md](USER_GUIDE.md)** - Complete user guide ⭐ **Start here!**
  - Introduction to Forge
  - Installation instructions
  - Quick start guide
  - Basic and advanced usage
  - Configuration options
  - Working with build data
  - CI/CD integration workflows
  - Best practices
  - FAQ

- **[TUTORIAL.md](TUTORIAL.md)** - Step-by-step hands-on tutorials
  - Your first build
  - Working with build types
  - Analyzing build data
  - Tracking performance
  - CI/CD integration examples
  - Real-world sample projects

- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Problem-solving guide
  - Installation issues
  - CMake detection problems
  - Build failures
  - Database issues
  - Performance problems
  - Platform-specific issues
  - Error messages reference

### Developer Documentation

- **[API.md](API.md)** - Complete API reference with examples
  - Installation instructions
  - Quick start guide
  - Core components documentation
  - Data models reference
  - Utilities documentation
  - Command-line interface guide
  - Best practices
  - Complete examples

### Technical Documentation

- **[linting-rules.md](linting-rules.md)** - Code quality standards and linting configuration
- **[cross-platform-testing-report.md](cross-platform-testing-report.md)** - Cross-platform testing results

## Documentation Navigator

**New to Forge?**
1. Start with [USER_GUIDE.md](USER_GUIDE.md) for an overview
2. Follow [TUTORIAL.md](TUTORIAL.md) for hands-on practice
3. Keep [TROUBLESHOOTING.md](TROUBLESHOOTING.md) handy for issues

**Developer/Contributor?**
1. Read [API.md](API.md) for technical reference
2. Review [linting-rules.md](linting-rules.md) for code standards
3. Check this guide for documentation requirements

**Having Issues?**
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) first
2. Review [USER_GUIDE.md](USER_GUIDE.md) FAQ section
3. Open a GitHub issue with diagnostic information

## Documentation Standards

All Forge code follows strict documentation standards:

### Docstring Format

We use **Google-style docstrings** for all public APIs:

```python
def function_name(param1: str, param2: int) -> bool:
    """
    Brief description of what the function does.

    Longer description if needed to explain behavior,
    edge cases, or important implementation details.

    Args:
        param1: Description of the parameter
        param2: Description of the parameter

    Returns:
        Description of the return value

    Raises:
        ValueError: When param is invalid

    Examples:
        >>> function_name("test", 42)
        True
    """
```

### Documentation Requirements

1. **Every module** must have a module-level docstring
2. **Every public class** must have a docstring
3. **Every public method/function** must have a docstring
4. Docstrings must include:
   - Brief description (first line)
   - `Args:` section for parameters
   - `Returns:` section for return values
   - `Raises:` section for exceptions (if applicable)
   - `Examples:` section for complex functions (optional)

### Type Hints

All public functions must include type hints:

```python
from typing import Optional, List

def process_data(
    items: List[str],
    config: Optional[Dict[str, Any]] = None
) -> bool:
    """Process the items with optional configuration."""
    pass
```

## Testing Documentation

Documentation completeness is validated by automated tests in `tests/test_documentation.py`:

```bash
# Run documentation tests
pytest tests/test_documentation.py -v
```

The tests verify:

- All modules have docstrings
- All public classes have docstrings
- All public methods have docstrings
- All public functions have docstrings
- Docstrings follow Google-style format
- Parameters are documented
- Return types are documented
- Examples work correctly (where present)
- `__all__` exports match public API

## Generating Documentation

### Viewing API Documentation

The API.md file is designed to be read directly on GitHub or locally in any Markdown viewer.

### Future: HTML Documentation

In a future release, we plan to support automated HTML documentation generation using:

- **Sphinx** with Google-style docstring extension
- **pdoc** for simple HTML generation
- **MkDocs** for documentation site

## Documentation Checklist

When adding new code, ensure:

- [ ] Module docstring is present
- [ ] Class docstring is present (if adding a class)
- [ ] All public methods have docstrings
- [ ] All parameters are documented
- [ ] Return type is documented
- [ ] Exceptions are documented (if any)
- [ ] Type hints are present
- [ ] Examples are included for complex functions
- [ ] Documentation tests pass: `pytest tests/test_documentation.py`

## Examples

### Good Module Documentation

```python
"""
Build inspection module for analyzing CMake output.

This module provides the BuildInspector class which analyzes
CMake configure and build output to extract metadata, warnings,
and errors from various compilers and build systems.
"""

from pathlib import Path
from typing import List, Optional

class BuildInspector:
    """
    Analyzes CMake and compiler output to extract build metadata.

    The BuildInspector parses output from CMake configuration and
    build steps to identify:
    - Project metadata (name, version, compiler info)
    - Built targets (executables, libraries)
    - Compiler warnings and errors
    - Build statistics

    Attributes:
        source_dir: Path to project source directory
    """

    def __init__(self, source_dir: Optional[Path] = None):
        """
        Initialize BuildInspector.

        Args:
            source_dir: Path to source directory for project detection
        """
        self.source_dir = source_dir

    def inspect_configure_output(
        self,
        output: str,
        success: bool
    ) -> ConfigureMetadata:
        """
        Extract metadata from CMake configure output.

        Analyzes CMake configuration output to identify project
        metadata including CMake version, generator, compiler
        information, and found packages.

        Args:
            output: Complete configure output text
            success: Whether configuration succeeded

        Returns:
            ConfigureMetadata object with extracted information

        Examples:
            >>> inspector = BuildInspector()
            >>> metadata = inspector.inspect_configure_output(
            ...     output="-- The C compiler identification is GNU 11.2.0",
            ...     success=True
            ... )
            >>> metadata.c_compiler
            '/usr/bin/gcc'
        """
        pass
```

## Contributing to Documentation

When contributing to Forge:

1. Follow the docstring format specified above
2. Add examples for complex or non-obvious functions
3. Run documentation tests before submitting PR
4. Update API.md if adding new public APIs
5. Ensure all parameters and return values are documented

## Questions?

For questions about documentation standards or how to document specific code:

1. Check this guide first
2. Look at existing well-documented modules (e.g., `utils/formatting.py`)
3. Review the test suite in `tests/test_documentation.py`
4. Ask in PR comments

## Documentation Quality Metrics

Target metrics:

- **100%** of public APIs have docstrings
- **100%** of docstrings follow Google-style format
- **100%** of parameters are documented
- **100%** of return types are documented
- **Documentation tests pass**: All tests in `test_documentation.py` pass

Current status: ✅ **All metrics achieved**
