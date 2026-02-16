"""
Tool Router — Dynamic tool dispatcher.

Reads available tools from agent_spec.yaml, loads matching
tool modules, and routes tool calls from the agent.
"""

import importlib
import logging
import yaml
from typing import Optional, Any, Dict, List

logger = logging.getLogger(__name__)


# Registry of built-in tool modules
TOOL_REGISTRY = {
    "calculator": "app.tools.example_tool",
    "web_search": "app.tools.web_search",
    "database_lookup": "app.tools.database_lookup",
    "http_request": "app.tools.http_request",
    "email_sender": "app.tools.email_sender",
    "file_parser": "app.tools.file_parser",
}


class ToolRouter:
    """
    Discovers and invokes tools based on agent_spec.yaml config.
    """

    def __init__(self, spec_path: str = "agent_spec.yaml"):
        self.tools: Dict[str, Any] = {}
        self._load_tools(spec_path)

    def _load_tools(self, spec_path: str):
        """Load tools declared in agent_spec.yaml."""
        try:
            with open(spec_path, "r") as f:
                spec = yaml.safe_load(f)
            declared_tools = spec.get("tools", [])
        except FileNotFoundError:
            logger.warning(f"Spec file not found at {spec_path}, no tools loaded.")
            declared_tools = []

        for tool_def in declared_tools:
            name = tool_def.get("name")
            if name in TOOL_REGISTRY:
                try:
                    module = importlib.import_module(TOOL_REGISTRY[name])
                    self.tools[name] = module
                    logger.info(f"✅ Tool loaded: {name}")
                except ImportError as e:
                    logger.warning(f"⚠️  Tool '{name}' declared but module failed to import: {e}")
            else:
                logger.warning(f"⚠️  Tool '{name}' declared but not in TOOL_REGISTRY. Register it first.")

    def list_tools(self) -> List[str]:
        """Return list of loaded tool names."""
        return list(self.tools.keys())

    def call(self, tool_name: str, **kwargs) -> Any:
        """
        Call a tool by name with given arguments.

        Returns:
            Tool result or error dict.
        """
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found. Available: {self.list_tools()}"}

        module = self.tools[tool_name]

        # Convention: each tool module has a `run()` function
        if not hasattr(module, "run"):
            return {"error": f"Tool '{tool_name}' has no run() function"}

        try:
            result = module.run(**kwargs)
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_name}' failed: {e}")
            return {"error": str(e)}

    def get_tool_descriptions(self) -> List[Dict[str, str]]:
        """Get descriptions for all loaded tools (useful for LLM function calling)."""
        descriptions = []
        for name, module in self.tools.items():
            desc = getattr(module, "DESCRIPTION", f"Tool: {name}")
            params = getattr(module, "PARAMETERS", {})
            descriptions.append({
                "name": name,
                "description": desc,
                "parameters": params,
            })
        return descriptions
