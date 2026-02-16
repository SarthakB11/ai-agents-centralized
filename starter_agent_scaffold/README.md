# 🚀 Starter Agent Scaffold

A **compliance-ready** template for building new AI agents. Clone this folder, rename it, and start building — all organizational standards are baked in.

---

## 📁 Folder Structure

```
starter_agent_scaffold/
│
├── agent_spec.yaml                ← Agent identity, LLM config, integrations, guardrails
├── requirements.txt               ← Python deps (uncomment providers/integrations you need)
├── README.md                      ← This file
│
├── app/
│   ├── main.py                    ← FastAPI entry point (/health, /agent/chat + integration routers)
│   ├── config.py                  ← Env-based config loader (Pydantic BaseSettings)
│   ├── agent.py                   ← Core agent: memory → tools → LLM → response
│   │
│   ├── services/                  ← LLM Provider Abstraction Layer
│   │   ├── base_provider.py       ← Abstract base class + LLMResponse dataclass
│   │   ├── openai_provider.py     ← OpenAI (GPT-4o, GPT-4o-mini, o1, o3-mini)
│   │   ├── gemini_provider.py     ← Google Gemini (2.5-pro, 2.5-flash, 2.0-flash)
│   │   ├── anthropic_provider.py  ← Anthropic Claude (Sonnet, Haiku, Opus)
│   │   └── llm_client.py         ← Unified LLM client + factory (auto-detects from spec)
│   │
│   ├── integrations/              ← External Platform Connectors
│   │   ├── __init__.py
│   │   ├── slack_integration.py   ← Slack bot (Bolt framework, Socket Mode)
│   │   ├── whatsapp_integration.py← WhatsApp Cloud API webhook
│   │   └── webhook_integration.py ← Generic webhook with HMAC + callback support
│   │
│   ├── prompts/
│   │   └── system_prompt.txt      ← Versioned system prompt
│   ├── tools/
│   │   └── example_tool.py        ← Example tool (calculator)
│   ├── memory/
│   │   └── memory_manager.py      ← Session memory (mock → swap for Redis)
│   └── models/                    ← Pydantic schemas
│
├── tests/
│   ├── test_agent.py              ← Unit tests
│   └── integration_tests/
│       └── test_flow.py           ← E2E flow test with mocked LLM
│
├── evaluation/                    ← Benchmark datasets & scoring
├── infra/
│   └── Dockerfile                 ← Production container
├── ci/
│   └── ci_pipeline.yaml          ← GitHub Actions CI/CD
└── docs/                          ← Agent-specific docs
```

---

## ⚡ Quick Start

```bash
# 1. Copy and rename
cp -r starter_agent_scaffold/ my-new-agent/
cd my-new-agent/

# 2. Edit agent_spec.yaml — set agent_name, provider, model, etc.

# 3. Install core deps
pip install -r requirements.txt

# 4. Install your LLM provider
pip install openai          # For OpenAI
# pip install google-generativeai  # For Gemini
# pip install anthropic      # For Anthropic

# 5. Configure secrets (.env file)
echo "OPENAI_API_KEY=sk-..." > .env

# 6. Validate spec
python ../agent_spec_validator.py agent_spec.yaml

# 7. Run
python app/main.py
# → http://localhost:8000/health
# → POST http://localhost:8000/agent/chat
```

---

## 🤖 Multi-Provider LLM Support

Switch providers by changing one line in `agent_spec.yaml`:

```yaml
# OpenAI
llm_provider:
  name: openai
  model: gpt-4o-mini

# Google Gemini
llm_provider:
  name: gemini
  model: gemini-2.5-flash

# Anthropic Claude  
llm_provider:
  name: anthropic
  model: claude-sonnet-4-20250514
```

The `LLMClient` auto-detects the provider from the spec and routes through the correct implementation. All providers return a standardized `LLMResponse` with:
- `output` — Generated text
- `tokens_input` / `tokens_output` — Token counts
- `cost_estimate` — USD cost based on model-specific pricing
- `model` / `error` — Metadata

### Adding a New Provider

1. Create `app/services/my_provider.py` extending `BaseLLMProvider`
2. Implement `generate()` and `get_provider_name()`
3. Register it in `llm_client.py`'s `create_provider()` factory

---

## 🔌 Integrations

### Slack Bot

```bash
pip install slack_bolt
```

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=...
SLACK_APP_TOKEN=xapp-...   # For Socket Mode
```

```bash
python -m app.integrations.slack_integration
```

Supports: `@mention` in channels + direct messages.

---

### WhatsApp (Meta Cloud API)

```env
WHATSAPP_API_TOKEN=...
WHATSAPP_VERIFY_TOKEN=my-verify-token
WHATSAPP_PHONE_NUMBER_ID=...
```

Webhook automatically registered at `/webhook/whatsapp`. Point Meta's webhook config to your domain.

---

### Generic Webhook

Any system can POST to `/webhook/inbound`:

```json
{
  "input": "Hello, agent!",
  "session_id": "external-session-123",
  "callback_url": "https://my-system.com/callback"  
}
```

Optional HMAC-SHA256 verification via `X-Webhook-Signature` header + `WEBHOOK_SECRET` env var.

---

## 🔑 Key Files

| File | Purpose |
|------|---------|
| `agent_spec.yaml` | Agent identity, LLM provider, integrations, guardrails |
| `app/services/llm_client.py` | Unified LLM client with provider auto-detection |
| `app/services/base_provider.py` | Abstract interface all providers implement |
| `app/integrations/slack_integration.py` | Slack bot via Bolt + Socket Mode |
| `app/integrations/whatsapp_integration.py` | WhatsApp Cloud API webhook handler |
| `app/integrations/webhook_integration.py` | Generic webhook with HMAC + callback |
| `app/agent.py` | Core agent logic |
| `app/config.py` | Environment-based settings (all secrets) |

---

## 📏 Compliance

This scaffold conforms to:
- [AI Agents Specification](../docs/ai-agents-specification.md) — Architecture & folder structure
- [Observability Framework](../docs/central-observability-framework-specification.md) — Logging & metrics
- [Risk Blueprint](../docs/risk-and-compliance-blueprint.md) — Security & guardrails
