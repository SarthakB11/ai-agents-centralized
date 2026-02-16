"""
Google Gemini LLM Provider.

Supports: gemini-2.5-pro, gemini-2.5-flash, gemini-2.0-flash, etc.
"""

from typing import List, Dict
from app.services.base_provider import BaseLLMProvider, LLMResponse

try:
    import google.generativeai as genai
except ImportError:
    genai = None


# Approximate pricing per 1K tokens (USD)
GEMINI_PRICING = {
    "gemini-2.5-pro": {"input": 0.00125, "output": 0.01}, 
    "gemini-2.5-flash": {"input": 0.00015, "output": 0.0006},
    "gemini-2.0-flash": {"input": 0.0001, "output": 0.0004},
    "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
    "gemini-1.5-flash": {"input": 0.000075, "output": 0.0003},
}


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM Provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash", **kwargs):
        super().__init__(model=model, **kwargs)
        if genai is None:
            raise ImportError("google-generativeai package not installed. Run: pip install google-generativeai")
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel(model)

    def generate(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        try:
            # Convert standard messages format to Gemini format
            gemini_messages = []
            system_instruction = None

            for msg in messages:
                if msg["role"] == "system":
                    system_instruction = msg["content"]
                elif msg["role"] == "user":
                    gemini_messages.append({"role": "user", "parts": [msg["content"]]})
                elif msg["role"] == "assistant":
                    gemini_messages.append({"role": "model", "parts": [msg["content"]]})

            # Rebuild model with system instruction if present
            if system_instruction:
                self.client = genai.GenerativeModel(
                    self.model,
                    system_instruction=system_instruction
                )

            response = self.client.generate_content(
                gemini_messages,
                generation_config=genai.types.GenerationConfig(
                    temperature=kwargs.get("temperature", self.temperature),
                    max_output_tokens=kwargs.get("max_tokens", self.max_tokens),
                )
            )

            tokens_in = response.usage_metadata.prompt_token_count
            tokens_out = response.usage_metadata.candidates_token_count

            return LLMResponse(
                output=response.text,
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                model=self.model,
                cost_estimate=self.estimate_cost(tokens_in, tokens_out),
            )
        except Exception as e:
            return LLMResponse(output="", error=str(e), model=self.model)

    def get_provider_name(self) -> str:
        return "gemini"

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        pricing = GEMINI_PRICING.get(self.model, {"input": 0, "output": 0})
        return (tokens_input / 1000 * pricing["input"]) + (tokens_output / 1000 * pricing["output"])
