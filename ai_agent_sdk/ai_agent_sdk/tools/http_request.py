"""
HTTP Request Tool — Make external API calls.

Useful for agents that need to fetch data from REST APIs,
check service status, or interact with third-party services.
"""

import logging

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)

DESCRIPTION = "Make HTTP GET/POST requests to external APIs. Returns status code, headers, and body."

PARAMETERS = {
    "url": {"type": "string", "description": "Target URL"},
    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH"], "default": "GET"},
    "headers": {"type": "object", "description": "Request headers (optional)"},
    "body": {"type": "object", "description": "JSON body for POST/PUT (optional)"},
    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 10},
}


def run(url: str, method: str = "GET", headers: dict = None, body: dict = None, timeout: int = 10) -> dict:
    """Make an HTTP request and return the response."""
    if requests is None:
        return {"error": "requests package not installed. Run: pip install requests"}

    try:
        resp = requests.request(
            method=method.upper(),
            url=url,
            headers=headers or {},
            json=body if method.upper() in ("POST", "PUT", "PATCH") else None,
            timeout=timeout,
        )

        # Try to parse as JSON, fallback to text
        try:
            response_body = resp.json()
        except ValueError:
            response_body = resp.text[:2000]  # Limit text response size

        return {
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": response_body,
            "url": url,
            "method": method.upper(),
        }
    except requests.exceptions.Timeout:
        return {"error": f"Request timed out after {timeout}s", "url": url}
    except requests.exceptions.ConnectionError:
        return {"error": f"Connection failed to {url}"}
    except Exception as e:
        logger.error(f"HTTP request failed: {e}")
        return {"error": str(e)}
