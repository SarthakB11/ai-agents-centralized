"""
Unit tests for LLM provider abstraction.
"""

import pytest
from unittest.mock import MagicMock, patch
from app.services.base_provider import BaseLLMProvider, LLMResponse


class TestLLMResponse:
    def test_default_values(self):
        resp = LLMResponse(output="Hello")
        assert resp.output == "Hello"
        assert resp.tokens_input == 0
        assert resp.tokens_output == 0
        assert resp.cost_estimate == 0.0
        assert resp.error is None

    def test_full_response(self):
        resp = LLMResponse(
            output="Test", tokens_input=100, tokens_output=50,
            model="gpt-4o", cost_estimate=0.005, error=None
        )
        assert resp.tokens_input == 100
        assert resp.model == "gpt-4o"


class TestOpenAIProvider:
    @patch("app.services.openai_provider.openai")
    def test_generate_success(self, mock_openai):
        from app.services.openai_provider import OpenAIProvider

        # Mock the API response
        mock_choice = MagicMock()
        mock_choice.message.content = "Hello world"
        mock_usage = MagicMock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 5
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = mock_usage

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.OpenAI.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key", model="gpt-4o-mini")
        result = provider.generate([{"role": "user", "content": "Hi"}])

        assert result.output == "Hello world"
        assert result.tokens_input == 10
        assert result.tokens_output == 5
        assert result.error is None

    def test_cost_estimation(self):
        from app.services.openai_provider import OpenAIProvider
        with patch("app.services.openai_provider.openai"):
            provider = OpenAIProvider(api_key="test", model="gpt-4o-mini")
            cost = provider.estimate_cost(1000, 500)
            assert cost > 0


class TestLLMClientFactory:
    def test_unsupported_provider(self):
        from app.services.llm_client import create_provider
        with pytest.raises(ValueError, match="Unsupported"):
            create_provider(provider_name="unknown_provider", api_key="test")

    @patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"})
    @patch("app.services.openai_provider.openai")
    def test_creates_openai(self, mock_openai):
        from app.services.llm_client import create_provider
        provider = create_provider(provider_name="openai")
        assert provider.get_provider_name() == "openai"
