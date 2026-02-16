"""Anthropic Claude LLM Provider."""

from typing import List, Dict
from ai_agent_sdk.providers.base_provider import BaseLLMProvider, LLMResponse

try:
    import anthropic
except ImportError:
    anthropic = None

ANTHROPIC_PRICING = {
    "claude-sonnet-4-20250514": {"input": 0.003, "output": 0.015},
    "claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005},
    "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
}


class AnthropicProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514", **kwargs):
        super().__init__(model=model, **kwargs)
        if anthropic is None:
            raise ImportError("anthropic not installed. Run: pip install anthropic")
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        try:
            system_msg = ""
            chat_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    system_msg = msg["content"]
                else:
                    chat_messages.append(msg)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                system=system_msg if system_msg else anthropic.NOT_GIVEN,
                messages=chat_messages,
                temperature=kwargs.get("temperature", self.temperature),
            )
            t_in = response.usage.input_tokens
            t_out = response.usage.output_tokens
            return LLMResponse(
                output=response.content[0].text, tokens_input=t_in, tokens_output=t_out,
                model=self.model, cost_estimate=self.estimate_cost(t_in, t_out),
            )
        except Exception as e:
            return LLMResponse(output="", error=str(e), model=self.model)

    def get_provider_name(self) -> str:
        return "anthropic"

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        p = ANTHROPIC_PRICING.get(self.model, {"input": 0, "output": 0})
        return (tokens_input / 1000 * p["input"]) + (tokens_output / 1000 * p["output"])
