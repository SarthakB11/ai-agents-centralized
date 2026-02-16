"""
BaseAgent — Abstract agent class that all custom agents extend.

Automatically loads skills from YAML files in the skills/ directory.
Adding a skill = drop a YAML file. Removing = delete it.
"""

import os
import time
import logging
from abc import ABC
from typing import Optional, List, Dict, Any

from single_agent_framework.providers.llm_client import LLMClient, create_provider
from single_agent_framework.providers.base_provider import BaseLLMProvider, LLMResponse
from single_agent_framework.core.tool_router import ToolRouter
from single_agent_framework.core.memory import MemoryManager
from single_agent_framework.core.skill_loader import SkillLoader, Skill
from single_agent_framework.services.guardrails import Guardrails
from single_agent_framework.services.observability import StructuredLogger, new_trace
from single_agent_framework.services.logging import setup_logging, set_request_context, clear_request_context, get_logger

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Base class for all agents. Subclass and override hooks.

    Skills are auto-loaded from the `skills/` directory (YAML files).
    Override setup() to add agent-specific configuration on top of skills.

    Usage:
        class MyAgent(BaseAgent):
            def setup(self):
                # Optional: register additional tools not in skills/
                pass

            def route_tools(self, input_text, available_tools):
                # Custom tool selection logic
                return None
    """

    def __init__(
        self,
        name: str = "agent",
        provider: Optional[BaseLLMProvider] = None,
        spec_path: str = "agent_spec.yaml",
        skills_dir: str = "skills",
        enable_guardrails: bool = True,
        enable_observability: bool = True,
        log_level: str = "INFO",
        log_format: str = "pretty",
        log_file: Optional[str] = None,
    ):
        self.name = name
        self.spec_path = spec_path
        self.skills_dir = skills_dir

        # Setup logging first
        setup_logging(
            agent_name=name, level=log_level,
            log_format=log_format, log_file=log_file,
        )
        self._logger = get_logger(name)

        # Core components
        self._logger.info(f"Initializing agent: {name}")
        self.llm = LLMClient(provider=provider, spec_path=spec_path)
        self.memory = MemoryManager()
        self.tool_router = ToolRouter()
        self.guardrails = Guardrails() if enable_guardrails else None
        self.obs_logger = StructuredLogger(agent_name=name) if enable_observability else None

        # Load system prompt
        self.system_prompt = "You are a helpful AI assistant."
        self._load_system_prompt()

        # Auto-discover and register skills from YAML files
        self.skill_loader = SkillLoader(skills_dir)
        self._load_skills()

        # User's setup hook (after skills are loaded)
        self.setup()

        self._logger.info(f"Agent '{name}' ready — {len(self.tool_router.list_tools())} tools loaded")

    def _load_system_prompt(self):
        """Load system prompt from file if exists."""
        for path in ["prompts/system_prompt.txt", "app/prompts/system_prompt.txt"]:
            if os.path.exists(path):
                with open(path, "r") as f:
                    self.system_prompt = f.read().strip()
                self._logger.debug(f"System prompt loaded from {path}")
                break

    def _load_skills(self):
        """Auto-load skills from YAML files and register them."""
        self.skill_loader.load_all()

        # Register tools
        for skill in self.skill_loader.get_tools():
            if skill.module and hasattr(skill.module, "run"):
                self.tool_router.register(skill.name, skill.module)
                self._logger.info(f"🔧 Tool registered via skill: {skill.name}")
            else:
                self._logger.warning(f"Tool skill '{skill.name}' has no run() function")

        # Register functions
        for skill in self.skill_loader.get_functions():
            if skill.module:
                func = getattr(skill.module, "run", None) or getattr(skill.module, "execute", None)
                if func:
                    self.tool_router.register_function(skill.name, func, skill.description)
                    self._logger.info(f"⚡ Function registered via skill: {skill.name}")

        # Log integrations and MCPs (they're available but wired separately)
        for skill in self.skill_loader.get_integrations():
            self._logger.info(f"🔗 Integration skill available: {skill.name}")

        for skill in self.skill_loader.get_mcps():
            self._logger.info(f"🔌 MCP skill available: {skill.name}")

        summary = self.skill_loader.summary()
        self._logger.info(
            f"Skills summary: {summary['enabled']} enabled, "
            f"{summary['disabled']} disabled, {summary['errors']} errors"
        )

    def reload_skills(self):
        """
        Hot-reload skills — re-scans the skills/ directory.
        New YAML files are picked up, deleted files are dropped.
        """
        self._logger.info("♻️  Reloading skills...")
        self.skill_loader.reload()

        # Re-register tools (clear existing first)
        old_tools = self.tool_router.list_tools()
        self.tool_router = ToolRouter()
        self._load_skills()
        self.setup()  # Re-run user setup in case they register manual tools

        new_tools = self.tool_router.list_tools()
        added = set(new_tools) - set(old_tools)
        removed = set(old_tools) - set(new_tools)

        if added:
            self._logger.info(f"➕ New tools: {added}")
        if removed:
            self._logger.info(f"➖ Removed tools: {removed}")

    # --- Hooks for subclasses ---

    def setup(self):
        """Called after skills load. Register additional tools or configure agent."""
        pass

    def before_llm(self, input_text: str, context: Any) -> str:
        """Hook: called before LLM generation."""
        return input_text

    def after_llm(self, response: LLMResponse) -> LLMResponse:
        """Hook: called after LLM generation."""
        return response

    def route_tools(self, input_text: str, available_tools: List[str] = None) -> Optional[Dict]:
        """
        Override to implement tool selection logic.
        `available_tools` lists all registered tool names.
        Return tool result dict or None.
        """
        return None

    # --- Tool Management ---

    def register_tool(self, name: str, module):
        """Manually register a tool (in addition to skills)."""
        self.tool_router.register(name, module)

    def get_skills_summary(self) -> Dict:
        """Get summary of loaded skills."""
        return self.skill_loader.summary()

    # --- Main Request Handler ---

    def handle_request(self, payload: Dict) -> Dict:
        """Process a request through the full pipeline."""
        trace_id = new_trace()
        start_time = time.time()

        input_text = payload.get("input", "")
        session_id = payload.get("session_id", "default")
        request_id = payload.get("request_id", trace_id)

        # Set logging context
        set_request_context(request_id, session_id)

        tool_calls = []
        error = None

        try:
            self._logger.info(f"Request received — session={session_id}")

            # 1. Input guardrails
            if self.guardrails:
                safety = self.guardrails.check_input(input_text)
                if safety.get("blocked"):
                    self._logger.warning(f"Request blocked: {safety.get('reason')}")
                    return {
                        "request_id": request_id,
                        "output": "I'm sorry, I can't process that request.",
                        "tool_calls": [],
                        "metadata": {"blocked": True, "reason": safety.get("reason")},
                    }
                input_text = safety["sanitized_text"]
                if safety.get("warnings"):
                    self._logger.info(f"Input warnings: {safety['warnings']}")

            # 2. Load memory
            context = self.memory.load(session_id)
            self._logger.debug(f"Memory loaded — {len(context)} entries")

            # 3. Pre-processing hook
            input_text = self.before_llm(input_text, context)

            # 4. Tool routing
            available = self.tool_router.list_tools()
            tool_result = self.route_tools(input_text, available)
            if tool_result:
                tool_calls.append(tool_result)
                self._logger.info(f"Tool called: {tool_result.get('tool', 'unknown')}")

            # 5. Build messages
            messages = [{"role": "system", "content": self.system_prompt}]
            if context:
                messages.append({"role": "user", "content": f"Previous context: {context}"})
            user_content = input_text
            if tool_result:
                user_content += f"\n\n[Tool Result]: {tool_result}"
            messages.append({"role": "user", "content": user_content})

            # 6. LLM generation
            self._logger.debug(f"Sending to LLM — {len(messages)} messages")
            llm_response = self.llm.generate(messages)

            if llm_response.error:
                self._logger.error(f"LLM error: {llm_response.error}")
            else:
                self._logger.info(
                    f"LLM response — tokens_in={llm_response.tokens_input}, "
                    f"tokens_out={llm_response.tokens_output}, "
                    f"cost=${llm_response.cost_estimate:.4f}"
                )

            # 7. Post-processing hook
            llm_response = self.after_llm(llm_response)

            # 8. Output guardrails
            output_text = llm_response.output
            if self.guardrails:
                output_safety = self.guardrails.check_output(output_text)
                output_text = output_safety["sanitized_text"]
                if output_safety.get("warnings"):
                    self._logger.info(f"Output warnings: {output_safety['warnings']}")

            # 9. Save memory
            self.memory.save(session_id, {"user": input_text, "assistant": output_text})

            # 10. Observability log
            latency_ms = (time.time() - start_time) * 1000
            if self.obs_logger:
                self.obs_logger.log_request(
                    request_id=request_id, status="success",
                    latency_ms=latency_ms,
                    tokens_input=llm_response.tokens_input,
                    tokens_output=llm_response.tokens_output,
                    cost_estimate=llm_response.cost_estimate,
                    model_name=llm_response.model,
                )

            self._logger.info(f"Request completed — {latency_ms:.0f}ms")

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
            self._logger.error(f"Agent error: {e}", exc_info=True)
            if self.obs_logger:
                self.obs_logger.log_request(
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

        finally:
            clear_request_context()
