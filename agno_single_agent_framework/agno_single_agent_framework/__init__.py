"""
Agno Single Agent Framework — Agno-powered framework for building standardized AI agents.

This framework integrates the Agno agent framework for advanced agentic capabilities
while preserving enterprise features like guardrails and observability.

Usage:
    pip install ./agno_single_agent_framework

    # Recommended: Use Agno-powered agent
    from agno_single_agent_framework import AgnoBaseAgent

    # Legacy: Use custom LLM orchestration
    from agno_single_agent_framework import BaseAgent
"""

from agno_single_agent_framework.core.base_agent import BaseAgent  # Legacy
from agno_single_agent_framework.core.agno_base_agent import AgnoBaseAgent  # Recommended
from agno_single_agent_framework.core.skill_loader import SkillLoader, Skill
from agno_single_agent_framework.providers.llm_client import LLMClient, create_provider
from agno_single_agent_framework.providers.base_provider import LLMResponse
from agno_single_agent_framework.core.tool_router import ToolRouter
from agno_single_agent_framework.services.guardrails import Guardrails
from agno_single_agent_framework.services.observability import StructuredLogger, new_trace
from agno_single_agent_framework.services.logging import setup_logging, get_logger, LogContext
from agno_single_agent_framework.core.memory import MemoryManager

__version__ = "1.0.0-agno"

__all__ = [
    "BaseAgent",  # Legacy
    "AgnoBaseAgent",  # Recommended
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
