# Copilot Instructions for Argos/Forge Project

## Project Setup (MANDATORY)

**These steps MUST be completed before starting development:**

1. **Install Git Pre-Commit Hook** (Enforces quality checks)
   ```bash
   cd forge
   python scripts/setup-git-hooks.py
   ```
   This installs a git hook that automatically runs before each commit:
   - Syntax checks (flake8)
   - Code formatting (black)
   - Import sorting (isort)
   - Tests and coverage
   
   **Verification**: Check that `.git/hooks/pre-commit` exists
   
2. **Verify Development Environment**
   ```bash
   cd forge
   python -m pytest  # Should run all tests
   python scripts/pre-commit-check.py  # Should pass all checks
   ```

3. **For Copilot/AI Assistants**: 
   - **ALWAYS verify the pre-commit hook is installed at session start**
   - **NEVER commit without running pre-commit checks**
   - **Follow the Code Review Checklist strictly** (see bottom of this file)

---

## Code Comment Standards

### Docstrings

- **Style**: Use Google-style docstrings for all public functions, classes, and methods
- **Required Sections**:
  - Brief description (first line, imperative mood)
  - `Args:` - Parameter descriptions with types if not obvious from type hints
  - `Returns:` - Return value description
  - `Raises:` - Exceptions that may be raised (if applicable)
  - `Examples:` - Usage examples for public API methods (optional, only used for complicated functions)
- **Type Hints**: Use function signature type hints, not docstring types
- **Format**:

  ```python
  def function_name(param: str) -> bool:
      """
      Brief description of what the function does.

      Longer description if needed to explain behavior,
      edge cases, or important implementation details.

      Args:
          param: Description of the parameter

      Returns:
          Description of the return value

      Raises:
          ValueError: When param is invalid

      Examples:
          >>> function_name("test")
          True
      """
  ```

### Inline Comments

- **Use Sparingly**: Prefer self-documenting code with clear variable/function names
- **Explain "Why", Not "What"**: Comments should clarify intent or rationale, not repeat what the code obviously does
- **Section Headers**: Use comments to mark logical sections in longer functions
  ```python
  # Extract suggestion from error message
  # Build the error message
  # Auto-detect color support if not specified
  ```
- **TODOs**: Use format `# TODO(#issue): Description` or `# TODO: Description` for temporary notes
- **Avoid**: Over-commenting obvious operations like `# Increment counter` or `# Return result`

### Module Docstrings

- **Required**: Every Python file must have a module-level docstring
- **Content**: Brief description of module purpose and key components
- **Format**:

  ```python
  """
  Brief description of the module.

  More detailed description if needed, including key classes
  or functions provided by this module.
  """
  ```

## Code Style Standards

### General Python

- **Line Length**: 100 characters maximum (already configured in .editorconfig)
- **Imports**:
  - Group by: standard library, third-party, local modules (separated by blank lines)
  - Within each group: `import` statements first, then `from ... import` statements
  - Alphabetically sort within each sub-group
  - Use `isort` for automatic sorting
  - Avoid wildcard imports (`from module import *`)
  - **Example**:

    ```python
    # Standard library
    import os
    import sys
    from pathlib import Path
    from typing import Optional

    # Third-party
    import pytest
    from pytest_mock import MockerFixture

    # Local modules
    from forge.cli.argument_parser import ArgumentParser
    from forge.models.metadata import ConfigureMetadata
    ```

- **Naming**:
  - Classes: `PascalCase`
  - Functions/variables: `snake_case`
  - Constants: `UPPER_SNAKE_CASE`
  - Private methods: `_leading_underscore`

### Type Hints

- **Always Use**: Type hints for function parameters and return values
- **Complex Types**: Import from `typing` module (List, Dict, Optional, Union, etc.)
- **Optional Parameters**: **Must** use `Optional[Type]` from typing module for nullable parameters
  - **Do NOT use** `Type | None` syntax (Python 3.10+ only)
  - Reason: Project targets Python 3.8+ for compatibility
  - Example: `def func(param: Optional[str] = None) -> Optional[int]:`

### Error Handling

