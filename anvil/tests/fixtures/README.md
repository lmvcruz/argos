# Test Fixtures

This directory contains test fixtures for validator parsers.

## Directory Structure

```
fixtures/
├── python/          # Python code samples
│   ├── good_code.py            # Valid, well-formatted Python
│   ├── unicode_content.py      # Python with Unicode characters
│   └── bad_code/               # Python with various issues
│       ├── syntax_error.py     # Python syntax errors
│       ├── missing_imports.py  # Undefined names (import issues)
│       ├── unused_code.py      # Unused imports and variables
│       ├── style_violations.py # PEP 8 style violations
│       └── unformatted.py      # Needs black formatting
├── cpp/             # C++ code samples
│   ├── good_code.cpp           # Valid, well-formatted C++
│   ├── good_code.hpp           # Valid C++ header
│   └── bad_code/               # C++ with various issues
│       ├── syntax_error.cpp    # C++ syntax errors
│       ├── style_violations.cpp # Style guideline violations
│       └── static_analysis_issues.cpp # Bugs detectable by static analysis
└── sample_code/     # Larger code samples for integration tests
    └── (project-like structures)
```

## Naming Conventions

### Good Code Files
- `good_code.{ext}` - Clean, valid code that should pass all validators
- Example: `good_code.py`, `good_code.cpp`, `good_code.hpp`

### Bad Code Files
- Organized under `bad_code/` subdirectories
- Named by the type of issue they demonstrate:
  - `syntax_error.{ext}` - Syntax errors that prevent compilation/parsing
  - `missing_imports.{ext}` - Import or include errors
  - `unused_code.{ext}` - Unused imports, variables, functions
  - `style_violations.{ext}` - Style guideline violations (PEP 8, Google C++ Style)
  - `unformatted.{ext}` - Code that needs formatting (black, clang-format)
  - `static_analysis_issues.{ext}` - Logical errors detectable by static analysis

### Special Files
- `unicode_content.py` - Test UTF-8 encoding handling

## Usage in Tests

```python
from tests.helpers.parser_test_helpers import ParserTestHelpers

helpers = ParserTestHelpers()

# Load a fixture
content = helpers.load_fixture("python/good_code.py")

# Get fixture path
path = helpers.get_fixture_path("cpp/bad_code/syntax_error.cpp")

# List all fixtures in a directory
fixtures = helpers.list_fixtures("python/bad_code")
```

## Adding New Fixtures

1. Decide the fixture category (python/cpp)
2. Determine if it's good code or bad code with a specific issue
3. Place in appropriate directory following naming conventions
4. Add test cases that use the fixture
5. Document any special characteristics in comments within the fixture

## Best Practices

- **Keep fixtures focused**: Each fixture should demonstrate one specific issue
- **Use realistic code**: Fixtures should resemble real-world code
- **Add comments**: Explain what makes the code good or bad
- **Test multiple scenarios**: Have variations of common issues
- **UTF-8 encoding**: All fixtures must be UTF-8 encoded
