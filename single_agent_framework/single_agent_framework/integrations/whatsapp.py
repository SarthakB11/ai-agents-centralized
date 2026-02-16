"""
WhatsApp Integration — Creates a FastAPI router for the WhatsApp Cloud API.
"""

import os
import logging
from fastapi import APIRouter, Request, HTTPException

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"


def create_whatsapp_router(agent, prefix: str = "/webhook/whatsapp") -> APIRouter:
    """
    Create a WhatsApp webhook router wired to the given agent.

    Usage:
        from single_agent_framework.integrations import create_whatsapp_router
        app.include_router(create_whatsapp_router(my_agent))
    """
    router = APIRouter(prefix=prefix, tags=["WhatsApp"])

    @router.get("")
    async def verify(request: Request):
        params = request.query_params
        if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == os.getenv("WHATSAPP_VERIFY_TOKEN"):
            return int(params.get("hub.challenge"))
        raise HTTPException(status_code=403, detail="Verification failed")

    @router.post("")
    async def handle_message(request: Request):
        body = await request.json()
        try:
            messages = body.get("entry", [{}])[0].get("changes", [{}])[0].get("value", {}).get("messages", [])
            if not messages:
                return {"status": "ok"}

            msg = messages[0]
            sender = msg.get("from", "unknown")
            if msg.get("type") != "text":
                await _send(sender, "I can only process text messages.")
                return {"status": "ok"}

            user_input = msg.get("text", {}).get("body", "")
            response = agent.handle_request({
                "input": user_input, "request_id": f"wa-{msg.get('id', '')}",
                "session_id": f"wa-{sender}", "metadata": {"source": "whatsapp", "sender": sender},
            })
            await _send(sender, response["output"])
        except Exception as e:
            logger.error(f"WhatsApp error: {e}")
        return {"status": "ok"}

    async def _send(to: str, text: str):
        if httpx is None:
            raise ImportError("httpx not installed")
        phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        token = os.getenv("WHATSAPP_API_TOKEN")
        if not phone_id or not token:
            return
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{WHATSAPP_API_URL}/{phone_id}/messages",
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}},
            )

    return router
