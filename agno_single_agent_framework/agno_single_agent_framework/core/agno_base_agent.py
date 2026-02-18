"""
AgnoBaseAgent — Agno-powered agent base class.

This replaces the custom LLM orchestration with Agno's Agent framework while
maintaining backward compatibility with the existing API and preserving
guardrails and observability features.
"""

import os
import time
import logging
from abc import ABC
from typing import Optional, List, Dict, Any

# Agno imports
from agno.agent import Agent
from agno.models.openai import OpenAI
from agno.models.anthropic import Claude
from agno.models.google import Gemini
from agno.db.sqlite import SqliteDb

# Agno exceptions (guardrails raise these automatically via pre/post hooks)
try:
    from agno.exceptions import InputCheckError, OutputCheckError
except ImportError:
    InputCheckError = Exception
    OutputCheckError = Exception

# Framework services
from agno_single_agent_framework.core.skill_loader import SkillLoader, Skill
from agno_single_agent_framework.services.guardrails import build_guardrail_hooks
from agno_single_agent_framework.services.observability import new_trace, log_run_metrics
from agno_single_agent_framework.services.logging import setup_logging, set_request_context, clear_request_context, get_logger

# Custom Toolkit imports
from agno_single_agent_framework.tools.calculator import CalculatorToolkit
from agno_single_agent_framework.tools.web_search import WebSearchToolkit
from agno_single_agent_framework.tools.http_request import HTTPRequestToolkit
from agno_single_agent_framework.tools.email_sender import EmailSenderToolkit
from agno_single_agent_framework.tools.file_parser import FileParserToolkit
from agno_single_agent_framework.tools.database_lookup import DatabaseLookupToolkit
from agno_single_agent_framework.tools.agno_builtin import AGNO_BUILTIN_REGISTRY, load_agno_toolkit

logger = logging.getLogger(__name__)


