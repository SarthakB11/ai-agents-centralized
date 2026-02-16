"""
Unit tests for tools and agent.
"""

import pytest
from app.tools import example_tool


class TestCalculatorTool:
    def test_add(self):
        result = example_tool.run("add", 5, 3)
        assert result["result"] == 8

    def test_subtract(self):
        result = example_tool.run("subtract", 10, 4)
        assert result["result"] == 6

    def test_multiply(self):
        result = example_tool.run("multiply", 7, 8)
        assert result["result"] == 56

    def test_divide(self):
        result = example_tool.run("divide", 100, 4)
        assert result["result"] == 25

    def test_divide_by_zero(self):
        result = example_tool.run("divide", 10, 0)
        assert "Error" in str(result["result"])

    def test_unknown_operation(self):
        result = example_tool.run("power", 2, 3)
        assert "error" in result
