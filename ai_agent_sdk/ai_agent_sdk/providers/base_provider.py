"""
Base LLM Provider Interface.

All LLM providers must implement this abstract class to ensure
consistent behavior across the agent ecosystem.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any


@dataclass
class LLMResponse:
    """Standardized response from any LLM provider."""
    output: str
    tokens_input: int = 0
    tokens_output: int = 0
    model: str = ""
    cost_estimate: float = 0.0
    error: Optional[str] = None


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    def __init__(self, model: str, temperature: float = 0.7, max_tokens: int = 500):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def generate(self, messages: List[Dict[str, str]], **kwargs) -> LLMResponse:
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        pass

    def estimate_cost(self, tokens_input: int, tokens_output: int) -> float:
        return 0.0
