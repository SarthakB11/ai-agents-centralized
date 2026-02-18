"""
Agno Single Agent Framework — FastAPI Application Entry Point.

This module serves the agent via FastAPI with:
  - Full Agno-powered agent (automatic tool routing, memory, streaming)
  - Enterprise guardrails and observability
  - Integration endpoints (webhook, whatsapp, slack)
  - Skills management API

Run:
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Or with AgentOS (recommended for production):
    pip install 'agno[os]'
    fastapi dev main.py
"""

import logging
from typing import Optional, AsyncIterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent import MyAgent   # Your custom agent — see agent.py

logger = logging.getLogger(__name__)

# ─── Initialize Agent ────────────────────────────────────────────────────────

agent = MyAgent(
    name="agno-agent",
    spec_path="agent_spec.yaml",
    enable_guardrails=True,
    enable_observability=True,
    enable_memory=True,
    db_file="agent_sessions.db",
    log_level="INFO",
    log_format="pretty",     # Change to "json" for production
)

# ─── FastAPI App ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agno Single Agent",
    description="Production AI agent powered by the Agno framework",
    version="1.0.0",
)

# ─── Auto-wire integration skills as routers ─────────────────────────────────

def _wire_integrations():
    """Discover enabled integration skills and mount their FastAPI routers."""
    for skill in agent.skill_loader.get_integrations():
        if skill.module is None:
            continue

        config = skill.config or {}
        prefix = config.get("prefix", f"/integration/{skill.name}")

        if hasattr(skill.module, "create_webhook_router"):
            router = skill.module.create_webhook_router(agent, prefix=prefix)
            app.include_router(router)
            logger.info(f"Integration wired: {skill.name} → {prefix}")

        elif hasattr(skill.module, "create_whatsapp_router"):
            router = skill.module.create_whatsapp_router(agent, prefix=prefix)
            app.include_router(router)
            logger.info(f"Integration wired: {skill.name} → {prefix}")

        else:
            logger.warning(f"Integration '{skill.name}' has no router factory")

_wire_integrations()

# ─── API Models ───────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    input: str
    request_id: Optional[str] = None
    session_id: Optional[str] = "default"
    stream: bool = False  # Enable streaming responses

class ChatResponse(BaseModel):
    request_id: str
    output: str
    tool_calls: list = []
    metadata: dict = {}

# ─── Routes ───────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    """Health check with agent and skills status."""
    summary = agent.get_skills_summary()
    return {
        "status": "ok",
        "agent": agent.name,
        "version": "1.0.0",
        "framework": "agno",
        "model": agent.agno_agent.model.id,
        "memory_enabled": agent.agno_agent.db is not None,
        "skills": summary,
    }


@app.post("/agent/chat")
async def chat(req: ChatRequest):
    """
    Main chat endpoint.

    Supports both regular (JSON) and streaming (SSE) responses.
    Set stream=true in the request body for streaming.
    """
    if req.stream:
        return StreamingResponse(
            _stream_response(req),
            media_type="text/event-stream",
        )

    return agent.handle_request({
        "input": req.input,
        "request_id": req.request_id,
        "session_id": req.session_id,
    })


async def _stream_response(req: ChatRequest) -> AsyncIterator[str]:
    """Stream the agent response as Server-Sent Events.

    Guardrails (PII, injection) run automatically via Agno's pre_hooks.
    InputCheckError is caught and returned as an SSE error event.
    """
    try:
        from agno.exceptions import InputCheckError
    except ImportError:
        InputCheckError = Exception

    try:
        input_text = agent.before_llm(req.input, {})

        async for chunk in await agent.agno_agent.astream(
            input_text,
            session_id=req.session_id,
        ):
            if chunk.content:
                yield f"data: {chunk.content}\n\n"

        yield "data: [DONE]\n\n"

    except InputCheckError as e:
        yield f"data: {{\"error\": \"Request blocked: {e}\"}}\n\n"
    except Exception as e:
        logger.error(f"Streaming error: {e}")
        yield f"data: {{\"error\": \"{e}\"}}\n\n"


@app.post("/agent/reload-skills")
async def reload_skills():
    """Hot-reload skills from the skills/ directory without restart."""
    agent.reload_skills()
    return {
        "status": "reloaded",
        "skills": agent.get_skills_summary(),
    }


@app.get("/agent/skills")
async def list_skills():
    """List all currently loaded skills and their status."""
    return agent.get_skills_summary()


@app.get("/agent/available-skills")
async def available_skills():
    """
    List all skills available in the framework (loaded or not).

    Shows both custom toolkits and Agno built-in toolkits,
    along with which dependencies are required.
    """
    from agno_single_agent_framework.core.skill_loader import SkillLoader
    from agno_single_agent_framework.tools.agno_builtin import AGNO_BUILTIN_REGISTRY

    all_skills = SkillLoader.list_available_skills()

    # Annotate Agno built-ins
    for skill in all_skills:
        if skill["name"] in AGNO_BUILTIN_REGISTRY:
            skill["source"] = "agno_builtin"
        else:
            skill["source"] = "custom"

    return {
        "available": all_skills,
        "agno_builtins": list(AGNO_BUILTIN_REGISTRY.keys()),
        "note": "Drop a YAML file in skills/ with 'name' and 'enabled: true' to activate any skill.",
    }


@app.get("/agent/memory/{session_id}")
async def get_session_memory(session_id: str):
    """Retrieve conversation history for a session."""
    # Agno manages memory via SqliteDb — query it directly
    if agent.agno_agent.db is None:
        return {"error": "Memory is not enabled for this agent"}

    try:
        history = agent.agno_agent.db.get_messages(session_id=session_id)
        return {
            "session_id": session_id,
            "message_count": len(history) if history else 0,
            "messages": history or [],
        }
    except Exception as e:
        return {"error": str(e)}
