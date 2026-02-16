from setuptools import setup, find_packages

setup(
    name="ai-agent-sdk",
    version="1.0.0",
    description="Shared SDK for building standardized AI agents",
    author="Platform Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0",
        "pydantic-settings>=2.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "openai": ["openai>=1.0"],
        "gemini": ["google-generativeai>=0.3"],
        "anthropic": ["anthropic>=0.20"],
        "slack": ["slack_bolt>=1.18"],
        "whatsapp": ["httpx>=0.24"],
        "redis": ["redis>=5.0"],
        "metrics": ["prometheus-client>=0.17"],
        "all": [
            "openai>=1.0", "google-generativeai>=0.3", "anthropic>=0.20",
            "slack_bolt>=1.18", "httpx>=0.24", "redis>=5.0",
            "prometheus-client>=0.17",
        ],
    },
)
