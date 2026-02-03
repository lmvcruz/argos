# Simple Example - Math Operation Validation

This example demonstrates using Verdict to validate a simple math operation parser.

## Directory Structure

```
examples/simple/
  config.yaml           # Verdict configuration
  adapter.py            # Target callable implementation
  test_cases/
    case_01.yaml        # Test case: addition
    case_02.yaml        # Test case: multiplication
```

## Files

### adapter.py

The target callable that parses math expressions:

```python
def parse_math_expression(input_text: str) -> dict:
    """Parse a simple math expression like '2 + 3 = 5'."""
    parts = input_text.strip().split()
    if len(parts) != 5:
        return {"valid": False, "error": "Invalid format"}

    num1 = int(parts[0])
    operator = parts[1]
    num2 = int(parts[2])
    result = int(parts[4])

    return {
        "valid": True,
        "operand1": num1,
        "operator": operator,
        "operand2": num2,
        "result": result,
    }
```

### test_cases/case_01.yaml

```yaml
input: |
  2 + 3 = 5

expected:
  valid: true
  operand1: 2
  operator: "+"
  operand2: 3
  result: 5
```

### test_cases/case_02.yaml

```yaml
input: |
  4 * 5 = 20

expected:
  valid: true
  operand1: 4
  operator: "*"
  operand2: 5
  result: 20
```

### config.yaml

```yaml
settings:
  max_workers: 1

test_suites:
  - name: "math_parser_tests"
    target: "math"
    type: "single_file"
    file: "test_cases/case_01.yaml"

targets:
  math:
    callable: "adapter.parse_math_expression"
```

## Running the Example

From the `examples/simple/` directory:

```bash
verdict run --config config.yaml
```

Expected output:

```
======================================================================
TEST RESULTS: 1 passed, 0 failed, 1 total
======================================================================

math_parser_tests
----------------------------------------------------------------------
  ✓ case_01

======================================================================
✓ ALL TESTS PASSED
======================================================================
```
