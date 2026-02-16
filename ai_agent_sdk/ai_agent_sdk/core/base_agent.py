"""
BaseAgent — Abstract agent class that all custom agents extend.

Provides the orchestration pipeline:
  input → guardrails → memory load → tool routing → LLM → guardrails → memory save → output
"""

import os
import time
import logging
from abc import ABC
from typing import Optional, List, Dict, Any

from ai_agent_sdk.providers.llm_client import LLMClient, create_provider
from ai_agent_sdk.providers.base_provider import BaseLLMProvider, LLMResponse
from ai_agent_sdk.core.tool_router import ToolRouter
from ai_agent_sdk.core.memory import MemoryManager
from ai_agent_sdk.services.guardrails import Guardrails
from ai_agent_sdk.services.observability import StructuredLogger, new_trace

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents. Subclass this and override hooks.

    Usage:
        class MyAgent(BaseAgent):
            def setup(self):
                self.register_tool("calculator", calculator_module)

            def before_llm(self, input_text, context):
                # custom preprocessing
                return input_text

            def after_llm(self, response):
                # custom postprocessing
                return response
    """

    def __init__(
        self,
        name: str = "agent",
        provider: Optional[BaseLLMProvider] = None,
        spec_path: str = "agent_spec.yaml",
        enable_guardrails: bool = True,
        enable_observability: bool = True,
    ):
        self.name = name
        self.spec_path = spec_path

        # Core components
        self.llm = LLMClient(provider=provider, spec_path=spec_path)
        self.memory = MemoryManager()
        self.tool_router = ToolRouter()
        self.guardrails = Guardrails() if enable_guardrails else None
        self.logger = StructuredLogger(agent_name=name) if enable_observability else None

        # Load system prompt
        self.system_prompt = "You are a helpful AI assistant."
        self._load_system_prompt()

        # Call user's setup hook
        self.setup()

    def _load_system_prompt(self):
        """Load system prompt from file if exists."""
        for path in ["prompts/system_prompt.txt", "app/prompts/system_prompt.txt"]:
            if os.path.exists(path):
                with open(path, "r") as f:
                    self.system_prompt = f.read().strip()
                break

    # --- Hooks for subclasses to override ---

    def setup(self):
        """Called once during init. Register tools and configure agent here."""
        pass

    def before_llm(self, input_text: str, context: Any) -> str:
        """Hook: called before LLM generation. Modify input if needed."""
        return input_text

    def after_llm(self, response: LLMResponse) -> LLMResponse:
        """Hook: called after LLM generation. Modify output if needed."""
        return response

    def route_tools(self, input_text: str) -> Optional[Dict]:
        """
        Override to implement custom tool routing logic.
        Return tool result dict or None to skip tools.
        """
        return None

    # --- Tool Management ---

    def register_tool(self, name: str, module):
        """Register a tool module with the agent."""
        self.tool_router.register(name, module)

    # --- Main Request Handler ---

    def handle_request(self, payload: Dict) -> Dict:
        """
        Process a request through the full pipeline.

        Args:
            payload: dict with 'input', optional 'session_id', 'request_id', 'metadata'

        Returns:
            dict with 'output', 'request_id', 'tool_calls', 'metadata'
        """
        trace_id = new_trace()
        start_time = time.time()

        input_text = payload.get("input", "")
        session_id = payload.get("session_id", "default")
        request_id = payload.get("request_id", trace_id)

        tool_calls = []
        error = None

        try:
            # 1. Input guardrails
            if self.guardrails:
                safety = self.guardrails.check_input(input_text)
                if safety.get("blocked"):
                    return {
                        "request_id": request_id,
                        "output": "I'm sorry, I can't process that request.",
                        "tool_calls": [],
                        "metadata": {"blocked": True, "reason": safety.get("reason")},
                    }
                input_text = safety["sanitized_text"]

            # 2. Load memory
            context = self.memory.load(session_id)

            # 3. Pre-processing hook
            input_text = self.before_llm(input_text, context)

            # 4. Tool routing
            tool_result = self.route_tools(input_text)
            if tool_result:
                tool_calls.append(tool_result)

            # 5. Build messages
            messages = [{"role": "system", "content": self.system_prompt}]
            if context:
                messages.append({"role": "user", "content": f"Previous context: {context}"})
            user_content = input_text
            if tool_result:
                user_content += f"\n\n[Tool Result]: {tool_result}"
            messages.append({"role": "user", "content": user_content})

            # 6. LLM generation
            llm_response = self.llm.generate(messages)

            # 7. Post-processing hook
            llm_response = self.after_llm(llm_response)

            # 8. Output guardrails
            output_text = llm_response.output
            if self.guardrails:
                output_safety = self.guardrails.check_output(output_text)
                output_text = output_safety["sanitized_text"]

            # 9. Save memory
            self.memory.save(session_id, {"user": input_text, "assistant": output_text})

            # 10. Log
            latency_ms = (time.time() - start_time) * 1000
            if self.logger:
                self.logger.log_request(
                    request_id=request_id, status="success",
                    latency_ms=latency_ms,
                    tokens_input=llm_response.tokens_input,
                    tokens_output=llm_response.tokens_output,
                    cost_estimate=llm_response.cost_estimate,
                    model_name=llm_response.model,
                )

            return {
                "request_id": request_id,
                "output": output_text,
                "tool_calls": tool_calls,
                "metadata": {
                    "tokens_input": llm_response.tokens_input,
                    "tokens_output": llm_response.tokens_output,
                    "cost_estimate": llm_response.cost_estimate,
                    "model": llm_response.model,
                    "provider": self.llm.provider.get_provider_name(),
                    "latency_ms": round((time.time() - start_time) * 1000, 2),
                },
            }

        except Exception as e:
            error = str(e)
            logger.error(f"Agent error: {e}")
            if self.logger:
                self.logger.log_request(
                    request_id=request_id, status="fail",
                    latency_ms=(time.time() - start_time) * 1000,
                    error=error,
                )
            return {
                "request_id": request_id,
                "output": "An error occurred while processing your request.",
                "tool_calls": tool_calls,
                "metadata": {"error": error},
            }
