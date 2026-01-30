"""
Python file with syntax errors.

This fixture is intentionally broken to test syntax error detection.
"""


# Missing colon after function definition
def broken_function()
    return "This won't parse"


# Unmatched parenthesis
def another_broken(arg1, arg2:
    return arg1 + arg2


# Invalid indentation
class BadClass:
def broken_method(self):
        return "Bad indentation"


# Missing closing quote
message = "This string is not closed


# Invalid syntax with if
if True
    print("Missing colon")
