
from app.services.llm_client import LLMClient
from app.memory.memory_manager import MemoryManager
from app.tools.example_tool import calculator
import json

class Agent:
    def __init__(self):
        self.llm = LLMClient()
        self.memory = MemoryManager()
        # In a real app, load tools dynamically based on spec
        self.tools = {
            "calculator": calculator
        }

    def handle_request(self, payload):
        request_id = payload.get("request_id", "unknown")
        user_input = payload.get("input")
        session_id = payload.get("session_id", "default")
        
        # 1. Load Context
        context = self.memory.load(session_id)
        
        # 2. Heuristic Routing / Tool Selection (Simplified)
        # Real implementation would use LLM to decide tool
        tool_result = None
        if "calculate" in user_input.lower():
             # extremely naive parsing for demo
             try:
                 # "calculate add 5 3"
                 parts = user_input.split()
                 op = parts[1]
                 a = float(parts[2])
                 b = float(parts[3])
                 tool_result = self.tools["calculator"](op, a, b)
             except:
                 tool_result = "Invalid calculation format"

        # 3. Generate Response
        response_data = self.llm.generate(
            input_text=user_input,
            context=context,
            tool_output=tool_result
        )

        # 4. Save Memory
        self.memory.save(session_id, user_input, response_data["output"])

        return {
            "request_id": request_id,
            "output": response_data["output"],
            "tool_calls": ["calculator"] if tool_result else [],
            "metadata": {
                "tokens": response_data.get("tokens_used", 0)
            }
        }
