"""
Generic Webhook Integration for AI Agents.

This module provides a generic inbound webhook endpoint that
any external system can call to interact with the agent. It
supports optional HMAC signature verification for security.

Setup:
  1. Set WEBHOOK_SECRET in .env (optional, for signature verification)
  2. Point your external system to: POST https://your-domain.com/webhook/inbound

Usage:
  from app.integrations.webhook_integration import webhook_router
  app.include_router(webhook_router)
"""

import os
import hmac
import hashlib
import logging
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from app.agent import Agent

logger = logging.getLogger(__name__)

webhook_router = APIRouter(prefix="/webhook", tags=["Webhook"])

agent = Agent()


class WebhookPayload(BaseModel):
    """Standard webhook payload schema."""
    input: str
    session_id: Optional[str] = "webhook-default"
    request_id: Optional[str] = None
    callback_url: Optional[str] = None  # Optional: POST response back to this URL
    metadata: Optional[dict] = {}


def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify HMAC-SHA256 signature."""
    expected = hmac.new(
        secret.encode(), payload, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


@webhook_router.post("/inbound")
async def handle_webhook(
    request: Request,
    x_webhook_signature: Optional[str] = Header(None),
):
    """
    Generic inbound webhook endpoint.

    Accepts JSON payloads and routes them through the agent.
    Optionally verifies HMAC signature if WEBHOOK_SECRET is set.
    """
    raw_body = await request.body()
    secret = os.getenv("WEBHOOK_SECRET")

    # Verify signature if secret is configured
    if secret and x_webhook_signature:
        if not verify_signature(raw_body, x_webhook_signature, secret):
            raise HTTPException(status_code=401, detail="Invalid signature")
    elif secret and not x_webhook_signature:
        raise HTTPException(status_code=401, detail="Missing X-Webhook-Signature header")

    body = await request.json()
    payload = WebhookPayload(**body)

    logger.info(f"Webhook received: session={payload.session_id}, input={payload.input[:100]}")

    response = agent.handle_request({
        "input": payload.input,
        "request_id": payload.request_id or f"wh-{id(request)}",
        "session_id": payload.session_id,
        "metadata": {**payload.metadata, "source": "webhook"},
    })

    result = {
        "status": "success",
        "output": response["output"],
        "request_id": response.get("request_id"),
        "metadata": response.get("metadata", {}),
    }

    # Optionally POST response back to callback URL
    if payload.callback_url:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                await client.post(payload.callback_url, json=result, timeout=10)
                logger.info(f"Callback sent to {payload.callback_url}")
        except Exception as e:
            logger.error(f"Callback failed: {e}")

    return result
