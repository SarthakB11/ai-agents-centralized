"""
Tests for integration endpoints (Webhook, WhatsApp).
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestWebhookEndpoint:
    @patch("app.integrations.webhook_integration.agent")
    def test_inbound_webhook(self, mock_agent, client):
        mock_agent.handle_request.return_value = {
            "output": "Hello from agent",
            "request_id": "wh-1",
            "metadata": {},
        }

        response = client.post("/webhook/inbound", json={
            "input": "Test message",
            "session_id": "test-session",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["output"] == "Hello from agent"

    def test_webhook_missing_input(self, client):
        response = client.post("/webhook/inbound", json={})
        assert response.status_code == 422  # Validation error


class TestChatEndpoint:
    @patch("app.main.agent_instance")
    def test_chat_success(self, mock_agent, client):
        mock_agent.handle_request.return_value = {
            "request_id": "req_123",
            "output": "Agent response",
            "tool_calls": [],
            "metadata": {},
        }

        response = client.post("/agent/chat", json={
            "input": "Hello",
            "request_id": "req_123",
            "session_id": "sess_001",
        })

        assert response.status_code == 200
        data = response.json()
        assert data["output"] == "Agent response"


class TestWhatsAppVerification:
    @patch.dict("os.environ", {"WHATSAPP_VERIFY_TOKEN": "test-token"})
    def test_webhook_verify_success(self, client):
        response = client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test-token",
                "hub.challenge": "12345",
            },
        )
        assert response.status_code == 200
        assert response.json() == 12345

    @patch.dict("os.environ", {"WHATSAPP_VERIFY_TOKEN": "test-token"})
    def test_webhook_verify_failure(self, client):
        response = client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "12345",
            },
        )
        assert response.status_code == 403
