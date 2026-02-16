"""
Observability Service — Structured logging, metrics, and tracing.
"""

import time
import uuid
import json
import logging
from functools import wraps
from typing import Callable
from contextvars import ContextVar

try:
    from prometheus_client import Counter, Histogram
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")
span_id_var: ContextVar[str] = ContextVar("span_id", default="")

if PROMETHEUS_AVAILABLE:
    REQUEST_COUNT = Counter("agent_requests_total", "Total requests", ["agent_name", "status"])
    REQUEST_LATENCY = Histogram("agent_request_latency_seconds", "Latency", ["agent_name"])
    TOKEN_USAGE = Counter("agent_tokens_total", "Tokens consumed", ["agent_name", "direction"])
    COST_TOTAL = Counter("agent_cost_usd_total", "Cost USD", ["agent_name"])
    TOOL_CALLS = Counter("agent_tool_calls_total", "Tool calls", ["agent_name", "tool_name"])
    ERROR_COUNT = Counter("agent_errors_total", "Errors", ["agent_name", "error_type"])


class StructuredLogger:
    """JSON structured logger with Prometheus metrics."""

    def __init__(self, agent_name: str = "agent", log_level: str = "INFO"):
        self.agent_name = agent_name
        self.logger = logging.getLogger(agent_name)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self.logger.addHandler(handler)

    def log_request(self, request_id: str, status: str, latency_ms: float,
                    tokens_input: int = 0, tokens_output: int = 0,
                    cost_estimate: float = 0.0, model_name: str = "",
                    tool_name: str = "", error: str = "", **extra):
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "agent_name": self.agent_name, "request_id": request_id,
            "trace_id": trace_id_var.get(""), "span_id": span_id_var.get(""),
            "model_name": model_name, "status": status,
            "latency_ms": round(latency_ms, 2),
            "tokens_input": tokens_input, "tokens_output": tokens_output,
            "cost_estimate": round(cost_estimate, 6),
            "tool_name": tool_name, "error": error, **extra,
        }
        if status == "fail":
            self.logger.error(json.dumps(entry))
        else:
            self.logger.info(json.dumps(entry))

        if PROMETHEUS_AVAILABLE:
            REQUEST_COUNT.labels(agent_name=self.agent_name, status=status).inc()
            REQUEST_LATENCY.labels(agent_name=self.agent_name).observe(latency_ms / 1000)
            TOKEN_USAGE.labels(agent_name=self.agent_name, direction="input").inc(tokens_input)
            TOKEN_USAGE.labels(agent_name=self.agent_name, direction="output").inc(tokens_output)
            COST_TOTAL.labels(agent_name=self.agent_name).inc(cost_estimate)
            if tool_name:
                TOOL_CALLS.labels(agent_name=self.agent_name, tool_name=tool_name).inc()
            if status == "fail":
                ERROR_COUNT.labels(agent_name=self.agent_name, error_type=error[:50]).inc()


def new_trace() -> str:
    tid = str(uuid.uuid4())
    trace_id_var.set(tid)
    span_id_var.set(str(uuid.uuid4())[:8])
    return tid

def new_span() -> str:
    sid = str(uuid.uuid4())[:8]
    span_id_var.set(sid)
    return sid

def track_latency(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            logging.getLogger("latency").debug(f"{func.__name__} took {(time.time()-start)*1000:.2f}ms")
    return wrapper
