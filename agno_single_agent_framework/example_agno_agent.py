"""
Example Agno-Powered Agent

This demonstrates the AgnoBaseAgent with:
- Multiple LLM providers
- Automatic tool execution
- Persistent memory
- Enterprise guardrails
- YAML-based skill management
"""

import os
from agno_single_agent_framework import AgnoBaseAgent

# Set API key (choose one)
# os.environ["OPENAI_API_KEY"] = "your-key"
# os.environ["ANTHROPIC_API_KEY"] = "your-key"
# os.environ["GOOGLE_API_KEY"] = "your-key"


class DemoAgent(AgnoBaseAgent):
    """
    Demo agent showcasing Agno integration.

    Skills are auto-loaded from skills/ directory.
    Tools are automatically called by Agno when needed.
    """

    def setup(self):
        """
        Optional: Add custom configuration here.

        You can:
        - Add custom Agno toolkits: self.add_toolkit(MyToolkit())
        - Configure agent behavior
        - Set up additional services
        """
        self._logger.info("Demo agent setup complete")

    def before_llm(self, input_text: str, context: any) -> str:
        """
        Optional: Pre-process input before Agno agent.

        This hook runs after guardrails but before Agno.
        """
        return input_text

    def after_llm(self, response: str, metadata: dict) -> str:
        """
        Optional: Post-process Agno's output.

        This hook runs before output guardrails.
        """
        return response


def main():
    """Run demo agent with example conversations."""

    print("=" * 60)
    print("Agno-Powered Agent Demo")
    print("=" * 60)
    print()

    # Create agent with your preferred LLM provider
    agent = DemoAgent(
        name="demo-agent",
        provider="openai",  # Change to "anthropic" or "gemini"
        model="gpt-4o-mini",  # Or "claude-sonnet-4-5", "gemini-2.0-flash-exp"
        skills_dir="skills",
        enable_guardrails=True,
        enable_observability=True,
        enable_memory=True,
        db_file="demo_agent.db",
        log_level="INFO",
        log_format="pretty",
    )

    print(f"✅ Agent initialized: {agent.name}")
    print(f"📦 Toolkits loaded: {len(agent._toolkits)}")
    print(f"🧠 Memory enabled: {agent.agno_agent.db is not None}")
    print(f"🤖 Model: {agent.agno_agent.model.id}")
    print()

    # Example 1: Simple calculation (Agno calls calculator automatically)
    print("=" * 60)
    print("Example 1: Automatic Tool Execution")
    print("=" * 60)
    print()

    response1 = agent.handle_request({
        "input": "What is 156 multiplied by 23?",
        "session_id": "demo-session-1",
    })

    print(f"User: What is 156 multiplied by 23?")
    print(f"Agent: {response1['output']}")
    print(f"Tools used: {[tc['tool'] for tc in response1['tool_calls']]}")
    print()

    # Example 2: Multi-step reasoning (Agno chains tools)
    print("=" * 60)
    print("Example 2: Multi-Step Reasoning")
    print("=" * 60)
    print()

    response2 = agent.handle_request({
        "input": "Calculate 50 divided by 2, then multiply the result by 10",
        "session_id": "demo-session-1",
    })

    print(f"User: Calculate 50 divided by 2, then multiply the result by 10")
    print(f"Agent: {response2['output']}")
    print(f"Tools used: {[tc['tool'] for tc in response2['tool_calls']]}")
    print()

    # Example 3: Memory persistence (Agno remembers previous conversation)
    print("=" * 60)
    print("Example 3: Memory & Context")
    print("=" * 60)
    print()

    response3a = agent.handle_request({
        "input": "My favorite number is 42",
        "session_id": "demo-session-2",
    })

    print(f"User: My favorite number is 42")
    print(f"Agent: {response3a['output']}")
    print()

    response3b = agent.handle_request({
        "input": "What's my favorite number?",
        "session_id": "demo-session-2",  # Same session = remembers
    })

    print(f"User: What's my favorite number?")
    print(f"Agent: {response3b['output']}")
    print()

    response3c = agent.handle_request({
        "input": "What's my favorite number?",
        "session_id": "demo-session-3",  # Different session = doesn't know
    })

    print(f"User (different session): What's my favorite number?")
    print(f"Agent: {response3c['output']}")
    print()

    # Example 4: Guardrails (PII detection)
    print("=" * 60)
    print("Example 4: Guardrails (PII Detection)")
    print("=" * 60)
    print()

    response4 = agent.handle_request({
        "input": "My email is alice@example.com and my phone is 555-1234",
        "session_id": "demo-session-4",
    })

    print(f"User: My email is alice@example.com and my phone is 555-1234")
    print(f"Agent: {response4['output']}")
    print(f"Note: PII was detected and redacted by guardrails")
    print()

    # Example 5: Metadata
    print("=" * 60)
    print("Example 5: Response Metadata")
    print("=" * 60)
    print()

    print(f"Metadata from last request:")
    for key, value in response4['metadata'].items():
        print(f"  {key}: {value}")
    print()

    print("=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print()
    print("Key Takeaways:")
    print("✅ Agno automatically decides when to call tools")
    print("✅ Memory persists across requests in the same session")
    print("✅ Guardrails protect against PII leakage")
    print("✅ Full observability with request metadata")
    print()
    print("To customize:")
    print("1. Add skills: Drop YAML files in skills/ directory")
    print("2. Switch LLM: Change provider/model parameters")
    print("3. Add hooks: Override setup(), before_llm(), after_llm()")
    print("4. Add toolkits: Create custom Agno Toolkit classes")
    print()


if __name__ == "__main__":
    main()
