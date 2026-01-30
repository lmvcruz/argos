"""
Python file with PEP 8 style violations.

This fixture violates multiple PEP 8 style guidelines.
"""

import json
import os  # Multiple imports on one line
import sys

# Too many blank lines


def BadFunctionName(X,y): # Function name should be lowercase, spaces after commas
    """Function with style issues."""
    z=X+y # No spaces around operator
    return z


class badClassName: # Class name should be PascalCase
    """Class with style issues."""

    def __init__(self,name,age): # Spaces after commas
        self.name=name # Spaces around =
        self.age=age

    def VeryLongMethodNameThatExceedsTheRecommendedLineLength(self, parameter1, parameter2, parameter3, parameter4, parameter5, parameter6, parameter7):
        """Method name and signature too long."""
        return parameter1+parameter2+parameter3+parameter4+parameter5+parameter6+parameter7 # Line too long


# Whitespace issues
def function_with_whitespace_issues( arg1 , arg2 , arg3 ):
    """Extra spaces in parameter list."""
    result = ( arg1+arg2 )*arg3 # Weird spacing
    return result


# Multiple statements on one line
x = 1; y = 2; z = 3


# Trailing whitespace and blank lines with whitespace
def trailing_issues():
    return "Has trailing whitespace"


# Wrong number of blank lines before class
class AnotherClass:
    pass
