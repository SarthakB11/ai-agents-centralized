"""
FastAPI application — Thin entry point that wires agent to endpoints.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from agent import StarterAgent
from ai_agent_sdk.integrations import create_webhook_router, create_whatsapp_router

# --- Initialize ---

agent = StarterAgent(
    name="starter-agent",
    spec_path="agent_spec.yaml",
    enable_guardrails=True,
    enable_observability=True,
)

app = FastAPI(title="Starter Agent", version="1.0.0")

# --- API Models ---

class ChatRequest(BaseModel):
    input: str
    request_id: Optional[str] = None
    session_id: Optional[str] = "default"

# --- Routes ---

@app.get("/health")
async def health():
    return {"status": "ok", "agent": agent.name, "version": "1.0.0"}

@app.post("/agent/chat")
async def chat(req: ChatRequest):
    response = agent.handle_request({
        "input": req.input,
        "request_id": req.request_id,
        "session_id": req.session_id,
    })
    return response

# --- Integration Routers (from SDK) ---

app.include_router(create_webhook_router(agent))
app.include_router(create_whatsapp_router(agent))
