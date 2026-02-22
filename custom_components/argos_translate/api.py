"""API client for Argos Translate (LibreTranslate)."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp

from .const import DEFAULT_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class CannotConnectError(Exception):
    """Raised when a connection or timeout error occurs."""


class InvalidAuthError(Exception):
    """Raised when the API returns a 401 or 403 response."""


class TranslationError(Exception):
    """Raised when the server returns a semantic error (HTTP 4xx, excluding 401/403).

    Distinct from CannotConnectError: the server IS reachable and understood the
    request but cannot fulfill it (e.g., translation pair not available, HTTP 400).
    """


class ArgosTranslateApiClient:
    """API client for LibreTranslate server."""

    def __init__(
        self,
        host: str,
        port: int,
        api_key: str,
        session: aiohttp.ClientSession,
        use_ssl: bool = False,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        """Initialize the API client."""
        scheme = "https" if use_ssl else "http"
        self._base_url = f"{scheme}://{host}:{port}"
        self._api_key = api_key
        self._session = session
        self._timeout = aiohttp.ClientTimeout(total=timeout)

    async def _request(
        self, method: str, endpoint: str, **kwargs: Any
    ) -> Any:
        """Make a request to the LibreTranslate API."""
        url = f"{self._base_url}{endpoint}"
        try:
            response = await self._session.request(
                method,
                url,
                timeout=self._timeout,
                **kwargs,
            )
        except aiohttp.ClientConnectionError as err:
            raise CannotConnectError(f"Connection error: {err}") from err
        except aiohttp.ClientError as err:
            raise CannotConnectError(f"Client error: {err}") from err
        except asyncio.TimeoutError as err:
            raise CannotConnectError("Request timed out") from err

        if response.status in (401, 403):
            raise InvalidAuthError(
                f"Authentication failed (HTTP {response.status})"
            )

        if response.status >= 400:
            raise TranslationError(
                f"Server returned HTTP {response.status}: {response.reason}"
            )

        return await response.json()

    async def async_test_connection(self) -> bool:
        """Test connection by fetching languages from LibreTranslate.

        Returns True if server is reachable and has language models installed.
        Raises CannotConnectError if unreachable or no languages installed.
        """
        languages = await self._request("GET", "/languages")
        if not languages:
            raise CannotConnectError("No languages installed on server")
        return True

    async def async_get_languages(self) -> list[dict[str, Any]]:
        """Fetch available languages from LibreTranslate.

        Returns list of language dicts: [{code, name, targets}, ...]
        """
        return await self._request("GET", "/languages")

    async def async_translate(
        self, text: str, source: str, target: str
    ) -> dict[str, Any]:
        """Translate text using LibreTranslate.

        API key is sent in the POST body (not as a header).
        Returns the full response dict from LibreTranslate, which includes
        'translatedText' and optionally 'detectedLanguage' when source is 'auto'.
        """
        payload: dict[str, str] = {
            "q": text,
            "source": source,
            "target": target,
        }
        if self._api_key:
            payload["api_key"] = self._api_key
        return await self._request("POST", "/translate", json=payload)

    async def async_detect_languages(self, text: str) -> list[dict[str, Any]]:
        """Detect language candidates for text using LibreTranslate /detect endpoint.

        Returns list of candidates: [{"language": "fr", "confidence": 91.0}, ...]
        sorted by descending confidence.
        """
        payload: dict[str, str] = {"q": text}
        if self._api_key:
            payload["api_key"] = self._api_key
        return await self._request("POST", "/detect", json=payload)