class AgnoBaseAgent(ABC):
    """
    Agno-powered base agent class.

    Uses Agno's framework for LLM orchestration, tool management, memory,
    guardrails (pre_hooks/post_hooks), and observability (run_response.metrics).

    Usage:
        class MyAgent(AgnoBaseAgent):
            def setup(self):
                pass  # optional custom init

            def route_tools(self, input_text, available_tools):
                return None  # optional custom tool routing
    """

    def __init__(
        self,
        name: str = "agent",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        spec_path: str = "agent_spec.yaml",
        skills_dir: Optional[str] = None,
        enable_guardrails: bool = True,
        enable_observability: bool = True,
        enable_memory: bool = True,
        db_file: Optional[str] = None,
        storage_type: str = "sqlite",
        db_url: Optional[str] = None,
        log_level: str = "INFO",
        log_format: str = "pretty",
        log_file: Optional[str] = None,
    ):
        self.name = name
        self.spec_path = spec_path
        self.skills_dir = skills_dir
        self._enable_observability = enable_observability

        # Setup logging first — also wires Agno's internal logger
        setup_logging(
            agent_name=name, level=log_level,
            log_format=log_format, log_file=log_file,
        )
        self._logger = get_logger(name)
        self._logger.info(f"Initializing Agno-powered agent: {name}")

        # Load system prompt
        self.system_prompt = self._load_system_prompt()

        # Auto-discover and load skills from YAML files
        self.skill_loader = SkillLoader(skills_dir)
        self._toolkits = []
        self._load_skills()

        # Determine model from spec or parameters
        model_config = self._get_model_config(provider, model, spec_path)

        # Build Agno-native guardrail hooks
        pre_hooks, post_hooks = [], []
        if enable_guardrails:
            pre_hooks, post_hooks = build_guardrail_hooks()
            self._logger.info(
                f"Guardrails: {len(pre_hooks)} pre_hook(s), {len(post_hooks)} post_hook(s)"
            )

        # Create Agno agent — guardrails attach here, enforced on every run
        self.agno_agent = Agent(
            name=name,
            model=model_config["model_instance"],
            tools=self._toolkits,
            db=self._create_storage(enable_memory, storage_type, db_file, db_url),
            add_history_to_context=enable_memory,
            num_history_runs=3 if enable_memory else 0,
            instructions=self.system_prompt,
            markdown=True,
            show_tool_calls=True,
            pre_hooks=pre_hooks,
            post_hooks=post_hooks,
        )

        # User's setup hook (after Agno agent is created)
        self.setup()

        self._logger.info(
            f"Agent '{name}' ready — {len(self._toolkits)} toolkits, "
            f"guardrails={'on' if enable_guardrails else 'off'}"
        )

    def _load_system_prompt(self) -> str:
        """Load system prompt from file if exists."""
        for path in ["prompts/system_prompt.txt", "app/prompts/system_prompt.txt"]:
            if os.path.exists(path):
                with open(path, "r") as f:
                    prompt = f.read().strip()
                self._logger.debug(f"System prompt loaded from {path}")
                return prompt
        return "You are a helpful AI assistant."

    def _get_model_config(self, provider: Optional[str], model: Optional[str], spec_path: str) -> Dict:
        """Determine which Agno model to use based on configuration."""
        if os.path.exists(spec_path):
            try:
                import yaml
                with open(spec_path) as f:
                    spec = yaml.safe_load(f)
                    llm_config = spec.get("llm", {})
                    provider = provider or llm_config.get("provider", "openai")
                    model = model or llm_config.get("model", "gpt-4o-mini")
            except Exception as e:
                self._logger.warning(f"Could not load spec: {e}")
                provider = provider or "openai"
                model = model or "gpt-4o-mini"
        else:
            provider = provider or "openai"
            model = model or "gpt-4o-mini"

        if provider == "openai":
            return {"provider": "openai", "model": model, "model_instance": OpenAI(id=model)}
        elif provider == "anthropic":
            return {"provider": "anthropic", "model": model, "model_instance": Claude(id=model)}
        elif provider == "gemini":
            return {"provider": "gemini", "model": model, "model_instance": Gemini(id=model)}
        else:
            self._logger.warning(f"Unknown provider '{provider}', defaulting to OpenAI")
            return {"provider": "openai", "model": "gpt-4o-mini", "model_instance": OpenAI(id="gpt-4o-mini")}

    def _create_storage(self, enable_memory: bool, storage_type: str, db_file: Optional[str], db_url: Optional[str]):
        """Create the appropriate storage backend for agent memory."""
        if not enable_memory:
            return None
        if storage_type == "postgres" and db_url:
            try:
                from agno.storage.agent.postgres import PostgresAgentStorage
                storage = PostgresAgentStorage(connection_string=db_url)
                self._logger.info("PostgresAgentStorage backend initialized")
                return storage
            except ImportError:
                self._logger.warning(
                    "PostgresAgentStorage not available (install: pip install psycopg2-binary), "
                    "falling back to SQLite"
                )
        return SqliteDb(db_file=db_file or f"{self.name}.db")

    def _load_skills(self):
        """Auto-load skills from YAML files and create Agno toolkits."""
        self.skill_loader.load_all()

        custom_toolkit_registry = {
            "calculator":      CalculatorToolkit,
            "web_search":      WebSearchToolkit,
            "http_request":    HTTPRequestToolkit,
            "email_sender":    EmailSenderToolkit,
            "file_parser":     FileParserToolkit,
            "database_lookup": DatabaseLookupToolkit,
        }

        for skill in self.skill_loader.get_tools():
            if skill.name in custom_toolkit_registry:
                toolkit = custom_toolkit_registry[skill.name]()
                self._toolkits.append(toolkit)
                self._logger.info(f"🔧 Custom toolkit registered: {skill.name}")
            elif skill.name in AGNO_BUILTIN_REGISTRY:
                toolkit = load_agno_toolkit(skill.name)
                if toolkit:
                    self._toolkits.append(toolkit)
                    self._logger.info(f"📦 Agno built-in toolkit registered: {skill.name}")
                else:
                    self._logger.warning(f"Agno toolkit '{skill.name}' could not be loaded (missing dependency?)")
            else:
                self._logger.warning(f"Unknown tool skill '{skill.name}' — not in custom or Agno registries")

        for skill in self.skill_loader.get_integrations():
            self._logger.info(f"🔗 Integration skill available: {skill.name}")

        summary = self.skill_loader.summary()
        self._logger.info(
            f"Skills summary: {summary['enabled']} enabled, "
            f"{summary['disabled']} disabled, {summary['errors']} errors"
        )

    def reload_skills(self):
        """Hot-reload skills — re-scans the skills directory and recreates Agno agent."""
        self._logger.info("♻️  Reloading skills...")
        self.skill_loader.reload()
        old_count = len(self._toolkits)
        self._toolkits = []
        self._load_skills()
        self.agno_agent.tools = self._toolkits
        self._logger.info(f"Reloaded: {old_count} → {len(self._toolkits)} toolkits")

    # --- Hooks for subclasses ---

    def setup(self):
        """Called after Agno agent is created. Override to add custom configuration."""
        pass

    def before_llm(self, input_text: str, context: Any) -> str:
        """Hook: called before sending to Agno agent."""
        return input_text

    def after_llm(self, response: str, metadata: Dict) -> str:
        """Hook: called after Agno agent responds."""
        return response

    def route_tools(self, input_text: str, available_tools: List[str] = None) -> Optional[Dict]:
        """
        Override to implement custom tool selection logic (if needed).
        Agno handles tool routing automatically — this hook is for custom pre-processing.
        """
        return None

    # --- Tool Management ---

    def add_toolkit(self, toolkit):
        """Add a custom Agno toolkit to the agent."""
        self._toolkits.append(toolkit)
        self.agno_agent.tools.append(toolkit)
        self._logger.info(f"Custom toolkit added: {toolkit.name}")

    def get_skills_summary(self) -> Dict:
        """Get summary of loaded skills."""
        return self.skill_loader.summary()

    # --- Main Request Handler ---

    def handle_request(self, payload: Dict) -> Dict:
        """
        Process a request through Agno agent.

        Guardrails run automatically via Agno's pre_hooks / post_hooks.
        If a pre_hook blocks the request, InputCheckError is raised and
        caught here — no manual checking needed.
        """
        trace_id = new_trace()
        start_time = time.time()

        input_text = payload.get("input", "")
        session_id = payload.get("session_id", "default")
        request_id = payload.get("request_id", trace_id)

        set_request_context(request_id, session_id)

        try:
            self._logger.info(f"Request received — session={session_id}")

            # Pre-processing hook
            input_text = self.before_llm(input_text, {})

            # Run Agno agent — pre_hooks (guardrails) fire here automatically
            agno_response = self.agno_agent.run(
                input_text,
                stream=False,
                session_id=session_id,
            )

            output_text = (
                agno_response.content
                if hasattr(agno_response, "content")
                else str(agno_response)
            )
            tool_calls = getattr(agno_response, "tool_calls", [])

            # Post-processing hook (post_hooks/guardrails already applied by Agno)
            output_text = self.after_llm(output_text, {"tool_calls": tool_calls})

            latency_ms = (time.time() - start_time) * 1000
            metrics = {}
            if self._enable_observability:
                metrics = log_run_metrics(self._logger, request_id, agno_response, latency_ms)

            return {
                "request_id": request_id,
                "output": output_text,
                "tool_calls": [{"tool": tc} for tc in tool_calls] if tool_calls else [],
                "metadata": {
                    "tokens_input":  metrics.get("input_tokens", 0),
                    "tokens_output": metrics.get("output_tokens", 0),
                    "model":         self.agno_agent.model.id,
                    "provider":      self.agno_agent.model.name,
                    "latency_ms":    round(latency_ms, 2),
                    "agno_powered":  True,
                },
            }

        except InputCheckError as e:
            self._logger.warning(f"Request blocked by guardrail: {e}")
            return {
                "request_id": request_id,
                "output": "I'm sorry, I can't process that request.",
                "tool_calls": [],
                "metadata": {"blocked": True, "reason": str(e)},
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)
            self._logger.error(f"Agent error: {e}", exc_info=True)
            if self._enable_observability:
                log_run_metrics(self._logger, request_id, None, latency_ms, status="fail", error=error_msg)
            return {
                "request_id": request_id,
                "output": "An error occurred while processing your request.",
                "tool_calls": [],
                "metadata": {"error": error_msg},
            }

        finally:
            clear_request_context()

    def stream_request(self, payload: Dict):
        """
        Stream a response token-by-token via Agno's streaming mode.

        Guardrails fire automatically at the start of the run via pre_hooks.
        InputCheckError is caught and re-raised as a string sentinel.

        Yields:
            str: Individual content chunks.
        """
        input_text = payload.get("input", "")
        session_id = payload.get("session_id", "default")

        input_text = self.before_llm(input_text, {})

        try:
            for chunk in self.agno_agent.run(input_text, stream=True, session_id=session_id):
                if chunk.content:
                    yield chunk.content
        except InputCheckError as e:
            yield f"[BLOCKED: {e}]"
