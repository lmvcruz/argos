#!/usr/bin/env python
"""Test Issue class with diff field."""

from anvil.models.validator import Issue

# Create an issue with diff
issue = Issue(
    file_path='test.py',
    line_number=1,
    message='Test',
    severity='error',
    diff='--- a/test.py\n+++ b/test.py\n-x=1\n+x = 1'
)

print(f'Created issue')
print(f'Issue.__dict__: {issue.__dict__}')
print(f'Issue fields: {Issue.__dataclass_fields__.keys()}')
print(f'Has diff attribute: {hasattr(issue, "diff")}')
print(f'Diff value: {getattr(issue, "diff", "NOT FOUND")}')
