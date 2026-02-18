"""
Tools for the Agno Single Agent Framework.

All tools are available as both Agno Toolkits (recommended) and
legacy module-style for backward compatibility.
"""

# Agno Toolkits (recommended)
from agno_single_agent_framework.tools.calculator import CalculatorToolkit
from agno_single_agent_framework.tools.web_search import WebSearchToolkit
from agno_single_agent_framework.tools.http_request import HTTPRequestToolkit
from agno_single_agent_framework.tools.email_sender import EmailSenderToolkit
from agno_single_agent_framework.tools.file_parser import FileParserToolkit
from agno_single_agent_framework.tools.database_lookup import DatabaseLookupToolkit

# Legacy module imports (backward compatibility)
from agno_single_agent_framework.tools import calculator
from agno_single_agent_framework.tools import web_search
from agno_single_agent_framework.tools import database_lookup
from agno_single_agent_framework.tools import http_request
from agno_single_agent_framework.tools import email_sender
from agno_single_agent_framework.tools import file_parser

__all__ = [
    # Agno Toolkits
    "CalculatorToolkit",
    "WebSearchToolkit",
    "HTTPRequestToolkit",
    "EmailSenderToolkit",
    "FileParserToolkit",
    "DatabaseLookupToolkit",
    # Legacy modules
    "calculator",
    "web_search",
    "database_lookup",
    "http_request",
    "email_sender",
    "file_parser",
]
