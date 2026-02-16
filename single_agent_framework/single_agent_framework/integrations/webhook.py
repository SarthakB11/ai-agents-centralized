"""
Generic Webhook Integration — Creates a FastAPI router for any agent.
"""

import os
import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

logger = logging.getLogger(__name__)


class WebhookPayload(BaseModel):
    input: str
    session_id: Optional[str] = "webhook-default"
    request_id: Optional[str] = None
    callback_url: Optional[str] = None
    metadata: Optional[dict] = {}


def create_webhook_router(agent, prefix: str = "/webhook") -> APIRouter:
    """
    Create a webhook router wired to the given agent instance.

    Usage:
        from single_agent_framework.integrations import create_webhook_router
        app.include_router(create_webhook_router(my_agent))
    """
    router = APIRouter(prefix=prefix, tags=["Webhook"])

    def _verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)

    @router.post("/inbound")
    async def handle_webhook(request: Request, x_webhook_signature: Optional[str] = Header(None)):
        raw_body = await request.body()
        secret = os.getenv("WEBHOOK_SECRET")

        if secret and x_webhook_signature:
            if not _verify_signature(raw_body, x_webhook_signature, secret):
                raise HTTPException(status_code=401, detail="Invalid signature")
        elif secret and not x_webhook_signature:
            raise HTTPException(status_code=401, detail="Missing X-Webhook-Signature")

        body = await request.json()
        payload = WebhookPayload(**body)

        response = agent.handle_request({
            "input": payload.input,
            "request_id": payload.request_id or f"wh-{id(request)}",
            "session_id": payload.session_id,
            "metadata": {**(payload.metadata or {}), "source": "webhook"},
        })

        result = {"status": "success", "output": response["output"],
                  "request_id": response.get("request_id"), "metadata": response.get("metadata", {})}

        if payload.callback_url:
            try:
                import httpx
                async with httpx.AsyncClient() as client:
                    await client.post(payload.callback_url, json=result, timeout=10)
            except Exception as e:
                logger.error(f"Callback failed: {e}")

        return result

    return router
