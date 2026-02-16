"""
Calculator Tool — Basic arithmetic operations.

Standardized tool format with DESCRIPTION, PARAMETERS, and run().
"""

DESCRIPTION = "Perform basic arithmetic: add, subtract, multiply, divide."

PARAMETERS = {
    "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
    "a": {"type": "number"},
    "b": {"type": "number"},
}


def run(operation: str, a: float, b: float) -> dict:
    """Execute a calculation."""
    ops = {
        "add": lambda: a + b,
        "subtract": lambda: a - b,
        "multiply": lambda: a * b,
        "divide": lambda: a / b if b != 0 else "Error: Division by zero",
    }

    if operation not in ops:
        return {"error": f"Unknown operation: {operation}"}

    result = ops[operation]()
    return {"result": result, "expression": f"{a} {operation} {b}"}
