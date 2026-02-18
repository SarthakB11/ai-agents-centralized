# Agno Single Agent Framework

**Production-grade framework** for building standardized single AI agents powered by [Agno](https://docs.agno.com) 🚀

This framework combines:
- ✅ **Agno's agentic capabilities** (multi-LLM, automatic tool execution, memory)
- ✅ **Enterprise features** (guardrails, observability, compliance)
- ✅ **Developer experience** (YAML-based skill management, hot-reload)

## What's New?

This framework now uses **Agno** — an open-source Python framework with 37.9k+ GitHub stars — for agent orchestration. See [AGNO_INTEGRATION.md](./AGNO_INTEGRATION.md) for full details.

**Key Benefits**:
- 🎯 Multi-LLM support (OpenAI, Anthropic, Gemini) with one line
- 🧠 Built-in memory & session management
- 🔧 Automatic tool execution (Agno decides when to use tools)
- 📦 100+ pre-built toolkits available
- 🔒 Enterprise guardrails preserved (PII, prompt injection)
- 📊 Full observability maintained

## Quick Start

## Install

```bash
# From this repo
pip install -e ./agno_single_agent_framework

# With Agno and providers
pip install 'agno[os]' anthropic openai google-generativeai
```

## Usage (Agno-Powered - Recommended)

```python
from agno_single_agent_framework import AgnoBaseAgent

class MyAgent(AgnoBaseAgent):
    def setup(self):
        # Optional: add custom configuration or toolkits
        pass

# Initialize with any LLM provider
agent = MyAgent(
    name="my-agent",
    provider="anthropic",  # or "openai", "gemini"
    model="claude-sonnet-4-5",
    skills_dir="skills",
    enable_guardrails=True,
    enable_observability=True,
    enable_memory=True,
)

# Agno automatically routes tools based on conversation!
result = agent.handle_request({
    "input": "Calculate 25 * 4 and then search for recent AI news",
    "session_id": "user-123",
})
print(result["output"])

# Memory persists across requests in the same session
result2 = agent.handle_request({
    "input": "What did I just ask you to calculate?",
    "session_id": "user-123",  # Remembers previous context
})
print(result2["output"])
```

## What's Included

This framework leverages **Agno** for agent orchestration and tool management.

| Module | Description |
|--------|-------------|
| `core.BaseAgent` | Agent base class with Agno integration |
| `core.ToolRouter` | Register and invoke tools via Agno |
| `core.MemoryManager` | Session memory (in-memory + Redis) |
| `providers` | OpenAI, Gemini, Anthropic with auto-factory |
| `services.Guardrails` | PII detection, injection blocking |
| `services.StructuredLogger` | JSON logging + Prometheus metrics |
| `tools` | Calculator, Web Search, DB Lookup, HTTP, Email, File Parser |
| `integrations` | Webhook, WhatsApp, Slack (FastAPI routers) |
| `models` | Pydantic schemas for all contracts |

## Extending

### Custom Tool
```python
# my_tool.py
DESCRIPTION = "Does something cool"
PARAMETERS = {"query": {"type": "string"}}

def run(query: str) -> dict:
    return {"result": f"Processed: {query}"}
```

### Custom Provider
```python
from agno_single_agent_framework.providers import BaseLLMProvider, LLMResponse

class MyProvider(BaseLLMProvider):
    def generate(self, messages, **kwargs):
        return LLMResponse(output="hello", tokens_input=0, tokens_output=0)
    def get_provider_name(self):
        return "my_provider"
```
