#!/usr/bin/env python
"""Debug black parser diff extraction step by step."""

from anvil.parsers.black_parser import BlackParser
from pathlib import Path
import re

# Test files
files = [Path(r'D:\playground\argos\scout\scout\cli.py')]

# Step 1: Run black and get output
print("Step 1: Running black...")
combined, diff_stdout = BlackParser.run_black(files, {})

print(f"Combined output length: {len(combined)}")
print(f"Diff stdout length: {len(diff_stdout)}")
print()

print("Step 2: Looking for 'would reformat' messages...")
reformat_pattern = re.compile(r"would reformat (.+?)$", re.MULTILINE)
matches = list(reformat_pattern.finditer(combined))
print(f"Found {len(matches)} 'would reformat' messages")
for match in matches:
    file_path = match.group(1).strip()
    print(f"  File: {repr(file_path)}")

    # Now try to match the diff for this file
    print(f"\n  Trying diff patterns for: {repr(file_path)}")
    escaped_path = re.escape(file_path)
    pattern_str = rf"--- a/{escaped_path}.*?(?=--- |\Z)"
    print(f"  Pattern: {repr(pattern_str[:100])}")
    diff_pattern = re.compile(pattern_str, re.MULTILINE | re.DOTALL)
    diff_match = diff_pattern.search(diff_stdout)
    print(f"  Match result: {diff_match is not None}")

    if not diff_match:
        # Try without the 'a/' prefix
        pattern_str2 = rf"--- {escaped_path}.*?(?=--- |\Z)"
        print(f"  Trying alt pattern: {repr(pattern_str2[:100])}")
        diff_pattern2 = re.compile(pattern_str2, re.MULTILINE | re.DOTALL)
        diff_match2 = diff_pattern2.search(diff_stdout)
        print(f"  Alt match result: {diff_match2 is not None}")

        # Check what's actually in the diff header
        print(f"\n  Looking for diff headers in output:")
        for line in diff_stdout.split('\n')[:5]:
            if '---' in line:
                print(f"    Found: {repr(line[:120])}")

print()
print("Step 3: Parsing with BlackParser...")
result = BlackParser.parse_text(combined, files, diff_output=diff_stdout)

print(f"Errors: {len(result.errors)}")
if result.errors:
    err = result.errors[0]
    print(f"  File: {err.file_path}")
    print(f"  Message: {err.message}")
    print(f"  Diff value: {repr(err.diff) if err.diff else 'None'}")
