"""
Tool Router — Register and invoke tools dynamically.
"""

import importlib
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ToolRouter:
    """Register tool modules and call them by name."""

    def __init__(self):
        self.tools: Dict[str, Any] = {}

    def register(self, name: str, module):
        """Register a tool module. Module must have a run() function."""
        if not hasattr(module, "run"):
            raise ValueError(f"Tool '{name}' must have a run() function")
        self.tools[name] = module
        logger.info(f"Tool registered: {name}")

    def register_function(self, name: str, func, description: str = ""):
        """Register a plain function as a tool."""
        class _FnTool:
            DESCRIPTION = description
            PARAMETERS = {}
            run = staticmethod(func)
        self.tools[name] = _FnTool
        logger.info(f"Function tool registered: {name}")

    def call(self, tool_name: str, **kwargs) -> Any:
        """Invoke a tool by name."""
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found. Available: {self.list_tools()}"}
        try:
            result = self.tools[tool_name].run(**kwargs)
            logger.info(f"Tool '{tool_name}' executed successfully")
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_name}' failed: {e}")
            return {"error": str(e)}

    def list_tools(self) -> List[str]:
        return list(self.tools.keys())

    def get_descriptions(self) -> List[Dict]:
        """Get tool descriptions for LLM function calling."""
        return [
            {
                "name": name,
                "description": getattr(mod, "DESCRIPTION", name),
                "parameters": getattr(mod, "PARAMETERS", {}),
            }
            for name, mod in self.tools.items()
        ]
