"""DataUpdateCoordinator for Argos Translate (LibreTranslate)."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ArgosTranslateApiClient, CannotConnectError
from .const import CONF_USE_SSL, DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class ArgosCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator to manage data fetching from LibreTranslate."""

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
        session = async_get_clientsession(hass)
        self.client = ArgosTranslateApiClient(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            api_key=entry.data.get(CONF_API_KEY, ""),
            session=session,
            use_ssl=entry.data.get(CONF_USE_SSL, False),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch language data from LibreTranslate."""
        try:
            languages = await self.client.async_get_languages()
        except CannotConnectError as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

        return {
            "languages": languages,
            "language_count": len(languages),
        }

    async def async_translate(
        self, text: str, source: str, target: str
    ) -> str:
        """Translate text via the API client.

        Convenience method used by the translate service (Phase 2).
        """
        return await self.client.async_translate(text, source, target)
