"""
LLM Client — Unified interface for all LLM providers.

Reads the provider from agent_spec.yaml or config and routes
to the correct provider implementation. Agents never call
providers directly; they always go through this client.
"""

import os
import yaml
from typing import Optional, List, Dict
from app.services.base_provider import BaseLLMProvider, LLMResponse


def _load_provider_from_spec(spec_path: str = "agent_spec.yaml") -> dict:
    """Load LLM provider config from agent_spec.yaml."""
    try:
        with open(spec_path, "r") as f:
            spec = yaml.safe_load(f)
        return spec.get("llm_provider", {})
    except FileNotFoundError:
        return {}


def create_provider(
    provider_name: Optional[str] = None,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    **kwargs
) -> BaseLLMProvider:
    """
    Factory function to create the correct LLM provider.

    Priority:
    1. Explicit arguments
    2. agent_spec.yaml values
    3. Environment variable defaults

    Usage:
        provider = create_provider()  # auto-detect from spec
        provider = create_provider("gemini", "gemini-2.5-flash")  # explicit
    """
    spec_config = _load_provider_from_spec()

    name = provider_name or spec_config.get("name", "openai")
    mdl = model or spec_config.get("model", "gpt-4o-mini")
    temp = kwargs.pop("temperature", spec_config.get("temperature", 0.7))
    max_tok = kwargs.pop("max_tokens", spec_config.get("max_tokens", 500))

    if name == "openai":
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not set")
        from app.services.openai_provider import OpenAIProvider
        return OpenAIProvider(api_key=key, model=mdl, temperature=temp, max_tokens=max_tok)

    elif name == "gemini":
        key = api_key or os.getenv("GEMINI_API_KEY")
        if not key:
            raise ValueError("GEMINI_API_KEY not set")
        from app.services.gemini_provider import GeminiProvider
        return GeminiProvider(api_key=key, model=mdl, temperature=temp, max_tokens=max_tok)

    elif name == "anthropic":
        key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not key:
            raise ValueError("ANTHROPIC_API_KEY not set")
        from app.services.anthropic_provider import AnthropicProvider
        return AnthropicProvider(api_key=key, model=mdl, temperature=temp, max_tokens=max_tok)

    else:
        raise ValueError(f"Unsupported LLM provider: {name}. Supported: openai, gemini, anthropic")


class LLMClient:
    """
    High-level LLM client used by the Agent.

    Wraps the provider factory and provides a simple generate() interface.
    Supports provider failover if configured.
    """

    def __init__(self, provider: Optional[BaseLLMProvider] = None):
        self.provider = provider or create_provider()

    def generate(self, input_text: str, context: any = None, tool_output: any = None) -> dict:
        """
        Generate a response. Builds the message list and delegates to the provider.

        Returns a dict for backward compatibility with the agent.
        """
        messages = self._build_messages(input_text, context, tool_output)
        response: LLMResponse = self.provider.generate(messages)

        if response.error:
            return {
                "output": "Error processing request",
                "error": response.error,
                "tokens_used": 0,
                "cost_estimate": 0,
            }

        return {
            "output": response.output,
            "tokens_used": response.tokens_input + response.tokens_output,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
            "cost_estimate": response.cost_estimate,
            "model": response.model,
            "provider": self.provider.get_provider_name(),
        }

    def _build_messages(self, input_text: str, context: any, tool_output: any) -> List[Dict[str, str]]:
        """Build standardized message list from agent inputs."""
        prompt_path = os.path.join("app", "prompts", "system_prompt.txt")
        system_prompt = "You are a helpful assistant."
        try:
            with open(prompt_path, "r") as f:
                system_prompt = f.read().strip()
        except FileNotFoundError:
            pass

        messages = [{"role": "system", "content": system_prompt}]

        # Add context from memory
        if context:
            context_str = str(context) if not isinstance(context, str) else context
            messages.append({"role": "user", "content": f"Previous context: {context_str}"})

        # Add tool output if available
        user_content = input_text
        if tool_output is not None:
            user_content += f"\n\n[Tool Result]: {tool_output}"

        messages.append({"role": "user", "content": user_content})
        return messages
