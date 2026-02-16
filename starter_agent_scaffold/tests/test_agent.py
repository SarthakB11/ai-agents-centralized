
import pytest
from app.agent import Agent

def test_calculator_tool():
    agent = Agent()
    result = agent.tools["calculator"]("add", 5, 3)
    assert result == 8

def test_agent_structure():
    agent = Agent()
    assert agent.llm is not None
    assert agent.memory is not None
    assert "calculator" in agent.tools
