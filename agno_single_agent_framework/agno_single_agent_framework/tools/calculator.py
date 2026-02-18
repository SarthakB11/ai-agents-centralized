"""
Calculator Toolkit — Basic arithmetic operations using Agno framework.

Provides add, subtract, multiply, and divide operations as Agno tools.
"""

from agno.tools import Toolkit


class CalculatorToolkit(Toolkit):
    """Toolkit for performing basic arithmetic operations."""

    def __init__(self):
        super().__init__(name="calculator")
        self.register(self.add)
        self.register(self.subtract)
        self.register(self.multiply)
        self.register(self.divide)

    def add(self, a: float, b: float) -> dict:
        """
        Add two numbers together.

        Args:
            a: The first number to add
            b: The second number to add

        Returns:
            A dictionary with the result and expression
        """
        result = a + b
        return {"result": result, "expression": f"{a} + {b} = {result}"}

    def subtract(self, a: float, b: float) -> dict:
        """
        Subtract the second number from the first number.

        Args:
            a: The number to subtract from
            b: The number to subtract

        Returns:
            A dictionary with the result and expression
        """
        result = a - b
        return {"result": result, "expression": f"{a} - {b} = {result}"}

    def multiply(self, a: float, b: float) -> dict:
        """
        Multiply two numbers together.

        Args:
            a: The first number to multiply
            b: The second number to multiply

        Returns:
            A dictionary with the result and expression
        """
        result = a * b
        return {"result": result, "expression": f"{a} × {b} = {result}"}

    def divide(self, a: float, b: float) -> dict:
        """
        Divide the first number by the second number.

        Args:
            a: The dividend (number to be divided)
            b: The divisor (number to divide by)

        Returns:
            A dictionary with the result and expression, or error if dividing by zero
        """
        if b == 0:
            return {"error": "Division by zero", "expression": f"{a} ÷ {b}"}

        result = a / b
        return {"result": result, "expression": f"{a} ÷ {b} = {result}"}


# Backward compatibility: Keep the old interface
DESCRIPTION = "Perform basic arithmetic: add, subtract, multiply, divide."
PARAMETERS = {
    "operation": {"type": "string", "enum": ["add", "subtract", "multiply", "divide"]},
    "a": {"type": "number"},
    "b": {"type": "number"},
}


def run(operation: str, a: float, b: float) -> dict:
    """Execute a calculation (legacy interface for backward compatibility)."""
    toolkit = CalculatorToolkit()
    ops = {
        "add": toolkit.add,
        "subtract": toolkit.subtract,
        "multiply": toolkit.multiply,
        "divide": toolkit.divide,
    }

    if operation not in ops:
        return {"error": f"Unknown operation: {operation}"}

    return ops[operation](a, b)