- **Custom Exceptions**: Create domain-specific exceptions (like `ArgumentError`, `ValidationError`)
- **Context**: Include helpful context in exception messages
- **Graceful Degradation**: Handle edge cases gracefully (return None, empty list, etc.)

## Testing Standards

### Test Structure

- **Follow TDD**: Write tests before implementation
- **Red-Green-Refactor**: Run the test before the real implementation (it must fail first)
  - **RED**: Write test → Run test → **IT MUST FAIL** (if it passes, you're testing existing code)
  - **GREEN**: Write minimal implementation → Run test → **IT MUST PASS**
  - **REFACTOR**: Clean up code → Run test → **IT MUST STILL PASS**
  - **QUALITY**: Run pre-commit checks → **THEY MUST PASS** before committing
- **Naming**: `test_descriptive_name_of_what_is_tested`
- **Organization**: Group related tests in classes with `Test` prefix
- **Fixtures**: Use pytest fixtures for reusable test data
- **Mocks vs Real Tests**: Use mocks for unit tests, but also include integration tests with real cases
- **Coverage**: Aim for 90%+ coverage; 100% for critical business logic

### Test Documentation

- **Docstrings**: Every test function should have a brief docstring explaining what it tests
- **Descriptive Names**: Test names should be self-explanatory
  ```python
  def test_extract_cmake_version_from_linux_output(self, linux_output):
      """Test extraction of CMake version from Linux output."""
  ```

## Project-Specific Guidelines

### CMake/Build Domain

- **Terminology**: Use consistent terms (configure vs setup, build vs compile, target vs executable)
- **Path Handling**: Always use `pathlib.Path` for file paths, not string concatenation
- **Cross-Platform**: Consider Windows, Linux, and macOS differences

### CLI/User-Facing Code

- **Error Messages**: Clear, actionable error messages with suggestions
- **Color Output**: Support both colored and plain text output
- **Help Text**: Comprehensive help text for all commands and arguments

### Data Models

- **Dataclasses**: Use `@dataclass` for data containers
- **Serialization**: Provide `to_dict()` and `from_dict()` methods for JSON serialization
- **Validation**: Validate data in `__post_init__` or separate validator methods

## Linting and Quality

### Pre-commit Checks

- All code must pass:
  - `black` - Code formatting
  - `isort` - Import sorting
  - `flake8` - Linting
  - `pylint` - Static analysis (with exceptions noted in code)
  - `pytest` - All tests passing
  - Coverage threshold (90%)

### Pylint Exceptions

- Use inline disables sparingly: `# pylint: disable=rule-name`
- Always add comment explaining why disable is needed
- Prefer fixing the issue over disabling the rule

## Best Practices

1. **Fail Fast**: Validate inputs early, raise exceptions for invalid states
2. **Immutability**: Prefer immutable data structures where appropriate
3. **Single Responsibility**: Functions/classes should do one thing well
4. **DRY**: Don't repeat yourself - extract common logic to helper functions
5. **Explicit > Implicit**: Be explicit about behavior, avoid magic values
6. **Document Assumptions**: If code assumes something, document it
7. **Test Edge Cases**: Test empty inputs, None values, boundary conditions

## Code Review Checklist

**CRITICAL: This checklist is MANDATORY before every commit.**

Before committing, ensure:

- [ ] **Pre-commit hook installed** (verify `.git/hooks/pre-commit` exists)
- [ ] **All functions have docstrings** (Google-style format)
- [ ] **Type hints are present** (parameters and return values)
- [ ] **Tests are written and passing** (follow TDD: RED → GREEN → Refactor)
- [ ] **Coverage is adequate** (90%+ per module, 90%+ overall)
- [ ] **No commented-out code** (delete it, don't leave it)
- [ ] **No debug print statements** (use logging module)
- [ ] **Error messages are helpful** (clear, actionable)
- [ ] **Pre-commit checks pass** (run `python scripts/pre-commit-check.py`)
  - Syntax errors (flake8): 0
  - Formatting (black): all files formatted
  - Import order (isort): properly sorted
  - Unused variables (autoflake): none
  - All tests passing
  - Coverage threshold met

**If ANY item fails, DO NOT commit. Fix the issues first.**
