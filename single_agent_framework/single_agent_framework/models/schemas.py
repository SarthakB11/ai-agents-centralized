"""
Pydantic models for request/response validation.

These schemas enforce contracts for all API interactions,
ensuring type safety and documentation consistency.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# --- Agent API Models ---

class AgentChatRequest(BaseModel):
    """Request payload for /agent/chat endpoint."""
    input: str = Field(..., description="User's input text")
    request_id: Optional[str] = Field(None, description="Unique request identifier")
    session_id: Optional[str] = Field("default", description="Session ID for memory")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class ToolCall(BaseModel):
    """Record of a tool invocation."""
    tool_name: str
    arguments: Dict[str, Any] = {}
    result: Any = None
    latency_ms: float = 0


class AgentChatResponse(BaseModel):
    """Response payload from /agent/chat endpoint."""
    request_id: str
    output: str
    tool_calls: List[ToolCall] = []
    tokens_used: int = 0
    cost_estimate: float = 0.0
    model: str = ""
    provider: str = ""
    metadata: Dict[str, Any] = {}


# --- Webhook Models ---

class WebhookRequest(BaseModel):
    """Inbound webhook payload."""
    input: str
    session_id: Optional[str] = "webhook-default"
    request_id: Optional[str] = None
    callback_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}


class WebhookResponse(BaseModel):
    """Webhook response payload."""
    status: str
    output: str
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = {}


# --- Evaluation Models ---

class EvalTestCase(BaseModel):
    """Single evaluation test case."""
    input: str
    expected_output: str
    category: Optional[str] = "general"
    difficulty: Optional[str] = "medium"


class EvalResult(BaseModel):
    """Result of a single evaluation case."""
    case_id: int
    input: str
    expected: str
    output: str
    latency_ms: float
    status: str
    match: bool = False


class BenchmarkReport(BaseModel):
    """Full benchmark report."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    total_cases: int
    accuracy: float
    mean_latency_ms: float
    total_cost_usd: float
    results: List[EvalResult] = []


# --- Agent Registry Models (for mesh design) ---

class AgentRegistryEntry(BaseModel):
    """Agent metadata for the distributed mesh registry."""
    agent_name: str
    domain: str
    version: str
    capabilities: List[str] = []
    latency_profile_ms: int = 0
    cost_profile_per_call: float = 0.0
    allowed_models: List[str] = []
    region: List[str] = []
    status: str = "active"


# --- Inter-Agent Communication Models ---

class TaskRequest(BaseModel):
    """Task delegation request between agents."""
    task_id: str
    role: str = "specialist"
    input: Dict[str, Any] = {}
    constraints: Dict[str, Any] = {}
    expected_output_schema: Optional[Dict[str, Any]] = None
    timeout_ms: int = 30000


class TaskResponse(BaseModel):
    """Task response from a specialist agent."""
    task_id: str
    status: str  # success | fail
    result: Dict[str, Any] = {}
    confidence: float = 0.0
    reasoning_summary: str = ""
    latency_ms: float = 0
