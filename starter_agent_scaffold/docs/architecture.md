# Starter Agent — Architecture

## Overview

This agent follows the standard architecture defined in the
[AI Agents Specification](../../docs/ai-agents-specification.md).

## Request Flow

```
Client Request
    │
    ▼
┌──────────────┐
│  FastAPI      │  ← main.py: /health, /agent/chat, webhooks
│  (Entry)      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Guardrails   │  ← PII filter, injection detection, token limits
│  (Input)      │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Agent Core   │  ← agent.py: memory load → tool routing → LLM call
└──────┬───────┘
       │
   ┌───┴───┐
   ▼       ▼
┌──────┐ ┌──────────┐
│ Tools │ │ LLM      │  ← Auto-detected from agent_spec.yaml
│       │ │ Provider  │
└──────┘ └──────────┘
       │
       ▼
┌──────────────┐
│  Guardrails   │  ← Output PII check, confidence threshold
│  (Output)     │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Observability│  ← Structured log, Prometheus metrics
└──────┬───────┘
       │
       ▼
   Response
```

## Components

| Component | File | Description |
|-----------|------|-------------|
| API Layer | `app/main.py` | FastAPI with integration routers |
| Agent Core | `app/agent.py` | Orchestration logic |
| LLM Layer | `app/services/llm_client.py` | Multi-provider factory |
| Tools | `app/tools/` | Pluggable tools via tool_router |
| Guardrails | `app/services/guardrails.py` | Safety filters |
| Observability | `app/services/observability.py` | Logging + metrics |
| Memory | `app/memory/memory_manager.py` | Session state |

## Deployment

- **Local**: `docker compose up` (see `infra/docker-compose.yml`)
- **Kubernetes**: `kubectl apply -f infra/k8s.yaml`
- **CI/CD**: GitHub Actions (see `ci/ci_pipeline.yaml`)
