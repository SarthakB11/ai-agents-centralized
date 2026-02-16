"""
AI Agent SDK — Shared framework for building standardized AI agents.

Usage:
    pip install ./ai_agent_sdk

    from ai_agent_sdk import BaseAgent, create_provider
    from ai_agent_sdk.tools import calculator, web_search
    from ai_agent_sdk.integrations import SlackBot, whatsapp_router
"""

from ai_agent_sdk.core.base_agent import BaseAgent
from ai_agent_sdk.core.skill_loader import SkillLoader, Skill
from ai_agent_sdk.providers.llm_client import LLMClient, create_provider
from ai_agent_sdk.providers.base_provider import LLMResponse
from ai_agent_sdk.core.tool_router import ToolRouter
from ai_agent_sdk.services.guardrails import Guardrails
from ai_agent_sdk.services.observability import StructuredLogger, new_trace
from ai_agent_sdk.services.logging import setup_logging, get_logger, LogContext
from ai_agent_sdk.core.memory import MemoryManager

__version__ = "1.0.0"

__all__ = [
    "BaseAgent",
    "SkillLoader",
    "Skill",
    "LLMClient",
    "create_provider",
    "LLMResponse",
    "ToolRouter",
    "Guardrails",
    "StructuredLogger",
    "MemoryManager",
    "setup_logging",
    "get_logger",
    "LogContext",
    "new_trace",
]
