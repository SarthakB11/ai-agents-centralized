"""OpenAI LLM Provider."""

from typing import List, Dict
from agno_single_agent_framework.providers.base_provider import BaseLLMProvider, LLMResponse

try:
    import openai
except ImportError:
    openai = None

OPENAI_PRICING = {
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    "gpt-4": {"input": 0.03, "output": 0.06},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "o1": {"input": 0.015, "output": 0.06},
    "o3-mini": {"input": 0.0011, "output": 0.0044},
}


class OpenAIProvider(BaseLLMProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", **kwargs):
        super().__init__(model=model, **kwargs)
        if openai is None:
            raise ImportError("openai package not installed. Run: pip install openai")
        self.client = openai.OpenAI(api_key=api_key)

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )
            t_in = response.usage.prompt_tokens
            t_out = response.usage.completion_tokens
            return LLMResponse(
                output=response.choices[0].message.content,
                tokens_input=t_in, tokens_output=t_out,
                model=self.model, cost_estimate=self.estimate_cost(t_in, t_out),
            )
        except Exception as e:
            return LLMResponse(output="", error=str(e), model=self.model)

    def get_provider_name(self) -> str:
        return "openai"

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        p = OPENAI_PRICING.get(self.model, {"input": 0, "output": 0})
        return (tokens_input / 1000 * p["input"]) + (tokens_output / 1000 * p["output"])
