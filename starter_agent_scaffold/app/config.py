"""
Config loader — reads environment and agent_spec.yaml.
"""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables / .env file.
    Only declare secrets and runtime config here — never hardcode values.
    """

    # Agent identity
    AGENT_NAME: str = "starter-agent"
    VERSION: str = "1.0.0"
    LOG_LEVEL: str = "INFO"

    # LLM Provider keys (set whichever provider you use)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None

    # Memory store
    REDIS_URL: str = "redis://localhost:6379"

    # Integrations
    SLACK_BOT_TOKEN: Optional[str] = None
    SLACK_SIGNING_SECRET: Optional[str] = None
    WHATSAPP_API_TOKEN: Optional[str] = None
    WHATSAPP_VERIFY_TOKEN: Optional[str] = None
    WEBHOOK_SECRET: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
