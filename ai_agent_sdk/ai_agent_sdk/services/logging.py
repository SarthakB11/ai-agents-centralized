"""
Logging Service — Structured, configurable logging for agents.

Provides:
- JSON structured logging with correlation IDs
- Console + file handlers with rotation
- Log level configuration per component
- Request context injection
"""

import os
import sys
import json
import time
import logging
import logging.handlers
from typing import Optional, Dict, Any
from contextvars import ContextVar

# Context variables for request correlation
_request_id: ContextVar[str] = ContextVar("log_request_id", default="")
_session_id: ContextVar[str] = ContextVar("log_session_id", default="")
_agent_name: ContextVar[str] = ContextVar("log_agent_name", default="agent")


class JSONFormatter(logging.Formatter):
    """Emits structured JSON log lines with agent context."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(record.created))
                         + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "agent": _agent_name.get("agent"),
            "request_id": _request_id.get(""),
            "session_id": _session_id.get(""),
        }

        # Include extra fields
        if hasattr(record, "extra_data"):
            log_entry.update(record.extra_data)

        # Include exception info
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
            }

        return json.dumps(log_entry, default=str)


class PrettyFormatter(logging.Formatter):
    """Human-readable colored output for development."""

    COLORS = {
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
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
    max_bytes: int = 10 * 1024 * 1024,    # 10 MB
    backup_count: int = 5,
):
    """
    Configure logging for the agent.

    Args:
        agent_name: Agent name (injected into all log lines)
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_format: "json" for structured or "pretty" for human-readable
        log_file: Optional file path for log rotation
        max_bytes: Max log file size before rotation
        backup_count: Number of rotated files to keep
    """
    _agent_name.set(agent_name)

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    root.handlers.clear()

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    if log_format == "json":
        console.setFormatter(JSONFormatter())
    else:
        console.setFormatter(PrettyFormatter())
    root.addHandler(console)

    # File handler with rotation
    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count,
        )
        file_handler.setFormatter(JSONFormatter())  # Always JSON in files
        root.addHandler(file_handler)

    # Reduce noise from third-party libraries
    for noisy_lib in ["urllib3", "httpx", "httpcore", "openai", "google", "anthropic"]:
        logging.getLogger(noisy_lib).setLevel(logging.WARNING)

    logger = logging.getLogger(agent_name)
    logger.info(f"Logging initialized — level={level}, format={log_format}, file={log_file or 'none'}")
    return logger


def set_request_context(request_id: str = "", session_id: str = ""):
    """Set request context for correlation in log lines."""
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
    Context manager for request-scoped logging.

    Usage:
        with LogContext(request_id="req-123", session_id="sess-456"):
            logger.info("Processing request")
            # All logs within this block have request_id + session_id
    """

    def __init__(self, request_id: str = "", session_id: str = ""):
        self.request_id = request_id
        self.session_id = session_id

    def __enter__(self):
        set_request_context(self.request_id, self.session_id)
        return self

    def __exit__(self, *args):
        clear_request_context()
