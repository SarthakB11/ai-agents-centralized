
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.agent import Agent
from app.config import settings

app = FastAPI(title=settings.AGENT_NAME, version=settings.VERSION)

class AgentRequest(BaseModel):
    input: str
    request_id: str = "req_123"
    session_id: str = "sess_001"

class AgentResponse(BaseModel):
    request_id: str
    output: str
    tool_calls: list = []
    metadata: dict = {}

agent_instance = Agent()

@app.get("/health")
def health_check():
    return {"status": "ok", "version": settings.VERSION}

@app.post("/agent/chat", response_model=AgentResponse)
def handle_chat(request: AgentRequest):
    try:
        response = agent_instance.handle_request(request.dict())
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
