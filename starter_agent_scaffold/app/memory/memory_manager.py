
import redis
from app.config import settings
import json

class MemoryManager:
    def __init__(self):
        # In a real app, careful with Redis connection management
        # self.redis = redis.from_url(settings.REDIS_URL)
        self.local_store = {} # Mock for starter

    def load(self, session_id):
        # return self.redis.get(session_id) or []
        return self.local_store.get(session_id, [])

    def save(self, session_id, user_input, agent_output):
        history = self.load(session_id)
        history.append({"user": user_input, "agent": agent_output})
        # self.redis.set(session_id, json.dumps(history))
        self.local_store[session_id] = history
