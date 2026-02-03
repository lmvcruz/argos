"""
Simple math expression parser for testing Verdict.

This module demonstrates the (str) -> dict interface contract.
"""


def parse_math_expression(input_text: str) -> dict:
    """
    Parse a simple math expression like '2 + 3 = 5'.

    Args:
        input_text: Math expression string

    Returns:
        Dictionary with parsed components
    """
    try:
        parts = input_text.strip().split()
        if len(parts) != 5:
            return {"valid": False, "error": "Invalid format"}

        # Parse components
        num1 = int(parts[0])
        operator = parts[1]
        num2 = int(parts[2])
        equals_sign = parts[3]
        result = int(parts[4])

        if equals_sign != "=":
            return {"valid": False, "error": "Missing equals sign"}

        return {
            "valid": True,
            "operand1": num1,
            "operator": operator,
            "operand2": num2,
            "result": result,
        }

    except (ValueError, IndexError) as e:
        return {"valid": False, "error": str(e)}
