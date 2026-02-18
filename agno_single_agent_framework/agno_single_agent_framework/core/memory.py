"""
Memory Manager — Session state management.

Default: in-memory dict. Override with Redis/DB for production.
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MemoryManager:
    """
    Local in-memory session store. Replace with RedisMemoryManager
    for production persistent memory.
    """

    def __init__(self):
        self._store: Dict[str, List[Dict]] = {}

    def save(self, session_id: str, entry: Dict):
        """Append an entry to session history."""
        if session_id not in self._store:
            self._store[session_id] = []
        self._store[session_id].append(entry)

    def load(self, session_id: str) -> List[Dict]:
        """Load full session history."""
        return self._store.get(session_id, [])

    def clear(self, session_id: str):
        """Clear a session."""
        self._store.pop(session_id, None)

    def get_last_n(self, session_id: str, n: int = 5) -> List[Dict]:
        """Get last N entries from session."""
        return self._store.get(session_id, [])[-n:]


class RedisMemoryManager(MemoryManager):
    """
    Redis-backed memory manager.

    Usage:
        manager = RedisMemoryManager(redis_url="redis://localhost:6379")
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        super().__init__()
        try:
            import redis
            self._redis = redis.from_url(redis_url)
            self._use_redis = True
            logger.info("Redis memory manager initialized")
        except ImportError:
            logger.warning("redis not installed, falling back to in-memory")
            self._use_redis = False

    def save(self, session_id: str, entry: Dict):
        if self._use_redis:
            import json
            self._redis.rpush(f"memory:{session_id}", json.dumps(entry))
        else:
            super().save(session_id, entry)

    def load(self, session_id: str) -> List[Dict]:
        if self._use_redis:
            import json
            raw = self._redis.lrange(f"memory:{session_id}", 0, -1)
            return [json.loads(r) for r in raw]
        return super().load(session_id)

    def clear(self, session_id: str):
        if self._use_redis:
            self._redis.delete(f"memory:{session_id}")
        else:
            super().clear(session_id)
