# Agno Integration Guide

## Overview

The `agno_single_agent_framework` integrates the [Agno framework](https://docs.agno.com) — a production-grade agentic framework for Python — with our enterprise features including guardrails, observability, and YAML-based skill management.

## What is Agno?

**Agno** is an open-source Python framework for building multi-agent systems that:
- ✅ Supports multiple LLM providers (OpenAI, Anthropic, Gemini)
- ✅ Provides built-in memory and session management
- ✅ Offers 100+ pre-built toolkits
- ✅ Handles tool execution automatically
- ✅ Includes agentic RAG with vector databases
- ✅ Streams responses in real-time
- ✅ Scales to production with AgentOS

GitHub: https://github.com/agno-agi/agno
Documentation: https://docs.agno.com

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  AgnoBaseAgent (Our Wrapper)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  Enterprise Features (Our Code):                                 │
│  • Guardrails (PII detection, prompt injection blocking)         │
│  • Observability (structured logging, metrics)                   │
│  • YAML skill management (auto-discovery)                        │
│  • Custom hooks (before_llm, after_llm, route_tools)             │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │           Agno Agent (Core Framework)                    │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  • LLM orchestration (OpenAI, Claude, Gemini)            │    │
│  │  • Tool management & automatic execution                 │    │
│  │  • Memory & session persistence (SqliteDb)               │    │
│  │  • Context management (adds history automatically)       │    │
│  │  • Streaming support                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                   │
│  Toolkits (Agno Pattern):                                        │
│  • CalculatorToolkit                                             │
│  • WebSearchToolkit                                              │
│  • HTTPRequestToolkit                                            │
│  • ... more toolkits                                             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Key Benefits

### 1. Production-Ready Agent Framework
- Agno is battle-tested with 37.9k+ GitHub stars
- Handles complex agentic loops automatically
- Built-in streaming and async support

### 2. Multi-LLM Support
- Switch between OpenAI, Anthropic, Gemini with one line
- No need to manage different API clients
- Unified interface for all providers

### 3. Automatic Tool Execution
- Agno decides when to call tools based on the conversation
- Handles multi-turn tool calling
- Manages tool failures gracefully

### 4. Built-in Memory
- Persistent session storage via SqliteDb
- Automatic context injection from previous turns
- Configurable history depth (default: 3 runs)

### 5. Enterprise Features Preserved
- All existing guardrails still work (PII detection, prompt injection)
- Observability logging intact
- YAML-based skill management maintained

## Quick Start

### Installation

```bash
pip install -e ./agno_single_agent_framework
```

### Basic Usage

```python
from agno_single_agent_framework import AgnoBaseAgent

# Create an agent with Agno
class MyAgent(AgnoBaseAgent):
    def setup(self):
        # Optional: add custom configuration
        pass

# Initialize
agent = MyAgent(
    name="my-agent",
    provider="openai",  # or "anthropic", "gemini"
    model="gpt-4o",
    skills_dir="skills",
    enable_guardrails=True,
    enable_observability=True,
    enable_memory=True,  # Persistent sessions
)

# Run
response = agent.handle_request({
    "input": "Calculate 25 * 4 and then search for recent AI news",
    "session_id": "user-123",
})

print(response["output"])
```

### Key Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `provider` | LLM provider: `openai`, `anthropic`, `gemini` | `openai` |
| `model` | Model ID (e.g., `gpt-4o`, `claude-sonnet-4-5`) | `gpt-4o-mini` |
| `enable_memory` | Enable persistent session memory | `True` |
| `db_file` | SQLite database file for memory | `{name}.db` |
| `enable_guardrails` | Enable PII detection & prompt injection blocking | `True` |
| `enable_observability` | Enable structured logging & metrics | `True` |

## Toolkits vs. Tools

### Old Pattern (Legacy BaseAgent)
```python
# Tools were simple functions with run()
def run(operation: str, a: float, b: float) -> dict:
    return {"result": a + b}
```

### New Pattern (AgnoBaseAgent)
```python
# Tools are Agno Toolkits (classes with multiple methods)
from agno.tools import Toolkit

class CalculatorToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="calculator")
        self.register(self.add)
        self.register(self.subtract)

    def add(self, a: float, b: float) -> dict:
        """Add two numbers. Agno reads this docstring."""
        return {"result": a + b}

    def subtract(self, a: float, b: float) -> dict:
        """Subtract b from a. Agno reads this docstring."""
        return {"result": a - b}
```

**Why Toolkits?**
- Agno's LLM can see all methods as separate tools
- Better organization for related functions
- Shared state across methods
- Better docstrings for LLM consumption

## Migrating from BaseAgent

### Option 1: Drop-in Replacement (Minimal Changes)

```python
# Before
from agno_single_agent_framework import BaseAgent

class MyAgent(BaseAgent):
    pass

# After
from agno_single_agent_framework import AgnoBaseAgent

class MyAgent(AgnoBaseAgent):
    pass
```

Most existing code will work unchanged because `AgnoBaseAgent` maintains the same interface.

### Option 2: Leverage Agno Features

```python
from agno_single_agent_framework import AgnoBaseAgent
from agno.tools import Toolkit

class CustomToolkit(Toolkit):
    def __init__(self):
        super().__init__(name="custom")
        self.register(self.my_function)

    def my_function(self, arg: str) -> dict:
        """Custom function description for the LLM."""
        return {"result": f"Processed: {arg}"}

class MyAgent(AgnoBaseAgent):
    def setup(self):
        # Add custom Agno toolkit
        self.add_toolkit(CustomToolkit())
```

## YAML Skill Configuration

YAML-based skill management is preserved! Enable/disable tools without code changes:

```yaml
# skills/calculator.yaml
name: calculator
enabled: true

# skills/web_search.yaml
name: web_search
enabled: true
config:
  default_results: 10
```

The framework automatically converts enabled skills to Agno toolkits.

## Model Configuration

### Via Code
```python
agent = AgnoBaseAgent(
    name="agent",
    provider="anthropic",
    model="claude-sonnet-4-5",
)
```

### Via agent_spec.yaml
```yaml
llm:
  provider: anthropic
  model: claude-sonnet-4-5
  temperature: 0.7
```

Supported providers:
- **OpenAI**: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
- **Anthropic**: `claude-sonnet-4-5`, `claude-opus-4-5`, `claude-haiku-4-5`
- **Google**: `gemini-2.0-flash-exp`, `gemini-1.5-pro`

## Memory & Sessions

Agno provides persistent memory via SqliteDb:

```python
agent = AgnoBaseAgent(
    name="agent",
    enable_memory=True,
    db_file="agent_sessions.db",
)

# Each session is isolated
response1 = agent.handle_request({
    "input": "My name is Alice",
    "session_id": "user-1",
})

response2 = agent.handle_request({
    "input": "What's my name?",
    "session_id": "user-1",  # Remembers Alice
})

response3 = agent.handle_request({
    "input": "What's my name?",
    "session_id": "user-2",  # Doesn't know (different session)
})
```

Memory includes:
- Last 3 conversation turns (configurable)
- Tool call results
- Internal agent reasoning

## Hooks & Customization

All existing hooks are preserved:

```python
class MyAgent(AgnoBaseAgent):
    def setup(self):
        """Called after Agno agent is created."""
        self.add_toolkit(CustomToolkit())

    def before_llm(self, input_text: str, context: Any) -> str:
        """Pre-process input before sending to Agno."""
        return input_text.upper()  # Example

    def after_llm(self, response: str, metadata: Dict) -> str:
        """Post-process Agno's output."""
        return response.replace("AI", "Assistant")

    def route_tools(self, input_text: str, available_tools: List[str]) -> Optional[Dict]:
        """
        Custom tool routing (optional).
        Note: Agno handles this automatically, but you can override.
        """
        if "urgent" in input_text.lower():
            # Force a specific tool call
            return {"tool": "email_sender", "priority": "high"}
        return None
```

## Guardrails Integration

Guardrails wrap around Agno for security:

```
User Input
    ↓
[Input Guardrails]
  • PII Detection & Redaction
  • Prompt Injection Blocking
  • Token Limits
    ↓
[Agno Agent]
  • LLM Processing
  • Tool Execution
    ↓
[Output Guardrails]
  • PII Redaction
  • Content Safety
    ↓
Final Output
```

Example:
```python
# Input: "My SSN is 123-45-6789, please save it"
# After input guardrails: "My SSN is [REDACTED], please save it"

agent = AgnoBaseAgent(
    name="agent",
    enable_guardrails=True,
)

response = agent.handle_request({
    "input": "My email is alice@example.com",
    "session_id": "user-1",
})
# Input is sanitized before reaching Agno
# Output is sanitized before returning to user
```

## Observability

All requests are logged with structured data:

```json
{
  "request_id": "trace-abc123",
  "status": "success",
  "latency_ms": 1234,
  "tokens_input": 150,
  "tokens_output": 85,
  "model": "gpt-4o",
  "provider": "openai",
  "tool_calls": ["calculator.add", "web_search.search"],
  "agno_powered": true
}
```

## Comparison: Legacy vs. Agno

| Feature | Legacy BaseAgent | AgnoBaseAgent |
|---------|------------------|---------------|
| LLM Orchestration | Custom implementation | Agno framework |
| Tool Execution | Manual routing via `route_tools()` | Automatic via Agno |
| Memory | Custom MemoryManager | Agno's SqliteDb |
| Multi-turn | Manual context building | Automatic history injection |
| Streaming | Not supported | Agno supports streaming |
| Multi-agent | Not supported | Agno Teams & Workflows |
| Provider Switching | Custom provider classes | Agno's unified interface |
| Guardrails | ✅ | ✅ (preserved) |
| Observability | ✅ | ✅ (preserved) |
| YAML Skills | ✅ | ✅ (preserved) |

## AgentOS (Coming Soon)

Agno provides `AgentOS` for production deployment:

```python
from agno.os import AgentOS

agent_os = AgentOS(agents=[my_agent])
app = agent_os.get_app()

# Run with: fastapi dev main.py
# Provides:
# - Streaming responses
# - Authentication
# - Request isolation
# - Control plane UI
```

This will be integrated in Task #4.

## Troubleshooting

### Import Errors
```bash
# Ensure Agno is installed
pip install 'agno>=0.1.0'

# Or with all extras
pip install 'agno[os]' anthropic openai google-generativeai
```

### Model Not Found
```python
# Check provider and model compatibility
agent = AgnoBaseAgent(
    provider="openai",
    model="gpt-4o",  # Correct
    # model="claude-sonnet-4-5",  # Wrong! Use provider="anthropic"
)
```

### Tools Not Working
```python
# Ensure skills are enabled in YAML
# skills/calculator.yaml
name: calculator
enabled: true  # Must be true
```

### Memory Not Persisting
```python
# Ensure enable_memory=True and db_file is writable
agent = AgnoBaseAgent(
    enable_memory=True,
    db_file="sessions.db",  # File will be created
)
```

## Next Steps

1. ✅ Core Agno integration (Task #1, #2)
2. 🔄 Update skill loader for more toolkits (Task #3)
3. 🔄 Integrate AgentOS for FastAPI serving (Task #4)
4. 🔄 Add multi-agent support (Teams, Workflows)
5. 🔄 Add streaming support
6. 🔄 Integrate Agno's built-in toolkits (100+ available)

## Resources

- **Agno Documentation**: https://docs.agno.com
- **Agno GitHub**: https://github.com/agno-agi/agno
- **Agno Cookbook**: https://github.com/agno-agi/agno/tree/main/cookbook
- **Custom Toolkits Guide**: https://docs.agno.com/basics/tools/creating-tools/toolkits
- **AgentOS Guide**: https://docs.agno.com/agent-os/custom-fastapi/overview

## Support

For questions about:
- **Agno Framework**: See https://docs.agno.com
- **Our Integration**: Contact the Platform Team

---

**Version**: 1.0.0-agno
**Last Updated**: 2026-02-16
