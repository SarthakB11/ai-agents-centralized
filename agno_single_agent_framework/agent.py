"""
Agent Definition — Customize your Agno-powered agent here.

This is the only file you need to modify for most use cases.

Skills are auto-loaded from the skills/ directory:
  Add a skill:    drop a YAML file in skills/ with enabled: true
  Remove a skill: delete the YAML file or set enabled: false
  Available:      calculator, duckduckgo, hackernews, wikipedia,
                  web_search, http_request, email_sender, file_parser,
                  database_lookup, yfinance, arxiv, newspaper, exa,
                  tavily, github, resend, python_exec, shell
"""

from agno_single_agent_framework import AgnoBaseAgent
from typing import Optional, Dict, List, Any


class MyAgent(AgnoBaseAgent):
    """
    Your custom Agno-powered agent.

    Agno handles:
      ✅ Tool selection & execution automatically
      ✅ Multi-turn memory via SqliteDb
      ✅ Multi-LLM provider switching
      ✅ Streaming responses

    You can:
      ✅ Add extra toolkits in setup()
      ✅ Pre-process input in before_llm()
      ✅ Post-process output in after_llm()
      ✅ Configure agent personality via prompts/system_prompt.txt
    """

    def setup(self):
        """
        Called after the Agno agent is initialized.

        Use this to:
          - Add custom toolkits not covered by skills/
          - Initialize agent-specific services
          - Log startup information
        """
        self._logger.info(f"Agent '{self.name}' custom setup complete")

        # Example: Add a custom toolkit programmatically
        # from my_tools import MyCustomToolkit
        # self.add_toolkit(MyCustomToolkit())

    def before_llm(self, input_text: str, context: Any) -> str:
        """
        Pre-process user input before sending to Agno.

        This hook runs AFTER input guardrails (PII/injection checks)
        but BEFORE the Agno agent processes the message.

        Common uses:
          - Expand abbreviations or domain shorthand
          - Add contextual information from your database
          - Format the input for specific tools
          - Log or audit input for compliance

        Args:
            input_text: Sanitized user input
            context: Additional context (empty dict by default)

        Returns:
            Processed input text to send to Agno
        """
        return input_text

    def after_llm(self, response: str, metadata: Dict) -> str:
        """
        Post-process Agno's output before returning to user.

        This hook runs BEFORE output guardrails (PII redaction).

        Common uses:
          - Format the response (markdown, HTML, etc.)
          - Add disclaimers or branding
          - Filter sensitive content
          - Log or audit output for compliance

        Args:
            response: Raw output from Agno agent
            metadata: Dict with tool_calls, etc.

        Returns:
            Processed output string
        """
        return response
