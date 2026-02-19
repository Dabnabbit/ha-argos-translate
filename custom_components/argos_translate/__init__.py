"""The Argos Translate integration - local translation for Home Assistant."""

from __future__ import annotations

import logging
from pathlib import Path

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse

from .const import (
    ATTR_SOURCE,
    ATTR_TARGET,
    ATTR_TEXT,
    DOMAIN,
    FRONTEND_SCRIPT_URL,
    SERVICE_TRANSLATE,
)
from .coordinator import ArgosTranslateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]

TRANSLATE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TEXT): str,
        vol.Required(ATTR_SOURCE): str,
        vol.Required(ATTR_TARGET): str,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Argos Translate from a config entry."""
    coordinator = ArgosTranslateCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register translate service
    async def handle_translate(call: ServiceCall) -> ServiceResponse:
        """Handle the translate service call."""
        text = call.data[ATTR_TEXT]
        source = call.data[ATTR_SOURCE]
        target = call.data[ATTR_TARGET]

        result = await coordinator.async_translate(text, source, target)
        return {"translated_text": result}

    hass.services.async_register(
        DOMAIN,
        SERVICE_TRANSLATE,
        handle_translate,
        schema=TRANSLATE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )

    await _async_register_frontend(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        # Only remove service if no more entries
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, SERVICE_TRANSLATE)
    return unload_ok


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Register the frontend card resources."""
    frontend_path = Path(__file__).parent / "frontend"
    hass.http.register_static_path(
        FRONTEND_SCRIPT_URL,
        str(frontend_path / f"{DOMAIN}-card.js"),
        cache_headers=True,
    )
    _LOGGER.debug("Registered frontend card at %s", FRONTEND_SCRIPT_URL)
