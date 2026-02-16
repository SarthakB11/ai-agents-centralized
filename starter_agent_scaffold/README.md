# 🚀 Starter Agent Scaffold

A **compliance-ready** template for building new AI agents. Clone this folder, rename it, and start building — all organizational standards are baked in.

---

## 📁 Folder Structure

```
starter_agent_scaffold/
│
├── agent_spec.yaml            ← Agent identity, inputs/outputs, LLM config, secrets, guardrails
├── requirements.txt           ← Python dependencies (FastAPI, OpenAI, Redis, pytest, etc.)
├── README.md                  ← This file
│
├── app/                       ← Core application code
│   ├── main.py                ← FastAPI entry point with /health and /agent/chat endpoints
│   ├── config.py              ← Environment-based configuration loader (Pydantic BaseSettings)
│   ├── agent.py               ← Core agent logic: memory loading → tool routing → LLM call → memory save
│   ├── prompts/
│   │   └── system_prompt.txt  ← Versioned system prompt (never hardcode prompts in code)
│   ├── tools/
│   │   └── example_tool.py    ← Example tool (calculator). Add your domain tools here.
│   ├── memory/
│   │   └── memory_manager.py  ← Session memory (local dict mock; swap for Redis in production)
│   ├── models/                ← Pydantic schemas for request/response validation
│   └── services/
│       └── llm_client.py      ← LLM wrapper: abstracts provider calls, returns output + token count
│
├── tests/                     ← Test suites
│   ├── test_agent.py          ← Unit tests: tool correctness, agent structure verification
│   └── integration_tests/
│       └── test_flow.py       ← End-to-end flow test with mocked LLM (no API costs)
│
├── evaluation/                ← Benchmark datasets and scoring scripts (add eval_dataset.json here)
│
├── infra/
│   └── Dockerfile             ← Production Docker image (Python 3.9, uvicorn on port 8000)
│
├── ci/
│   └── ci_pipeline.yaml       ← GitHub Actions: lint, unit tests, integration tests, spec validation
│
└── docs/                      ← Agent-specific architecture docs and changelog
```

---

## ⚡ Quick Start

```bash
# 1. Copy and rename
cp -r starter_agent_scaffold/ my-new-agent/
cd my-new-agent/

# 2. Update agent identity
#    Edit agent_spec.yaml → change agent_name, owner, tools, etc.

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure secrets (create .env file)
echo "OPENAI_API_KEY=sk-..." > .env
echo "REDIS_URL=redis://localhost:6379" >> .env

# 5. Validate your spec
python ../agent_spec_validator.py agent_spec.yaml

# 6. Run the agent
python app/main.py
# → API at http://localhost:8000
# → Health check: GET /health
# → Chat: POST /agent/chat

# 7. Run tests
pytest tests/
```

---

## 🔑 Key Files Explained

| File | Purpose |
|------|---------|
| `agent_spec.yaml` | Declares the agent's identity, capabilities, LLM config, required secrets, and guardrails. Validated by `agent_spec_validator.py`. |
| `app/main.py` | FastAPI server exposing `/health` (GET) and `/agent/chat` (POST) endpoints. |
| `app/agent.py` | Core request handler: loads memory → routes to tools → calls LLM → saves memory → returns response. |
| `app/config.py` | Loads configuration from `.env` using Pydantic `BaseSettings`. Never hardcode secrets. |
| `app/services/llm_client.py` | Wraps LLM provider calls. Swap the provider here without touching agent logic. |
| `app/memory/memory_manager.py` | Manages session history. Default is an in-memory dict; replace with Redis for production. |
| `app/tools/example_tool.py` | Example tool implementation. Add new tools as separate files in `app/tools/`. |
| `app/prompts/system_prompt.txt` | The system prompt. Version this file and log the version in every execution. |
| `ci/ci_pipeline.yaml` | GitHub Actions workflow: linting, unit tests, integration tests, and spec validation. |
| `infra/Dockerfile` | Production-ready container image. |

---

## 🧪 Testing

- **Unit tests** (`tests/test_agent.py`): Validate individual components (tools, agent structure).
- **Integration tests** (`tests/integration_tests/test_flow.py`): Test the full request flow with mocked LLM calls — no API costs.

---

## 📏 Compliance

This scaffold conforms to:
- [AI Agents Specification](../docs/ai-agents-specification.md) — Architecture & folder structure
- [Observability Framework](../docs/central-observability-framework-specification.md) — Logging & metrics
- [Risk Blueprint](../docs/risk-and-compliance-blueprint.md) — Security & guardrails
