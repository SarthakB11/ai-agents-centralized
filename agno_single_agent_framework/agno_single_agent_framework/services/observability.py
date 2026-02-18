"""
Observability — Agno-native metrics and optional OpenTelemetry tracing.

Agno captures input/output tokens, latency, and tool-call counts on every
run_response automatically via run_response.metrics. This module exposes:

  - log_run_metrics() — log Agno's native metrics after each run
  - new_trace()       — generate a correlation trace ID
  - setup_otel()      — optional OTel wiring (SigNoz, Langfuse, LangSmith, etc.)

Agent-level metrics (no extra packages needed):
    run_response = agent.run("...")
    run_response.metrics.to_dict()          # per-run aggregated
    agent.get_session_metrics().to_dict()   # cumulative across all session runs

OTel backends supported (all use AgnoInstrumentor):
    SigNoz, Langfuse, LangSmith, Langtrace, Logfire, LangWatch, Weave, OpenLIT
    Install: pip install openinference-instrumentation-agno opentelemetry-sdk opentelemetry-exporter-otlp
"""

import uuid
import logging
from contextvars import ContextVar
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def new_trace() -> str:
    """Generate a new correlation trace ID and store in context."""
    tid = str(uuid.uuid4())
    trace_id_var.set(tid)
    return tid


def log_run_metrics(
    agent_logger: logging.Logger,
    request_id: str,
    run_response: Any,
    latency_ms: float,
    status: str = "success",
    error: str = "",
) -> Dict:
    """
    Log structured metrics from an Agno run_response.

    Reads token counts and timing from run_response.metrics (Agno-native),
    then emits a single structured log line. Returns the metrics dict.

    Metric fields: input_tokens, output_tokens, total_tokens, duration,
                   time_to_first_token, cache_read_tokens, cache_write_tokens
    """
    metrics: Dict = {}
    if hasattr(run_response, "metrics") and run_response.metrics:
        try:
            metrics = run_response.metrics.to_dict()
        except Exception:
            pass

    parts = [
        f"status={status}",
        f"request_id={request_id}",
        f"latency={latency_ms:.0f}ms",
        f"tokens_in={metrics.get('input_tokens', 0)}",
        f"tokens_out={metrics.get('output_tokens', 0)}",
        f"trace_id={trace_id_var.get('')}",
    ]
    if error:
        parts.append(f"error={error}")

    log_fn = agent_logger.error if status == "fail" else agent_logger.info
    log_fn("Run metrics — " + " | ".join(parts))

    return metrics


def setup_otel(
    service_name: str = "agno-agent",
    otlp_endpoint: Optional[str] = None,
    otlp_headers: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Wire up OpenTelemetry tracing via AgnoInstrumentor.

    Automatically captures all Agno agent runs as OTel spans.
    Compatible with any OTel-compatible backend (SigNoz, Langfuse, etc.).

    Args:
        service_name:   Service name shown in your observability backend.
        otlp_endpoint:  OTLP HTTP endpoint URL. If None, uses local/console exporter.
        otlp_headers:   Auth headers, e.g. {"signoz-ingestion-key": "..."}.

    Returns:
        True if OTel was set up successfully, False if dependencies are missing.

    Install:
        pip install openinference-instrumentation-agno \\
                    opentelemetry-sdk \\
                    opentelemetry-exporter-otlp

    Example — SigNoz:
        setup_otel(
            service_name="my-agent",
            otlp_endpoint="https://ingest.us.signoz.cloud:443/v1/traces",
            otlp_headers={"signoz-ingestion-key": os.getenv("SIGNOZ_INGESTION_KEY")},
        )

    Example — Langfuse (uses openlit):
        import openlit
        from langfuse import get_client
        langfuse = get_client()
        openlit.init(tracer=langfuse._otel_tracer, disable_batch=True)
    """
    try:
        from openinference.instrumentation.agno import AgnoInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry import trace

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)

        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                headers=otlp_headers or {},
            )
        else:
            exporter = ConsoleSpanExporter()

        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)
        AgnoInstrumentor().instrument()

        logger.info(
            f"OTel tracing enabled — service={service_name}, "
            f"endpoint={otlp_endpoint or 'console'}"
        )
        return True

    except ImportError as e:
        logger.warning(
            f"OTel setup skipped — missing dependencies ({e}). "
            "Install: pip install openinference-instrumentation-agno "
            "opentelemetry-sdk opentelemetry-exporter-otlp"
        )
        return False
