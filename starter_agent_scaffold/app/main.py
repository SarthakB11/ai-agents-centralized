"""
FastAPI entry point for the AI Agent.

Registers the core /agent/chat endpoint plus all integration routers
(WhatsApp webhook, generic webhook). Slack runs as a separate process
via Socket Mode.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.agent import Agent
from app.config import settings

# Integration routers
from app.integrations.webhook_integration import webhook_router
from app.integrations.whatsapp_integration import whatsapp_router


app = FastAPI(
    title=settings.AGENT_NAME,
    version=settings.VERSION,
    description="Standardized AI Agent API",
)

# Register integration routers
app.include_router(webhook_router)
app.include_router(whatsapp_router)


# --- Request / Response Models ---

class AgentRequest(BaseModel):
    input: str
    request_id: Optional[str] = "req_123"
    session_id: Optional[str] = "sess_001"
    metadata: Optional[dict] = {}


class AgentResponse(BaseModel):
    request_id: str
    output: str
    tool_calls: list = []
    metadata: dict = {}


# --- Agent Instance ---

agent_instance = Agent()


# --- Endpoints ---

@app.get("/health")
def health_check():
    """Health check endpoint. Used by K8s probes and monitoring."""
    return {
        "status": "ok",
        "agent": settings.AGENT_NAME,
        "version": settings.VERSION,
    }


@app.post("/agent/chat", response_model=AgentResponse)
def handle_chat(request: AgentRequest):
    """
    Core agent chat endpoint.
    Accepts text input and returns the agent's response.
    """
    try:
        response = agent_instance.handle_request(request.dict())
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
