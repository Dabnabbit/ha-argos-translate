"""Tests for Argos Translate config flow."""

from unittest.mock import AsyncMock, patch

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_HOST, CONF_NAME, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.argos_translate.config_flow import (
    CannotConnect,
    InvalidAuth,
    NoLanguages,
)
from custom_components.argos_translate.const import CONF_USE_SSL, DOMAIN


async def test_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test the user config flow form — successful setup."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "custom_components.argos_translate.config_flow._async_validate_connection",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "My LibreTranslate",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 5000,
                CONF_USE_SSL: False,
                CONF_API_KEY: "test-key",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        CONF_NAME: "My LibreTranslate",
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 5000,
        CONF_USE_SSL: False,
        CONF_API_KEY: "test-key",
    }
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_cannot_connect(hass: HomeAssistant) -> None:
    """Test the config flow form — connection failure shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.argos_translate.config_flow._async_validate_connection",
        side_effect=CannotConnect,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "My LibreTranslate",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 5000,
                CONF_USE_SSL: False,
                CONF_API_KEY: "test-key",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test the config flow form — invalid auth shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.argos_translate.config_flow._async_validate_connection",
        side_effect=InvalidAuth,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "My LibreTranslate",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 5000,
                CONF_USE_SSL: False,
                CONF_API_KEY: "bad-key",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_form_no_languages(hass: HomeAssistant) -> None:
    """Test the config flow form — no languages shows error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.argos_translate.config_flow._async_validate_connection",
        side_effect=NoLanguages,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "My LibreTranslate",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 5000,
                CONF_USE_SSL: False,
                CONF_API_KEY: "",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "no_languages"}


async def test_form_duplicate_abort(hass: HomeAssistant) -> None:
    """Test the config flow aborts when the same host:port is already configured."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="192.168.1.100:5000",
        data={
            CONF_NAME: "My LibreTranslate",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 5000,
            CONF_USE_SSL: False,
            CONF_API_KEY: "existing-key",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.argos_translate.config_flow._async_validate_connection",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "My LibreTranslate",
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 5000,
                CONF_USE_SSL: False,
                CONF_API_KEY: "test-key",
            },
        )

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test the options flow updates entry.data with new values and triggers reload."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "My LibreTranslate",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 5000,
            CONF_USE_SSL: False,
            CONF_API_KEY: "old-key",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.argos_translate.config_flow._async_validate_connection",
        return_value=None,
    ), patch.object(
        hass.config_entries,
        "async_reload",
        return_value=True,
    ) as mock_reload:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.1.200",
                CONF_PORT: 5000,
                CONF_USE_SSL: True,
                CONF_API_KEY: "new-key",
            },
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.data[CONF_API_KEY] == "new-key"
    assert entry.data[CONF_HOST] == "192.168.1.200"
    assert entry.data[CONF_USE_SSL] is True
    assert entry.data[CONF_NAME] == "My LibreTranslate"
    mock_reload.assert_called_once_with(entry.entry_id)


async def test_options_flow_no_reload_on_connection_error(hass: HomeAssistant) -> None:
    """Test that async_reload is NOT called when connection validation fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "My LibreTranslate",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 5000,
            CONF_USE_SSL: False,
            CONF_API_KEY: "old-key",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.argos_translate.config_flow._async_validate_connection",
        side_effect=CannotConnect,
    ), patch.object(
        hass.config_entries,
        "async_reload",
        return_value=True,
    ) as mock_reload:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "bad-host",
                CONF_PORT: 5000,
                CONF_USE_SSL: False,
                CONF_API_KEY: "old-key",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}
    mock_reload.assert_not_called()
    assert entry.data[CONF_HOST] == "192.168.1.100"


async def test_options_flow_no_reload_on_auth_error(hass: HomeAssistant) -> None:
    """Test that async_reload is NOT called when auth validation fails."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_NAME: "My LibreTranslate",
            CONF_HOST: "192.168.1.100",
            CONF_PORT: 5000,
            CONF_USE_SSL: False,
            CONF_API_KEY: "old-key",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM

    with patch(
        "custom_components.argos_translate.config_flow._async_validate_connection",
        side_effect=InvalidAuth,
    ), patch.object(
        hass.config_entries,
        "async_reload",
        return_value=True,
    ) as mock_reload:
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: "192.168.1.100",
                CONF_PORT: 5000,
                CONF_USE_SSL: False,
                CONF_API_KEY: "bad-key",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}
    mock_reload.assert_not_called()
    assert entry.data[CONF_HOST] == "192.168.1.100"
