"""
Web Search Toolkit — Search the web using SerpAPI or Tavily via Agno framework.

Setup:
  pip install requests
  Set SERP_API_KEY or TAVILY_API_KEY in .env
"""

import os
import logging
from agno.tools import Toolkit

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class WebSearchToolkit(Toolkit):
    """Toolkit for searching the web using Tavily or SerpAPI."""

    def __init__(self):
        super().__init__(name="web_search")
        self.register(self.search)

    def search(self, query: str, num_results: int = 5) -> dict:
        """
        Search the web for real-time information.

        Args:
            query: The search query string
            num_results: Number of results to return (default 5)

        Returns:
            A dictionary containing search results with titles, snippets, and URLs
        """
        if requests is None:
            return {"error": "requests package not installed. Run: pip install requests"}

        # Try Tavily first, then SerpAPI, then fallback
        tavily_key = os.getenv("TAVILY_API_KEY")
        serp_key = os.getenv("SERP_API_KEY")

        if tavily_key:
            return self._search_tavily(query, num_results, tavily_key)
        elif serp_key:
            return self._search_serpapi(query, num_results, serp_key)
        else:
            return {"error": "No search API key configured. Set TAVILY_API_KEY or SERP_API_KEY."}

    def _search_tavily(self, query: str, num_results: int, api_key: str) -> dict:
        """Search using Tavily API."""
        try:
            resp = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "max_results": num_results,
                    "search_depth": "basic",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for r in data.get("results", []):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("content", "")[:200],
                    "url": r.get("url", ""),
                })

            return {"provider": "tavily", "query": query, "results": results}
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return {"error": str(e)}

    def _search_serpapi(self, query: str, num_results: int, api_key: str) -> dict:
        """Search using SerpAPI."""
        try:
            resp = requests.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "api_key": api_key,
                    "num": num_results,
                    "engine": "google",
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for r in data.get("organic_results", []):
                results.append({
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "url": r.get("link", ""),
                })

            return {"provider": "serpapi", "query": query, "results": results}
        except Exception as e:
            logger.error(f"SerpAPI search failed: {e}")
            return {"error": str(e)}


# Backward compatibility
DESCRIPTION = "Search the web for real-time information. Returns top results with titles, snippets, and URLs."
PARAMETERS = {
    "query": {"type": "string", "description": "Search query"},
    "num_results": {"type": "integer", "description": "Number of results (default 5)", "default": 5},
}


def run(query: str, num_results: int = 5) -> dict:
    """Search the web and return structured results (legacy interface)."""
    toolkit = WebSearchToolkit()
    return toolkit.search(query, num_results)


def _search_tavily(query: str, num_results: int, api_key: str) -> dict:
    """Search using Tavily API."""
    try:
        resp = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": num_results,
                "search_depth": "basic",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for r in data.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("content", "")[:200],
                "url": r.get("url", ""),
            })

        return {"provider": "tavily", "query": query, "results": results}
    except Exception as e:
        logger.error(f"Tavily search failed: {e}")
        return {"error": str(e)}


def _search_serpapi(query: str, num_results: int, api_key: str) -> dict:
    """Search using SerpAPI."""
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "api_key": api_key,
                "num": num_results,
                "engine": "google",
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for r in data.get("organic_results", []):
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "url": r.get("link", ""),
            })

        return {"provider": "serpapi", "query": query, "results": results}
    except Exception as e:
        logger.error(f"SerpAPI search failed: {e}")
        return {"error": str(e)}
