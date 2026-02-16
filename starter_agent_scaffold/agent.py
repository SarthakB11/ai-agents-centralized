"""
Starter Agent — Example agent built on the AI Agent SDK.

Skills are auto-loaded from the skills/ directory.
    Add a skill:    drop a YAML file in skills/
    Remove a skill: delete the YAML file
    Disable:        set `enabled: false` in the YAML

This agent only contains YOUR custom logic. Everything else
(LLM providers, guardrails, observability, tools) comes from the SDK.
"""

from single_agent_framework import BaseAgent
from typing import Optional, Dict, List


class StarterAgent(BaseAgent):
    """
    Example agent demonstrating the SDK skills pattern.

    All tools, integrations, and functions listed in skills/*.yaml
    are auto-registered by BaseAgent. You only need to:
      1. Override route_tools() to implement your selection logic
      2. Optionally override before_llm() / after_llm() for custom processing
      3. Optionally override setup() to register tools NOT in skills/
    """

    def route_tools(self, input_text: str, available_tools: List[str] = None) -> Optional[Dict]:
        """
        Simple keyword-based tool routing.
        Replace with LLM-based routing (function calling) for production.
        """
        input_lower = input_text.lower()
        available = available_tools or []

        # Calculator
        if "calculator" in available:
            if any(kw in input_lower for kw in ["calculate", "add", "subtract", "multiply", "divide"]):
                return self._handle_calculator(input_text)

        # Web Search
        if "web_search" in available:
            if any(kw in input_lower for kw in ["search", "find", "look up", "what is", "who is"]):
                result = self.tool_router.call("web_search", query=input_text)
                return {"tool": "web_search", "query": input_text, "result": result}

        # HTTP Request
        if "http_request" in available:
            if any(kw in input_lower for kw in ["fetch", "get url", "call api", "http"]):
                return {"tool": "http_request", "note": "provide URL to make request"}

        # File Parser
        if "file_parser" in available:
            if any(kw in input_lower for kw in ["parse file", "read pdf", "extract text"]):
                return {"tool": "file_parser", "note": "provide file path to parse"}

        return None  # No tool needed — go straight to LLM

    def _handle_calculator(self, text: str) -> Optional[Dict]:
        """Parse and execute calculator commands."""
        parts = text.lower().split()
        ops = {"add": "add", "subtract": "subtract", "multiply": "multiply", "divide": "divide"}

        for word in parts:
            if word in ops:
                numbers = [float(p) for p in parts if p.replace(".", "").replace("-", "").isdigit()]
                if len(numbers) >= 2:
                    result = self.tool_router.call("calculator", operation=ops[word], a=numbers[0], b=numbers[1])
                    return {"tool": "calculator", "operation": word, "result": result}
        return None
