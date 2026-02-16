"""
Skill Loader — Auto-discover and register skills from YAML files.

Skills are YAML files in a `skills/` directory. Each file defines a
skill (tool, integration, MCP, function) that the agent can use.

Adding a skill   = drop a YAML file in skills/
Removing a skill = delete the YAML file

Skill YAML format:
    name: calculator
    type: tool                  # tool | integration | mcp | function
    enabled: true
    module: ai_agent_sdk.tools.calculator
    description: Arithmetic operations
    config:
      precision: 2
"""

import os
import glob
import importlib
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

import yaml

logger = logging.getLogger(__name__)


@dataclass
class Skill:
    """Represents a loaded skill."""
    name: str
    type: str                       # tool | integration | mcp | function
    module_path: str
    description: str = ""
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    module: Any = None              # The loaded Python module/object
    source_file: str = ""           # Path to the YAML that defined it


class SkillLoader:
    """
    Discovers, validates, and loads skills from YAML files.

    Usage:
        loader = SkillLoader("skills/")
        loader.load_all()

        for skill in loader.get_tools():
            agent.register_tool(skill.name, skill.module)
    """

    VALID_TYPES = {"tool", "integration", "mcp", "function"}

    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = skills_dir
        self.skills: Dict[str, Skill] = {}
        self._errors: List[str] = []

    # --- Discovery & Loading ---

    def load_all(self) -> "SkillLoader":
        """
        Scan the skills directory, parse all YAML files, and load modules.
        Returns self for chaining.
        """
        if not os.path.isdir(self.skills_dir):
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return self

        yaml_files = glob.glob(os.path.join(self.skills_dir, "*.yaml"))
        yaml_files += glob.glob(os.path.join(self.skills_dir, "*.yml"))

        logger.info(f"📂 Scanning {self.skills_dir}/ — found {len(yaml_files)} skill file(s)")

        for filepath in sorted(yaml_files):
            self._load_skill_file(filepath)

        loaded = [s.name for s in self.skills.values() if s.enabled]
        disabled = [s.name for s in self.skills.values() if not s.enabled]

        logger.info(f"✅ Skills loaded: {loaded}")
        if disabled:
            logger.info(f"⏸️  Skills disabled: {disabled}")
        if self._errors:
            for err in self._errors:
                logger.error(f"❌ {err}")

        return self

    def _load_skill_file(self, filepath: str):
        """Parse a single YAML skill file and load its module."""
        filename = os.path.basename(filepath)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not data or not isinstance(data, dict):
                self._errors.append(f"{filename}: Empty or invalid YAML")
                return

            # Validate required fields
            name = data.get("name")
            skill_type = data.get("type")
            module_path = data.get("module")

            if not name:
                self._errors.append(f"{filename}: Missing 'name' field")
                return
            if not skill_type:
                self._errors.append(f"{filename}: Missing 'type' field")
                return
            if skill_type not in self.VALID_TYPES:
                self._errors.append(f"{filename}: Invalid type '{skill_type}'. Must be one of {self.VALID_TYPES}")
                return
            if not module_path:
                self._errors.append(f"{filename}: Missing 'module' field")
                return

            skill = Skill(
                name=name,
                type=skill_type,
                module_path=module_path,
                description=data.get("description", ""),
                enabled=data.get("enabled", True),
                config=data.get("config", {}),
                source_file=filepath,
            )

            # Only load module if enabled
            if skill.enabled:
                skill.module = self._import_module(module_path, filename)
                if skill.module is None:
                    return  # Error already logged

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
        """Get all skills, optionally filtered to enabled only."""
        skills = list(self.skills.values())
        if enabled_only:
            skills = [s for s in skills if s.enabled]
        return skills

    def get_by_type(self, skill_type: str, enabled_only: bool = True) -> List[Skill]:
        """Get skills by type (tool, integration, mcp, function)."""
        return [s for s in self.get_all(enabled_only) if s.type == skill_type]

    def get_tools(self) -> List[Skill]:
        """Get all enabled tool skills."""
        return self.get_by_type("tool")

    def get_integrations(self) -> List[Skill]:
        """Get all enabled integration skills."""
        return self.get_by_type("integration")

    def get_mcps(self) -> List[Skill]:
        """Get all enabled MCP skills."""
        return self.get_by_type("mcp")

    def get_functions(self) -> List[Skill]:
        """Get all enabled function skills."""
        return self.get_by_type("function")

    def get(self, name: str) -> Optional[Skill]:
        """Get a specific skill by name."""
        return self.skills.get(name)

    def has(self, name: str) -> bool:
        """Check if a skill is loaded and enabled."""
        skill = self.skills.get(name)
        return skill is not None and skill.enabled

    def get_errors(self) -> List[str]:
        """Get list of loading errors."""
        return self._errors

    # --- Hot Reload ---

    def reload(self) -> "SkillLoader":
        """Re-scan the skills directory. New files are picked up, deleted files are dropped."""
        self.skills.clear()
        self._errors.clear()
        return self.load_all()

    # --- Summary ---

    def summary(self) -> Dict:
        """Get a summary of loaded skills."""
        return {
            "total": len(self.skills),
            "enabled": len([s for s in self.skills.values() if s.enabled]),
            "disabled": len([s for s in self.skills.values() if not s.enabled]),
            "by_type": {
                t: len(self.get_by_type(t)) for t in self.VALID_TYPES
            },
            "errors": len(self._errors),
            "skills": [
                {"name": s.name, "type": s.type, "enabled": s.enabled, "module": s.module_path}
                for s in self.skills.values()
            ],
        }
