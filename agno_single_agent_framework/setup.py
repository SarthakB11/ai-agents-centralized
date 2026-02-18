from setuptools import setup, find_packages

setup(
    name="agno-single-agent-framework",
    version="1.0.0",
    description="Agno-based framework for building standardized single AI agents",
    author="Platform Team",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "pydantic>=2.0",
        "pydantic-settings>=2.0",
        "PyYAML>=6.0",
        "agno>=1.0.0",  # Agno framework — core dependency
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
    ],
    extras_require={
        # LLM providers
        "openai":     ["openai>=1.0"],
        "anthropic":  ["anthropic>=0.20"],
        "gemini":     ["google-generativeai>=0.3"],

        # Agno built-in toolkits
        "duckduckgo": ["duckduckgo-search>=5.0"],
        "newspaper":  ["newspaper4k", "lxml_html_clean"],
        "yfinance":   ["yfinance>=0.2"],
        "arxiv":      ["arxiv>=2.0"],
        "wikipedia":  ["wikipedia>=1.4"],
        "exa":        ["exa-py>=1.0"],
        "tavily":     ["tavily-python>=0.3"],
        "spider":     ["spider-client>=0.0.27"],
        "firecrawl":  ["firecrawl-py>=1.0"],

        # Integrations
        "slack":      ["slack_bolt>=1.18"],
        "whatsapp":   ["httpx>=0.24"],

        # Storage & infrastructure
        "redis":      ["redis>=5.0"],
        "postgres":   ["psycopg2-binary>=2.9"],
        "mysql":      ["pymysql>=1.1"],
        "metrics":    ["prometheus-client>=0.17"],

        # File parsing
        "files":      ["PyPDF2>=3.0", "python-docx>=1.0", "pandas>=2.0", "openpyxl>=3.1"],

        # Everything
        "all": [
            "openai>=1.0", "anthropic>=0.20", "google-generativeai>=0.3",
            "duckduckgo-search>=5.0", "newspaper4k", "lxml_html_clean",
            "yfinance>=0.2", "arxiv>=2.0", "wikipedia>=1.4",
            "exa-py>=1.0", "tavily-python>=0.3",
            "spider-client>=0.0.27", "firecrawl-py>=1.0",
            "slack_bolt>=1.18", "httpx>=0.24",
            "redis>=5.0", "psycopg2-binary>=2.9", "pymysql>=1.1",
            "prometheus-client>=0.17",
            "PyPDF2>=3.0", "python-docx>=1.0", "pandas>=2.0", "openpyxl>=3.1",
        ],
    },
)
