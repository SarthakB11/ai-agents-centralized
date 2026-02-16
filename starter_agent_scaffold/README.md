# Starter Agent

A minimal agent built on the **AI Agent SDK**. Copy this directory to create a new agent.

## Quick Start

```bash
# 1. Install the SDK
pip install -e ../ai_agent_sdk

# 2. Install agent dependencies
pip install -r requirements.txt

# 3. Configure
cp .env.example .env
# Edit .env with your API keys

# 4. Run
uvicorn main:app --reload
```

## What to customize

| File | Purpose |
|------|---------|
| `agent.py` | Your agent logic — extend `BaseAgent`, register tools, override hooks |
| `prompts/` | System prompts and templates |
| `tools/` | Your custom tools (SDK built-ins are already available) |
| `agent_spec.yaml` | Agent metadata, LLM config, tool declarations |
| `.env` | API keys and secrets |

## Architecture

```
Your Agent (this dir)          AI Agent SDK (shared)
┌──────────────────┐          ┌──────────────────────────┐
│ agent.py         │──uses──▶ │ BaseAgent                │
│ main.py          │          │ LLM Providers (OpenAI,   │
│ prompts/         │          │   Gemini, Anthropic)     │
│ tools/ (custom)  │          │ Built-in Tools           │
│ agent_spec.yaml  │          │ Guardrails               │
│ tests/           │          │ Observability            │
│ infra/           │          │ Integrations (Webhook,   │
│                  │          │   WhatsApp, Slack)       │
└──────────────────┘          │ Memory Manager           │
                              │ Pydantic Models          │
                              └──────────────────────────┘
```

## Creating a New Agent

1. Copy this directory: `cp -r starter_agent_scaffold/ my_new_agent/`
2. Edit `agent.py` — subclass `BaseAgent`, register your tools
3. Edit `prompts/system_prompt.txt` — customize personality
4. Add custom tools in `tools/`
5. Update `agent_spec.yaml` with your agent's metadata
6. Run `python agent_spec_validator.py my_new_agent/agent_spec.yaml`
