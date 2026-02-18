"""
HTTP Request Toolkit — Make external API calls using Agno framework.

Useful for agents that need to fetch data from REST APIs,
check service status, or interact with third-party services.
"""

import logging
from agno.tools import Toolkit

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class HTTPRequestToolkit(Toolkit):
    """Toolkit for making HTTP requests to external APIs."""

    def __init__(self):
        super().__init__(name="http_request")
        self.register(self.get)
        self.register(self.post)
        self.register(self.put)
        self.register(self.request)

    def request(self, url: str, method: str = "GET", headers: dict = None, body: dict = None, timeout: int = 10) -> dict:
        """
        Make an HTTP request to an external API.

        Args:
            url: The target URL
            method: HTTP method (GET, POST, PUT, PATCH)
            headers: Optional request headers dictionary
            body: Optional JSON body for POST/PUT/PATCH requests
            timeout: Timeout in seconds (default 10)

        Returns:
            A dictionary with status_code, headers, and response body
        """
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

    def get(self, url: str, headers: dict = None, timeout: int = 10) -> dict:
        """
        Make an HTTP GET request.

        Args:
            url: The target URL
            headers: Optional request headers
            timeout: Timeout in seconds (default 10)

        Returns:
            A dictionary with status_code, headers, and response body
        """
        return self.request(url, method="GET", headers=headers, timeout=timeout)

    def post(self, url: str, body: dict = None, headers: dict = None, timeout: int = 10) -> dict:
        """
        Make an HTTP POST request with JSON body.

        Args:
            url: The target URL
            body: JSON body to send
            headers: Optional request headers
            timeout: Timeout in seconds (default 10)

        Returns:
            A dictionary with status_code, headers, and response body
        """
        return self.request(url, method="POST", headers=headers, body=body, timeout=timeout)

    def put(self, url: str, body: dict = None, headers: dict = None, timeout: int = 10) -> dict:
        """
        Make an HTTP PUT request with JSON body.

        Args:
            url: The target URL
            body: JSON body to send
            headers: Optional request headers
            timeout: Timeout in seconds (default 10)

        Returns:
            A dictionary with status_code, headers, and response body
        """
        return self.request(url, method="PUT", headers=headers, body=body, timeout=timeout)


# Backward compatibility
DESCRIPTION = "Make HTTP GET/POST requests to external APIs. Returns status code, headers, and body."
PARAMETERS = {
    "url": {"type": "string", "description": "Target URL"},
    "method": {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH"], "default": "GET"},
    "headers": {"type": "object", "description": "Request headers (optional)"},
    "body": {"type": "object", "description": "JSON body for POST/PUT (optional)"},
    "timeout": {"type": "integer", "description": "Timeout in seconds", "default": 10},
}


def run(url: str, method: str = "GET", headers: dict = None, body: dict = None, timeout: int = 10) -> dict:
    """Make an HTTP request and return the response (legacy interface)."""
    toolkit = HTTPRequestToolkit()
    return toolkit.request(url, method, headers, body, timeout)
