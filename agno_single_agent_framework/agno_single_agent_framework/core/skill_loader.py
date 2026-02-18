"""
Skill Loader — Auto-discover and register skills from YAML files.

Built-in skills are shipped with the SDK. You don't need to write Python code.
Just drop a YAML file in skills/ and the SDK does the rest.

Adding a skill   = drop a YAML file in skills/
Removing a skill = delete the YAML file
Disable a skill  = set `enabled: false`

Minimal YAML for a built-in skill:
    name: calculator
    enabled: true

Full YAML for a custom skill:
    name: my_custom_tool
    type: tool
    module: my_app.tools.custom    # Only needed for custom skills
    enabled: true
    description: Does something amazing
    config:
      key: value
"""

import os
import glob
import importlib
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import yaml

logger = logging.getLogger(__name__)

# Skills directory shipped inside the package — resolved relative to this file
# so it works regardless of the caller's working directory.
_PACKAGE_SKILLS_DIR = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "skills")
)


# ──────────────────────────────────────────────────────────────
# Built-in Skill Registry
# The SDK ships these. Users just reference them by name in YAML.
# No Python code needed.
# ──────────────────────────────────────────────────────────────

BUILTIN_SKILLS: Dict[str, Dict[str, str]] = {
    # ── Custom Toolkits (our full implementations) ───────────────────────────
    "calculator":       {"type": "tool",        "module": "agno_single_agent_framework.tools.calculator",       "description": "Arithmetic operations — add, subtract, multiply, divide"},
    "web_search":       {"type": "tool",        "module": "agno_single_agent_framework.tools.web_search",       "description": "Search the web via Tavily or SerpAPI"},
    "database_lookup":  {"type": "tool",        "module": "agno_single_agent_framework.tools.database_lookup",  "description": "Read-only SQL queries on PostgreSQL/MySQL"},
    "http_request":     {"type": "tool",        "module": "agno_single_agent_framework.tools.http_request",     "description": "Make HTTP GET/POST/PUT requests to APIs"},
    "email_sender":     {"type": "tool",        "module": "agno_single_agent_framework.tools.email_sender",     "description": "Send emails via SMTP"},
    "file_parser":      {"type": "tool",        "module": "agno_single_agent_framework.tools.file_parser",      "description": "Extract text from PDF, DOCX, CSV, Excel, TXT"},

    # ── Agno Built-in Toolkits (ready-made from Agno ecosystem) ─────────────
    "duckduckgo":       {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "DuckDuckGo web search — no API key required"},
    "hackernews":       {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Hacker News top stories, newest posts, and details"},
    "wikipedia":        {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Search and retrieve Wikipedia articles"},
    "yfinance":         {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Yahoo Finance — stock prices, company info, analyst recommendations"},
    "arxiv":            {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "ArXiv academic paper search"},
    "newspaper":        {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Fetch and parse news articles from URLs"},
    "exa":              {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Exa AI semantic search — requires EXA_API_KEY"},
    "tavily":           {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Tavily AI-optimized search — requires TAVILY_API_KEY"},
    "github":           {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "GitHub repo search, files, issues — requires GITHUB_TOKEN"},
    "resend":           {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Resend email API — requires RESEND_API_KEY"},
    "python_exec":      {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Execute Python code — use only in trusted environments"},
    "shell":            {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Execute shell commands — use only in trusted environments"},
    "spider":           {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Spider web crawler — crawl entire sites, extract content — requires SPIDER_API_KEY"},
    "firecrawl":        {"type": "tool",        "module": "agno_single_agent_framework.tools.agno_builtin",     "description": "Firecrawl web scraper — LLM-ready markdown output — requires FIRECRAWL_API_KEY"},

    # ── Integrations (FastAPI routers) ───────────────────────────────────────
    "webhook":          {"type": "integration", "module": "agno_single_agent_framework.integrations.webhook",   "description": "Generic inbound webhook with HMAC verification"},
    "whatsapp":         {"type": "integration", "module": "agno_single_agent_framework.integrations.whatsapp",  "description": "WhatsApp Cloud API two-way messaging"},
    "slack":            {"type": "integration", "module": "agno_single_agent_framework.integrations.slack",     "description": "Slack bot via Socket Mode"},
}


@dataclass
class Skill:
    """Represents a loaded skill."""
    name: str
    type: str                       # tool | integration | mcp | function
    module_path: str
    description: str = ""
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    module: Any = None
    source_file: str = ""
    is_builtin: bool = False


class SkillLoader:
    """
    Discovers, validates, and loads skills from YAML files.

    Built-in skills only need a name + enabled flag:
        name: calculator
        enabled: true

    Custom skills need a module path:
        name: my_tool
        type: tool
        module: my_app.tools.my_tool
        enabled: true
    """

    VALID_TYPES = {"tool", "integration", "mcp", "function"}

    def __init__(self, skills_dir: str = None):
        self.skills_dir = skills_dir or _PACKAGE_SKILLS_DIR
        self.skills: Dict[str, Skill] = {}
        self._errors: List[str] = []

    # --- Discovery & Loading ---

    def load_all(self) -> "SkillLoader":
        """Scan skills/, parse YAML files, resolve modules, and load."""
        if not os.path.isdir(self.skills_dir):
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return self

        yaml_files = sorted(
            glob.glob(os.path.join(self.skills_dir, "*.yaml"))
            + glob.glob(os.path.join(self.skills_dir, "*.yml"))
        )

        logger.info(f"📂 Scanning {self.skills_dir}/ — found {len(yaml_files)} skill file(s)")

        for filepath in yaml_files:
            self._load_skill_file(filepath)

        loaded = [s.name for s in self.skills.values() if s.enabled]
        disabled = [s.name for s in self.skills.values() if not s.enabled]

        if loaded:
            logger.info(f"✅ Skills loaded: {loaded}")
        if disabled:
            logger.info(f"⏸️  Skills disabled: {disabled}")
        if self._errors:
            for err in self._errors:
                logger.error(f"❌ {err}")

        return self

    def _load_skill_file(self, filepath: str):
        """Parse a single YAML skill file."""
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                self._errors.append(f"{filename}: Empty or invalid YAML")
                return

            name = data.get("name")
            if not name:
                self._errors.append(f"{filename}: Missing 'name' field")
                return

            # ── Resolve from built-in registry ──
            builtin = BUILTIN_SKILLS.get(name)
            is_builtin = builtin is not None

            # Type: explicit > builtin > error
            skill_type = data.get("type") or (builtin["type"] if builtin else None)
            if not skill_type:
                self._errors.append(f"{filename}: Missing 'type' — and '{name}' is not a built-in skill")
                return
            if skill_type not in self.VALID_TYPES:
                self._errors.append(f"{filename}: Invalid type '{skill_type}'. Must be: {self.VALID_TYPES}")
                return

            # Module: explicit > builtin > error
            module_path = data.get("module") or (builtin["module"] if builtin else None)
            if not module_path:
                self._errors.append(
                    f"{filename}: Missing 'module' — and '{name}' is not a built-in skill. "
                    f"Custom skills need: module: my_app.tools.my_tool"
                )
                return

            # Description: explicit > builtin > default
            description = data.get("description") or (builtin.get("description", "") if builtin else "")

            skill = Skill(
                name=name,
                type=skill_type,
                module_path=module_path,
                description=description,
                enabled=data.get("enabled", True),
                config=data.get("config", {}),
                source_file=filepath,
                is_builtin=is_builtin,
            )

            if skill.enabled:
                skill.module = self._import_module(module_path, filename)
                if skill.module is None:
                    return

            self.skills[name] = skill

        except yaml.YAMLError as e:
            self._errors.append(f"{filename}: YAML parse error — {e}")
        except Exception as e:
            self._errors.append(f"{filename}: Unexpected error — {e}")

    def _import_module(self, module_path: str, source: str):
        """Import a Python module by dotted path."""
        try:
            return importlib.import_module(module_path)
        except ImportError as e:
            self._errors.append(f"{source}: Cannot import '{module_path}' — {e}")
            return None
        except Exception as e:
            self._errors.append(f"{source}: Error loading '{module_path}' — {e}")
            return None

    # --- Querying ---

    def get_all(self, enabled_only: bool = True) -> List[Skill]:
        skills = list(self.skills.values())
        return [s for s in skills if s.enabled] if enabled_only else skills

    def get_by_type(self, skill_type: str, enabled_only: bool = True) -> List[Skill]:
        return [s for s in self.get_all(enabled_only) if s.type == skill_type]

    def get_tools(self) -> List[Skill]:
        return self.get_by_type("tool")

    def get_integrations(self) -> List[Skill]:
        return self.get_by_type("integration")

    def get_mcps(self) -> List[Skill]:
        return self.get_by_type("mcp")

    def get_functions(self) -> List[Skill]:
        return self.get_by_type("function")

    def get(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def has(self, name: str) -> bool:
        skill = self.skills.get(name)
        return skill is not None and skill.enabled

    def get_errors(self) -> List[str]:
        return self._errors

    # --- Hot Reload ---

    def reload(self) -> "SkillLoader":
        """Re-scan skills/. New files picked up, deleted files dropped."""
        self.skills.clear()
        self._errors.clear()
        return self.load_all()

    # --- Registry Info ---

    @staticmethod
    def list_available_skills() -> Dict[str, Dict]:
        """List all built-in skills available in the SDK."""
        return {
            name: {"type": info["type"], "description": info.get("description", "")}
            for name, info in BUILTIN_SKILLS.items()
        }

    # --- Summary ---

    def summary(self) -> Dict:
        return {
            "total": len(self.skills),
            "enabled": len([s for s in self.skills.values() if s.enabled]),
            "disabled": len([s for s in self.skills.values() if not s.enabled]),
            "by_type": {t: len(self.get_by_type(t)) for t in self.VALID_TYPES},
            "errors": len(self._errors),
            "skills": [
                {
                    "name": s.name, "type": s.type,
                    "enabled": s.enabled, "builtin": s.is_builtin,
                    "description": s.description,
                }
                for s in self.skills.values()
            ],
        }
