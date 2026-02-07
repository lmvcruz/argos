#!/usr/bin/env python
"""Test diff extraction regex patterns."""

import re

# Sample diff output from Black on Windows
diff_output = """--- anvil\\validators\\black_validator.py 2026-02-07 18:48:14.605211+00:00
+++ anvil\\validators\\black_validator.py 2026-02-07 18:51:58.811527+00:00
@@ -12,11 +12,11 @@

 from anvil.models.validator import ValidationResult, Validator
 from anvil.parsers.black_parser import BlackParser

 # Set up logger for anvil.black
-logger = logging.getLogger('anvil.black')
+logger = logging.getLogger("anvil.black")


 class BlackValidator(Validator):
     \"\"\"
     Validator for black Python code formatter.
"""

file_path = 'anvil\\validators\\black_validator.py'
filename = 'black_validator.py'

print(f"File path to match: {file_path}")
print(f"Filename: {filename}")
print()

# Test patterns
patterns_to_test = [
    (f"--- {re.escape(file_path)}.*?(?=--- |\\Z)",
     "Escaped full path with lookahead"),
    (f"--- {re.escape(file_path)}.*?$", "Escaped full path with MULTILINE $"),
    (f"--- .+?{re.escape(filename)}.*?(?=--- |\\Z)",
     "Filename fallback with lookahead"),
    (f"--- .+?\\\\{re.escape(filename)}.*?$",
     "Filename with explicit backslash"),
]

for pattern_str, desc in patterns_to_test:
    print(f"Testing: {desc}")
    print(f"  Pattern: {pattern_str[:60]}...")

    regex = re.compile(pattern_str, re.MULTILINE | re.DOTALL)
    match = regex.search(diff_output)

    if match:
        matched_text = match.group(0)
        print(f"  ✓ MATCHED (length={len(matched_text)})")
        print(f"  First line: {matched_text.split(chr(10))[0]}")
    else:
        print(f"  ✗ NO MATCH")
    print()
