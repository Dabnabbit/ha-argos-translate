"""Tests for Argos Translate coordinator."""

from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argos_translate.api import CannotConnectError
from custom_components.argos_translate.const import CONF_USE_SSL, DOMAIN
from custom_components.argos_translate.coordinator import ArgosCoordinator


async def test_coordinator_update(hass: HomeAssistant) -> None:
    """Test successful data refresh from mocked API client."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 5000,
            CONF_API_KEY: "test-key",
            CONF_NAME: "Test",
            CONF_USE_SSL: False,
        },
    )
    entry.add_to_hass(hass)

    mock_languages = [
        {"code": "en", "name": "English", "targets": ["es"]},
        {"code": "es", "name": "Spanish", "targets": ["en"]},
    ]

    with patch(
        "custom_components.argos_translate.coordinator.ArgosTranslateApiClient.async_get_languages",
        new_callable=AsyncMock,
        return_value=mock_languages,
    ):
        coordinator = ArgosCoordinator(hass, entry)
        await coordinator.async_refresh()

    assert coordinator.data == {
        "languages": mock_languages,
        "language_count": 2,
    }


async def test_coordinator_update_failed(hass: HomeAssistant) -> None:
    """Test failed refresh sets last_update_success to False."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 5000,
            CONF_API_KEY: "test-key",
            CONF_NAME: "Test",
            CONF_USE_SSL: False,
        },
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.argos_translate.coordinator.ArgosTranslateApiClient.async_get_languages",
        new_callable=AsyncMock,
        side_effect=CannotConnectError("Connection refused"),
    ):
        coordinator = ArgosCoordinator(hass, entry)
        await coordinator.async_refresh()

    assert coordinator.last_update_success is False
