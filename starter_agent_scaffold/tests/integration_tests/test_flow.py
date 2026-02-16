
import pytest
from app.agent import Agent
from unittest.mock import MagicMock

def test_full_agent_flow():
    # Mock LLM to avoid API costs during test
    agent = Agent()
    agent.llm.generate = MagicMock(return_value={"output": "The answer is 8", "tokens_used": 10})
    
    payload = {
        "input": "calculate add 5 3",
        "session_id": "test_sess"
    }
    
    response = agent.handle_request(payload)
    
    assert response["output"] == "The answer is 8"
    assert "calculator" in response["tool_calls"]
    assert agent.memory.load("test_sess")[0]["user"] == "calculate add 5 3"
