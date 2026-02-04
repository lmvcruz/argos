"""
Tests for Black diff parsing and code extraction.

Tests the logic for extracting actual_code and expected_code
from Black's --diff output.
"""


class TestBlackDiffExtraction:
    """Tests for extracting code snippets from Black diff output."""

    def test_extract_code_from_simple_diff(self):
        """Verify extraction of code from a simple Black diff."""
        from anvil.parsers.black_parser import BlackParser

        diff_output = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
-x=1
+x = 1
 y = 2
"""

        actual_code, expected_code = BlackParser.extract_code_from_diff(diff_output)

        assert actual_code == "x=1"
        assert expected_code == "x = 1"

    def test_extract_code_from_multi_line_diff(self):
        """Verify extraction when multiple lines are changed."""
        from anvil.parsers.black_parser import BlackParser

        diff_output = """--- a/test.py
+++ b/test.py
@@ -1,4 +1,4 @@
-def foo(x,y):
-    return x+y
+def foo(x, y):
+    return x + y
 z = 1
"""

        actual_code, expected_code = BlackParser.extract_code_from_diff(diff_output)

        assert "def foo(x,y):" in actual_code
        assert "return x+y" in actual_code
        assert "def foo(x, y):" in expected_code
        assert "return x + y" in expected_code

    def test_extract_code_handles_empty_diff(self):
        """Verify graceful handling of empty diff."""
        from anvil.parsers.black_parser import BlackParser

        diff_output = ""

        actual_code, expected_code = BlackParser.extract_code_from_diff(diff_output)

        assert actual_code == ""
        assert expected_code == ""

    def test_extract_code_with_no_changes_in_diff(self):
        """Verify handling when diff header exists but no actual changes."""
        from anvil.parsers.black_parser import BlackParser

        diff_output = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
 x = 1
 y = 2
 z = 3
"""

        actual_code, expected_code = BlackParser.extract_code_from_diff(diff_output)

        # No changes means no actual/expected code
        assert actual_code == ""
        assert expected_code == ""

    def test_extract_code_multiple_chunks(self):
        """Verify extraction when diff has multiple change chunks."""
        from anvil.parsers.black_parser import BlackParser

        diff_output = """--- a/test.py
+++ b/test.py
@@ -1,3 +1,3 @@
-x=1
+x = 1
 y = 2
@@ -10,3 +10,3 @@
-z=3
+z = 3
 a = 4
"""

        actual_code, expected_code = BlackParser.extract_code_from_diff(diff_output)

        # Should extract all removed and added lines
        assert "x=1" in actual_code
        assert "z=3" in actual_code
        assert "x = 1" in expected_code
        assert "z = 3" in expected_code

    def test_extract_code_preserves_whitespace(self):
        """Verify that whitespace is preserved in extracted code."""
        from anvil.parsers.black_parser import BlackParser

        diff_output = """--- a/test.py
+++ b/test.py
@@ -1,2 +1,2 @@
-x  =  1
+x = 1
"""

        actual_code, expected_code = BlackParser.extract_code_from_diff(diff_output)

        assert actual_code == "x  =  1"
        assert expected_code == "x = 1"

    def test_parse_text_with_diff_adds_code_fields(self):
        """Verify that parse_text can extract code from diff when available."""
        from pathlib import Path

        from anvil.parsers.black_parser import BlackParser

        text_output = """--- a/main.py
+++ b/main.py
@@ -1,2 +1,2 @@
-x=1
+x = 1
 y = 2
would reformat main.py
"""

        result = BlackParser.parse_text(text_output, [Path("main.py")])

        # Result should include errors (would reformat)
        assert result.passed is False
        assert len(result.errors) == 1

        # extract_code_from_diff should work on the same output
        actual_code, expected_code = BlackParser.extract_code_from_diff(text_output)
        assert "x=1" in actual_code
        assert "x = 1" in expected_code

    def test_extract_code_ignores_context_lines(self):
        """Verify that only removed and added lines are extracted."""
        from anvil.parsers.black_parser import BlackParser

        diff_output = """--- a/test.py
+++ b/test.py
@@ -1,5 +1,5 @@
 # Comment (context)
-x=1
+x = 1
 y = 2
 z = 3
"""

        actual_code, expected_code = BlackParser.extract_code_from_diff(diff_output)

        # Only changed lines, not context
        assert "x=1" in actual_code
        assert "x = 1" in expected_code
        assert "# Comment" not in actual_code
        assert "y = 2" not in actual_code
