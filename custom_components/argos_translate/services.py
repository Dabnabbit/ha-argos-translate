"""Service handlers for the Argos Translate integration."""

from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError
from homeassistant.helpers import config_validation as cv

from .api import CannotConnectError
from .const import ATTR_SOURCE, ATTR_TARGET, ATTR_TEXT, DOMAIN, SERVICE_TRANSLATE

_LOGGER = logging.getLogger(__name__)

SERVICE_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_TEXT): cv.string,
        vol.Required(ATTR_SOURCE): cv.string,
        vol.Required(ATTR_TARGET): cv.string,
    }
)


@callback
def async_register_services(hass: HomeAssistant) -> None:
    """Register integration service actions for Argos Translate."""

    async def _async_handle_translate(call: ServiceCall) -> ServiceResponse:
        """Handle the translate service call."""
        text: str = call.data[ATTR_TEXT]
        source: str = call.data[ATTR_SOURCE]
        target: str = call.data[ATTR_TARGET]

        # Look up coordinator from first config entry
        entries = hass.config_entries.async_entries(DOMAIN)
        if not entries:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_config_entry",
            )

        entry = entries[0]
        coordinator = entry.runtime_data.coordinator

        # Validate language pair against coordinator data
        languages = coordinator.data.get("languages", []) if coordinator.data else []
        source_lang = None
        for lang in languages:
            if lang["code"] == source:
                source_lang = lang
                break

        if source_lang is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_source",
                translation_placeholders={"source": source},
            )

        if target not in source_lang.get("targets", []):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_target",
                translation_placeholders={"source": source, "target": target},
            )

        # Call translation API
        try:
            translated_text = await coordinator.async_translate(text, source, target)
        except CannotConnectError as err:
            raise HomeAssistantError(
                f"Translation failed: {err}"
            ) from err

        return {"translated_text": translated_text}

    hass.services.async_register(
        DOMAIN,
        SERVICE_TRANSLATE,
        _async_handle_translate,
        schema=SERVICE_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
