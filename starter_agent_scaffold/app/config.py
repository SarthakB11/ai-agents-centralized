
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    AGENT_NAME: str = "starter-agent"
    VERSION: str = "1.0.0"
    OPENAI_API_KEY: str
    REDIS_URL: str = "redis://localhost:6379"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
