"""
Starter Agent — Example agent built on the AI Agent SDK.

This file demonstrates how to create a custom agent by extending BaseAgent.
Just override the hooks you need: setup(), before_llm(), after_llm(), route_tools().
"""

from ai_agent_sdk import BaseAgent
from ai_agent_sdk.tools import calculator, web_search


class StarterAgent(BaseAgent):
    """
    Example agent that demonstrates the SDK pattern.

    To build your own agent:
    1. Subclass BaseAgent
    2. Override setup() to register your tools
    3. Override route_tools() to implement your tool selection logic
    4. Optionally override before_llm() / after_llm() for custom processing
    """

    def setup(self):
        """Register tools this agent can use."""
        self.register_tool("calculator", calculator)
        self.register_tool("web_search", web_search)

    def route_tools(self, input_text: str):
        """Simple keyword-based tool routing. Replace with LLM-based routing for production."""
        input_lower = input_text.lower()

        if any(kw in input_lower for kw in ["calculate", "add", "subtract", "multiply", "divide"]):
            return self._handle_calculator(input_text)

        if any(kw in input_lower for kw in ["search", "find", "look up", "what is"]):
            return {"tool": "web_search", "query": input_text}

        return None  # No tool needed — go straight to LLM

    def _handle_calculator(self, text: str):
        """Parse calculator commands."""
        parts = text.lower().split()
        operations = {"add": "add", "subtract": "subtract", "multiply": "multiply", "divide": "divide"}

        for word in parts:
            if word in operations:
                numbers = [float(p) for p in parts if p.replace(".", "").replace("-", "").isdigit()]
                if len(numbers) >= 2:
                    result = self.tool_router.call("calculator", operation=operations[word], a=numbers[0], b=numbers[1])
                    return {"tool": "calculator", "operation": word, "result": result}

        return None

    def before_llm(self, input_text: str, context):
        """Optional: modify input before sending to LLM."""
        return input_text

    def after_llm(self, response):
        """Optional: modify output after LLM response."""
        return response
