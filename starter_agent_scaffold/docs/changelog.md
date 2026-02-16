# Changelog

All notable changes to this agent are documented here.

## [1.0.0] — Initial Release

### Added
- Core agent with multi-provider LLM support (OpenAI, Gemini, Anthropic)
- Tool system: calculator, web search, database lookup, HTTP request, email sender, file parser
- Integration templates: Slack, WhatsApp, generic Webhook
- Guardrails: PII detection/redaction, prompt injection detection, token limits
- Observability: structured JSON logging, Prometheus metrics, distributed tracing
- Evaluation: benchmark runner, metrics (accuracy, latency, cost, tokens), sample dataset
- Infrastructure: Dockerfile, docker-compose, Kubernetes manifest with HPA
- CI/CD: GitHub Actions pipeline with lint, test, integration test, spec validation
- Pydantic models for all API contracts and inter-agent communication
