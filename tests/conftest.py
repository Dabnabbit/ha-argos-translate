"""Common fixtures for the Argos Translate tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_NAME, CONF_PORT

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argos_translate.const import CONF_USE_SSL, DOMAIN

MOCK_LANGUAGES = [
    {"code": "en", "name": "English", "targets": ["es", "fr"]},
    {"code": "es", "name": "Spanish", "targets": ["en"]},
    {"code": "fr", "name": "French", "targets": ["en", "es"]},
]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this package."""
    yield


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry to prevent full integration setup during config flow tests."""
    with patch(
        "custom_components.argos_translate.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a mock config entry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Test LibreTranslate",
        data={
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 5000,
            CONF_API_KEY: "",
            CONF_NAME: "Test LibreTranslate",
            CONF_USE_SSL: False,
        },
    )
