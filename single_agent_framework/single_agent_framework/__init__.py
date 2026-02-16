"""
AI Agent SDK — Shared framework for building standardized AI agents.

Usage:
    pip install ./single_agent_framework

    from single_agent_framework import BaseAgent, create_provider
    from single_agent_framework.tools import calculator, web_search
    from single_agent_framework.integrations import SlackBot, whatsapp_router
"""

from single_agent_framework.core.base_agent import BaseAgent
from single_agent_framework.core.skill_loader import SkillLoader, Skill
from single_agent_framework.providers.llm_client import LLMClient, create_provider
from single_agent_framework.providers.base_provider import LLMResponse
from single_agent_framework.core.tool_router import ToolRouter
from single_agent_framework.services.guardrails import Guardrails
from single_agent_framework.services.observability import StructuredLogger, new_trace
from single_agent_framework.services.logging import setup_logging, get_logger, LogContext
from single_agent_framework.core.memory import MemoryManager

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
