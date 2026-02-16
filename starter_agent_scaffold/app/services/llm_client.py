
import openai
from app.config import settings

class LLMClient:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.model = "gpt-4o-mini" # Should load from spec really

    def generate(self, input_text, context, tool_output=None):
        messages = [
            {"role": "system", "content": "You are a helpful assistant."}, # Should load from prompt file
            {"role": "user", "content": f"Context: {context}\nInput: {input_text}"}
        ]
        
        if tool_output:
             messages.append({"role": "function", "name": "tool", "content": str(tool_output)})

        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            return {
                "output": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens
            }
        except Exception as e:
             # Log error here following observation spec
             return {"output": "Error processing request", "error": str(e)}

