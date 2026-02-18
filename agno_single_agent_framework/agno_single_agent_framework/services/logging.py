"""
Logging — Structured, configurable logging with Agno integration.

Uses agno.utils.log.configure_agno_logging() to wire Agno's internal
logger to the same handler/formatter, so agent internals and your app
produce a consistent log stream.

Provides:
  - JSON structured logging (production) and pretty console logging (dev)
  - Request context correlation via ContextVars (request_id, session_id)
  - File handler with rotation
"""

import os
import sys
import json
import time
import logging
import logging.handlers
from typing import Optional
from contextvars import ContextVar

from agno.utils.log import configure_agno_logging

# Context variables for request-scoped correlation IDs
_request_id: ContextVar[str] = ContextVar("log_request_id", default="")
_session_id: ContextVar[str] = ContextVar("log_session_id", default="")
_agent_name: ContextVar[str] = ContextVar("log_agent_name", default="agent")


class JSONFormatter(logging.Formatter):
    """Emits structured JSON log lines with agent + request context."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": (
                time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
                + f".{int(record.msecs):03d}Z"
            ),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "agent": _agent_name.get("agent"),
            "request_id": _request_id.get(""),
            "session_id": _session_id.get(""),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }
        return json.dumps(log_entry, default=str)


class PrettyFormatter(logging.Formatter):
    """Human-readable colored output for development."""

    COLORS = {
        "DEBUG":    "\033[36m",
        "INFO":     "\033[32m",
        "WARNING":  "\033[33m",
        "ERROR":    "\033[31m",
        "CRITICAL": "\033[35m",
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "")
        req_id = _request_id.get("")
        prefix = f"[{req_id[:8]}] " if req_id else ""
        return (
            f"{color}{record.levelname:8}{self.RESET} "
            f"{prefix}"
            f"\033[90m{record.name}\033[0m — "
            f"{record.getMessage()}"
        )


def setup_logging(
    agent_name: str = "agent",
    level: str = "INFO",
    log_format: str = "pretty",
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,   # 10 MB
    backup_count: int = 5,
) -> logging.Logger:
    """
    Configure logging for the agent and wire Agno's internal logger
    to the same handler/formatter for a unified log stream.

    Args:
        agent_name:   Name injected into all log lines.
        level:        Log level (DEBUG, INFO, WARNING, ERROR).
        log_format:   "pretty" for dev, "json" for production.
        log_file:     Optional path — enables rotating file handler (always JSON).
        max_bytes:    Max log file size before rotation.
        backup_count: Number of rotated files to keep.
    """
    _agent_name.set(agent_name)

    logger = logging.getLogger(agent_name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()
    logger.propagate = False

    formatter = JSONFormatter() if log_format == "json" else PrettyFormatter()

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    logger.addHandler(console)

    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        fh = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        fh.setFormatter(JSONFormatter())   # always JSON in files
        logger.addHandler(fh)

    # Wire Agno's internal agent logger to the same handler
    configure_agno_logging(custom_agent_logger=logger)

    # Suppress noise from third-party libraries
    for lib in ["urllib3", "httpx", "httpcore", "openai", "google", "anthropic"]:
        logging.getLogger(lib).setLevel(logging.WARNING)

    logger.info(
        f"Logging initialized — level={level}, format={log_format}, file={log_file or 'none'}"
    )
    return logger


def set_request_context(request_id: str = "", session_id: str = ""):
    """Set request-scoped correlation IDs injected into every log line."""
    if request_id:
        _request_id.set(request_id)
    if session_id:
        _session_id.set(session_id)


def clear_request_context():
    """Clear request context after handling."""
    _request_id.set("")
    _session_id.set("")


def get_logger(name: str) -> logging.Logger:
    """Get a named logger (convenience wrapper)."""
    return logging.getLogger(name)


class LogContext:
    """
    Context manager for request-scoped logging correlation.

    Usage:
        with LogContext(request_id="req-123", session_id="sess-456"):
            logger.info("Processing request")
            # All logs within this block carry request_id + session_id
    """

    def __init__(self, request_id: str = "", session_id: str = ""):
        self.request_id = request_id
        self.session_id = session_id

    def __enter__(self):
        set_request_context(self.request_id, self.session_id)
        return self

    def __exit__(self, *args):
        clear_request_context()
