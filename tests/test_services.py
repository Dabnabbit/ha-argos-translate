"""Tests for Argos Translate translate service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError, ServiceValidationError

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argos_translate.api import CannotConnectError
from custom_components.argos_translate.const import DOMAIN
from custom_components.argos_translate.services import async_register_services

MOCK_LANGUAGES = [
    {"code": "en", "name": "English", "targets": ["es", "fr"]},
    {"code": "es", "name": "Spanish", "targets": ["en"]},
]


async def _setup_service(
    hass: HomeAssistant, mock_translated: str = "Hola"
) -> tuple[MockConfigEntry, MagicMock]:
    """Set up the translate service with a mocked coordinator."""
    mock_coordinator = MagicMock()
    mock_coordinator.data = {
        "languages": MOCK_LANGUAGES,
        "language_count": len(MOCK_LANGUAGES),
    }
    mock_coordinator.async_translate = AsyncMock(return_value=mock_translated)

    mock_runtime_data = MagicMock()
    mock_runtime_data.coordinator = mock_coordinator

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "localhost",
            CONF_PORT: 5000,
            CONF_API_KEY: "",
        },
    )
    entry.add_to_hass(hass)
    entry.runtime_data = mock_runtime_data

    async_register_services(hass)

    return entry, mock_coordinator


async def test_translate_success(hass: HomeAssistant) -> None:
    """Test successful translation service call."""
    _entry, mock_coordinator = await _setup_service(hass, "Hola")

    result = await hass.services.async_call(
        DOMAIN,
        "translate",
        {"text": "Hello", "source": "en", "target": "es"},
        blocking=True,
        return_response=True,
    )

    assert result == {"translated_text": "Hola"}
    mock_coordinator.async_translate.assert_called_once_with("Hello", "en", "es")


async def test_translate_invalid_source(hass: HomeAssistant) -> None:
    """Test translate with invalid source language raises ServiceValidationError."""
    await _setup_service(hass)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "translate",
            {"text": "Hello", "source": "xx", "target": "es"},
            blocking=True,
            return_response=True,
        )


async def test_translate_invalid_target(hass: HomeAssistant) -> None:
    """Test translate with invalid target language raises ServiceValidationError."""
    await _setup_service(hass)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "translate",
            {"text": "Hello", "source": "en", "target": "xx"},
            blocking=True,
            return_response=True,
        )


async def test_translate_api_error(hass: HomeAssistant) -> None:
    """Test translate when API is unreachable raises HomeAssistantError."""
    _entry, mock_coordinator = await _setup_service(hass)
    mock_coordinator.async_translate = AsyncMock(
        side_effect=CannotConnectError("timeout")
    )

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN,
            "translate",
            {"text": "Hello", "source": "en", "target": "es"},
            blocking=True,
            return_response=True,
        )


async def test_translate_no_config_entry(hass: HomeAssistant) -> None:
    """Test translate when no config entry exists raises ServiceValidationError."""
    # Register service without adding any config entry
    async_register_services(hass)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            "translate",
            {"text": "Hello", "source": "en", "target": "es"},
            blocking=True,
            return_response=True,
        )
