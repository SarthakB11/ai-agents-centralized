# Single Agent Framework

Shared framework for building standardized AI agents at Beatroute.

## Install

```bash
# From this repo
pip install -e ./single_agent_framework

# With specific provider
pip install -e "./single_agent_framework[openai]"
pip install -e "./single_agent_framework[gemini]"
pip install -e "./single_agent_framework[all]"
```

## Usage

```python
from single_agent_framework import BaseAgent
from single_agent_framework.tools import calculator, web_search

class MyAgent(BaseAgent):
    def setup(self):
        self.register_tool("calculator", calculator)
        self.register_tool("web_search", web_search)

    def route_tools(self, input_text):
        if "calculate" in input_text.lower():
            return self.tool_router.call("calculator", operation="add", a=1, b=2)
        return None

# Run
agent = MyAgent(name="my-agent")
result = agent.handle_request({"input": "calculate add 5 3"})
print(result["output"])
```

## What's Included

| Module | Description |
|--------|-------------|
| `core.BaseAgent` | Agent base class with full pipeline |
| `core.ToolRouter` | Register and invoke tools |
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
from single_agent_framework.providers import BaseLLMProvider, LLMResponse

class MyProvider(BaseLLMProvider):
    def generate(self, messages, **kwargs):
        return LLMResponse(output="hello", tokens_input=0, tokens_output=0)
    def get_provider_name(self):
        return "my_provider"
```
