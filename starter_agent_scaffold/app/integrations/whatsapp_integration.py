"""
WhatsApp Integration for AI Agents (via Meta Cloud API).

This module provides FastAPI endpoints for the WhatsApp Business
Cloud API webhook. It receives incoming messages and sends
responses back through the agent.

Setup:
  1. Create a Meta Developer App at https://developers.facebook.com
  2. Set up WhatsApp Business API
  3. Configure webhook URL to: https://your-domain.com/webhook/whatsapp
  4. Set WHATSAPP_API_TOKEN and WHATSAPP_VERIFY_TOKEN in .env
  5. Set WHATSAPP_PHONE_NUMBER_ID in .env

Usage:
  from app.integrations.whatsapp_integration import whatsapp_router
  app.include_router(whatsapp_router)
"""

import os
import logging
from fastapi import APIRouter, Request, HTTPException

try:
    import httpx
except ImportError:
    httpx = None

from app.agent import Agent

logger = logging.getLogger(__name__)

whatsapp_router = APIRouter(prefix="/webhook/whatsapp", tags=["WhatsApp"])

agent = Agent()

WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"


@whatsapp_router.get("")
async def verify_webhook(request: Request):
    """
    Webhook verification endpoint.
    Meta sends a GET request with a challenge to verify the webhook URL.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN")

    if mode == "subscribe" and token == verify_token:
        logger.info("WhatsApp webhook verified")
        return int(challenge)
    else:
        raise HTTPException(status_code=403, detail="Verification failed")


@whatsapp_router.post("")
async def handle_whatsapp_message(request: Request):
    """
    Handle incoming WhatsApp messages.
    Processes text messages and sends the agent's response back.
    """
    body = await request.json()

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}

        message = messages[0]
        sender = message.get("from", "unknown")
        msg_type = message.get("type", "")

        if msg_type != "text":
            await send_whatsapp_message(sender, "Sorry, I can only process text messages right now.")
            return {"status": "ok"}

        user_input = message.get("text", {}).get("body", "")
        logger.info(f"WhatsApp message from {sender}: {user_input}")

        response = agent.handle_request({
            "input": user_input,
            "request_id": f"wa-{message.get('id', '')}",
            "session_id": f"wa-{sender}",
            "metadata": {"source": "whatsapp", "sender": sender},
        })

        await send_whatsapp_message(sender, response["output"])

    except Exception as e:
        logger.error(f"Error processing WhatsApp message: {e}")

    return {"status": "ok"}


async def send_whatsapp_message(to: str, text: str):
    """Send a text message to a WhatsApp user."""
    if httpx is None:
        raise ImportError("httpx not installed. Run: pip install httpx")

    phone_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
    token = os.getenv("WHATSAPP_API_TOKEN")

    if not phone_id or not token:
        logger.error("WHATSAPP_PHONE_NUMBER_ID or WHATSAPP_API_TOKEN not set")
        return

    url = f"{WHATSAPP_API_URL}/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code != 200:
            logger.error(f"Failed to send WhatsApp message: {resp.text}")
