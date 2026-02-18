"""
LLM Client — Unified interface with provider factory.
"""

import os
import yaml
from typing import Optional, List, Dict
from agno_single_agent_framework.providers.base_provider import BaseLLMProvider, LLMResponse


def _load_provider_from_spec(spec_path: str = "agent_spec.yaml") -> dict:
    try:
        with open(spec_path, "r") as f:
            return yaml.safe_load(f).get("llm_provider", {})
    except FileNotFoundError:
        return {}


def create_provider(
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    spec_path: str = "agent_spec.yaml",
    **kwargs
) -> BaseLLMProvider:
    """
    Factory to create the correct LLM provider.

    Priority: explicit args > agent_spec.yaml > env defaults.
    """
    spec = _load_provider_from_spec(spec_path)
    name = provider_name or spec.get("name", "openai")
    mdl = model or spec.get("model", "gpt-4o-mini")
    temp = kwargs.pop("temperature", spec.get("temperature", 0.7))
    max_tok = kwargs.pop("max_tokens", spec.get("max_tokens", 500))

    if name == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not set")
        from agno_single_agent_framework.providers.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=key, model=mdl, temperature=temp, max_tokens=max_tok)

    elif name == "gemini":
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY not set")
        from agno_single_agent_framework.providers.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=key, model=mdl, temperature=temp, max_tokens=max_tok)

    elif name == "anthropic":
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        from agno_single_agent_framework.providers.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=key, model=mdl, temperature=temp, max_tokens=max_tok)

    else:
        raise ValueError(f"Unsupported LLM provider: {name}. Supported: openai, gemini, anthropic")


class LLMClient:
    """High-level LLM client wrapping any provider."""

    def __init__(self, provider: Optional[BaseLLMProvider] = None, spec_path: str = "agent_spec.yaml"):
        self.provider = provider or create_provider(spec_path=spec_path)

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        return self.provider.generate(messages, **kwargs)

    def quick_generate(self, prompt: str, system_prompt: str = "You are a helpful assistant.") -> LLMResponse:
        """Convenience method for simple prompt → response."""
        return self.generate([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ])
