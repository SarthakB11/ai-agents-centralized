"""
FastAPI application — Thin entry point.

Skills are auto-loaded from skills/ by the agent.
Integration skills (webhook, whatsapp) are auto-wired as FastAPI routers.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
import logging

from agent import StarterAgent

logger = logging.getLogger(__name__)

# --- Initialize Agent ---

agent = StarterAgent(
    name="starter-agent",
    spec_path="agent_spec.yaml",
    skills_dir="skills",
    enable_guardrails=True,
    enable_observability=True,
    log_level="INFO",
    log_format="pretty",       # "json" for production
    # log_file="logs/agent.log",  # Uncomment for file logging
)

app = FastAPI(title="Starter Agent", version="1.0.0")


# --- Auto-wire integration skills as FastAPI routers ---

def _wire_integration_skills():
    """Discover enabled integration skills and mount their routers."""
    for skill in agent.skill_loader.get_integrations():
        if skill.module is None:
            continue

        config = skill.config or {}
        prefix = config.get("prefix", f"/integration/{skill.name}")

        if hasattr(skill.module, "create_webhook_router"):
            router = skill.module.create_webhook_router(agent, prefix=prefix)
            app.include_router(router)
            logger.info(f"🔗 Integration wired: {skill.name} → {prefix}")

        elif hasattr(skill.module, "create_whatsapp_router"):
            router = skill.module.create_whatsapp_router(agent, prefix=prefix)
            app.include_router(router)
            logger.info(f"🔗 Integration wired: {skill.name} → {prefix}")

        else:
            logger.warning(f"Integration '{skill.name}' has no router factory")

_wire_integration_skills()


# --- API Models ---

class ChatRequest(BaseModel):
    input: str
    request_id: Optional[str] = None
    session_id: Optional[str] = "default"


# --- Core Routes ---

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agent": agent.name,
        "version": "1.0.0",
        "skills": agent.get_skills_summary(),
    }

@app.post("/agent/chat")
async def chat(req: ChatRequest):
    return agent.handle_request({
        "input": req.input,
        "request_id": req.request_id,
        "session_id": req.session_id,
    })

@app.post("/agent/reload-skills")
async def reload_skills():
    """Hot-reload skills from the skills/ directory."""
    agent.reload_skills()
    return {
        "status": "reloaded",
        "skills": agent.get_skills_summary(),
    }

@app.get("/agent/skills")
async def list_skills():
    """List all loaded skills."""
    return agent.get_skills_summary()

@app.get("/agent/available-skills")
async def available_skills():
    """List all built-in skills available in the SDK (whether or not they're enabled)."""
    from ai_agent_sdk.core.skill_loader import SkillLoader
    return {
        "available": SkillLoader.list_available_skills(),
        "note": "Create a YAML file in skills/ with 'name' and 'enabled: true' to activate any of these.",
    }
