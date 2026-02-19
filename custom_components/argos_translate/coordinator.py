"""DataUpdateCoordinator for Argos Translate."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_API_KEY, CONF_HOST, CONF_PORT, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ArgosTranslateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage Argos Translate / LibreTranslate API."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self.config_entry = entry
        self._host = entry.data[CONF_HOST]
        self._port = entry.data[CONF_PORT]
        self._api_key = entry.data.get(CONF_API_KEY, "")
        self._base_url = f"http://{self._host}:{self._port}"

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch available languages from the translation server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self._base_url}/languages",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    if resp.status == 200:
                        languages = await resp.json()
                        return {
                            "languages": languages,
                            "language_count": len(languages),
                            "status": "online",
                        }
                    return {"languages": [], "language_count": 0, "status": "error"}
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Argos Translate: {err}") from err

    async def async_translate(self, text: str, source: str, target: str) -> str:
        """Translate text using the API."""
        try:
            payload: dict[str, Any] = {
                "q": text,
                "source": source,
                "target": target,
                "format": "text",
            }
            if self._api_key:
                payload["api_key"] = self._api_key

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self._base_url}/translate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("translatedText", "")
                    _LOGGER.error("Translation failed with status %s", resp.status)
                    return f"[Translation error: HTTP {resp.status}]"
        except Exception as err:
            _LOGGER.error("Translation request failed: %s", err)
            return f"[Translation error: {err}]"
