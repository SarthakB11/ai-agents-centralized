"""
Agno Built-in Toolkits — Ready-made tool integrations from the Agno ecosystem.

Agno ships 100+ pre-built toolkits. This module wraps the most useful ones
and integrates them with our YAML-based skill system.

Each toolkit is wrapped in a try/except so missing optional dependencies
don't crash the whole framework — they just log a warning.

Available Agno toolkits (install extras as needed):
  pip install 'agno[duckduckgo]'     # DuckDuckGo search
  pip install 'agno[newspaper4k]'    # News article fetching
  pip install 'agno[yfinance]'       # Stock market data
  pip install 'agno[shell]'          # Shell command execution
  pip install 'agno[python]'         # Python code execution

Reference: https://docs.agno.com/basics/tools
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_duckduckgo_toolkit():
    """
    DuckDuckGo Web Search Toolkit.

    Privacy-respecting web search with no API key required.
    Returns news and general web search results.

    Install: pip install duckduckgo-search
    """
    try:
        from agno.tools.duckduckgo import DuckDuckGoTools
        toolkit = DuckDuckGoTools()
        logger.info("DuckDuckGoTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("DuckDuckGoTools not available. Install: pip install duckduckgo-search")
        return None
    except Exception as e:
        logger.warning(f"Failed to load DuckDuckGoTools: {e}")
        return None


def get_newspaper_toolkit():
    """
    Newspaper4k Article Fetching Toolkit.

    Fetches and parses news articles from URLs.
    Extracts text, authors, publish date, and summary.

    Install: pip install newspaper4k lxml_html_clean
    """
    try:
        from agno.tools.newspaper4k import Newspaper4kTools
        toolkit = Newspaper4kTools()
        logger.info("Newspaper4kTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("Newspaper4kTools not available. Install: pip install newspaper4k lxml_html_clean")
        return None
    except Exception as e:
        logger.warning(f"Failed to load Newspaper4kTools: {e}")
        return None


def get_yfinance_toolkit():
    """
    Yahoo Finance Stock Market Toolkit.

    Fetches real-time and historical stock prices, company info,
    financial statements, and market data.

    Install: pip install yfinance
    """
    try:
        from agno.tools.yfinance import YFinanceTools
        toolkit = YFinanceTools(
            stock_price=True,
            analyst_recommendations=True,
            company_info=True,
            company_news=True,
        )
        logger.info("YFinanceTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("YFinanceTools not available. Install: pip install yfinance")
        return None
    except Exception as e:
        logger.warning(f"Failed to load YFinanceTools: {e}")
        return None


def get_hackernews_toolkit():
    """
    HackerNews Toolkit.

    Fetches top stories, newest stories, and story details from Hacker News.
    No API key required.
    """
    try:
        from agno.tools.hackernews import HackerNewsTools
        toolkit = HackerNewsTools()
        logger.info("HackerNewsTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("HackerNewsTools not available — likely included in base agno")
        return None
    except Exception as e:
        logger.warning(f"Failed to load HackerNewsTools: {e}")
        return None


def get_python_toolkit():
    """
    Python Code Execution Toolkit.

    Allows the agent to write and execute Python code.
    Runs code in a subprocess for safety.

    WARNING: Enable only in trusted environments.
    """
    try:
        from agno.tools.python import PythonTools
        toolkit = PythonTools()
        logger.info("PythonTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("PythonTools not available in this agno version")
        return None
    except Exception as e:
        logger.warning(f"Failed to load PythonTools: {e}")
        return None


def get_shell_toolkit():
    """
    Shell Command Execution Toolkit.

    Allows the agent to run shell commands.

    WARNING: Enable only in trusted/sandboxed environments.
    """
    try:
        from agno.tools.shell import ShellTools
        toolkit = ShellTools()
        logger.info("ShellTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("ShellTools not available in this agno version")
        return None
    except Exception as e:
        logger.warning(f"Failed to load ShellTools: {e}")
        return None


def get_exa_toolkit():
    """
    Exa AI Search Toolkit.

    High-quality semantic search powered by Exa AI.
    Better than traditional web search for research tasks.

    Install: pip install exa-py
    Requires: EXA_API_KEY environment variable
    """
    try:
        from agno.tools.exa import ExaTools
        toolkit = ExaTools()
        logger.info("ExaTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("ExaTools not available. Install: pip install exa-py and set EXA_API_KEY")
        return None
    except Exception as e:
        logger.warning(f"Failed to load ExaTools: {e}")
        return None


def get_tavily_toolkit():
    """
    Tavily Search Toolkit.

    AI-optimized search designed for LLM agents.
    Returns clean, structured results.

    Install: pip install tavily-python
    Requires: TAVILY_API_KEY environment variable
    """
    try:
        from agno.tools.tavily import TavilyTools
        toolkit = TavilyTools()
        logger.info("TavilyTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("TavilyTools not available. Install: pip install tavily-python and set TAVILY_API_KEY")
        return None
    except Exception as e:
        logger.warning(f"Failed to load TavilyTools: {e}")
        return None


def get_resend_toolkit():
    """
    Resend Email Toolkit.

    Modern email sending via Resend API. Alternative to SMTP.

    Install: pip install resend
    Requires: RESEND_API_KEY environment variable
    """
    try:
        from agno.tools.resend import ResendTools
        import os
        toolkit = ResendTools(from_email=os.getenv("RESEND_FROM_EMAIL", "noreply@example.com"))
        logger.info("ResendTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("ResendTools not available. Install: pip install resend and set RESEND_API_KEY")
        return None
    except Exception as e:
        logger.warning(f"Failed to load ResendTools: {e}")
        return None


def get_arxiv_toolkit():
    """
    ArXiv Academic Paper Search Toolkit.

    Search and fetch academic papers from arXiv.
    Great for research and scientific agents.

    Install: pip install arxiv
    """
    try:
        from agno.tools.arxiv import ArxivTools
        toolkit = ArxivTools()
        logger.info("ArxivTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("ArxivTools not available. Install: pip install arxiv")
        return None
    except Exception as e:
        logger.warning(f"Failed to load ArxivTools: {e}")
        return None


def get_wikipedia_toolkit():
    """
    Wikipedia Toolkit.

    Search and retrieve Wikipedia articles.
    No API key required.

    Install: pip install wikipedia
    """
    try:
        from agno.tools.wikipedia import WikipediaTools
        toolkit = WikipediaTools()
        logger.info("WikipediaTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("WikipediaTools not available. Install: pip install wikipedia")
        return None
    except Exception as e:
        logger.warning(f"Failed to load WikipediaTools: {e}")
        return None


def get_github_toolkit():
    """
    GitHub Toolkit.

    Interact with GitHub repositories: search repos, read files,
    list issues, PRs, and more.

    Requires: GITHUB_TOKEN environment variable
    """
    try:
        from agno.tools.github import GithubTools
        toolkit = GithubTools()
        logger.info("GithubTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("GithubTools not available. Set GITHUB_TOKEN env var.")
        return None
    except Exception as e:
        logger.warning(f"Failed to load GithubTools: {e}")
        return None


def get_spider_toolkit():
    """
    Spider Web Crawler Toolkit.

    High-performance web crawler and scraper. Crawls entire websites,
    extracts clean text content, and returns structured data.

    Install: pip install spider-client
    Requires: SPIDER_API_KEY environment variable
    """
    try:
        from agno.tools.spider import SpiderTools
        toolkit = SpiderTools()
        logger.info("SpiderTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("SpiderTools not available. Install: pip install spider-client and set SPIDER_API_KEY")
        return None
    except Exception as e:
        logger.warning(f"Failed to load SpiderTools: {e}")
        return None


def get_firecrawl_toolkit():
    """
    Firecrawl Web Scraping Toolkit.

    Scrapes web pages and converts them to clean, LLM-ready markdown.
    Handles JavaScript-rendered pages and complex sites.

    Install: pip install firecrawl-py
    Requires: FIRECRAWL_API_KEY environment variable
    """
    try:
        from agno.tools.firecrawl import FirecrawlTools
        toolkit = FirecrawlTools()
        logger.info("FirecrawlTools loaded successfully")
        return toolkit
    except ImportError:
        logger.warning("FirecrawlTools not available. Install: pip install firecrawl-py and set FIRECRAWL_API_KEY")
        return None
    except Exception as e:
        logger.warning(f"Failed to load FirecrawlTools: {e}")
        return None


# ─── Registry: maps YAML skill names to factory functions ───────────────────
# These can be referenced in skills/*.yaml files by their "name" field.

AGNO_BUILTIN_REGISTRY = {
    "duckduckgo":  get_duckduckgo_toolkit,
    "newspaper":   get_newspaper_toolkit,
    "yfinance":    get_yfinance_toolkit,
    "hackernews":  get_hackernews_toolkit,
    "python_exec": get_python_toolkit,
    "shell":       get_shell_toolkit,
    "exa":         get_exa_toolkit,
    "tavily":      get_tavily_toolkit,
    "resend":      get_resend_toolkit,
    "arxiv":       get_arxiv_toolkit,
    "wikipedia":   get_wikipedia_toolkit,
    "github":      get_github_toolkit,
    "spider":      get_spider_toolkit,
    "firecrawl":   get_firecrawl_toolkit,
}


def load_agno_toolkit(name: str):
    """
    Load an Agno built-in toolkit by its registry name.

    Args:
        name: The toolkit name (as used in skills/*.yaml)

    Returns:
        An Agno Toolkit instance, or None if unavailable.
    """
    factory = AGNO_BUILTIN_REGISTRY.get(name)
    if factory is None:
        logger.warning(f"Unknown Agno built-in toolkit: '{name}'. "
                       f"Available: {list(AGNO_BUILTIN_REGISTRY.keys())}")
        return None
    return factory()
