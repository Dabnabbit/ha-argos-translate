"""Config flow for Argos Translate integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_API_KEY
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ApiClient, CannotConnectError as ApiCannotConnect, InvalidAuthError as ApiInvalidAuth
from .const import DEFAULT_PORT, DOMAIN

_LOGGER = logging.getLogger(__name__)


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_API_KEY): str,
    }
)



class CannotConnect(Exception):
    """Error to indicate we cannot connect."""


class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""


async def _async_validate_connection(hass: HomeAssistant, user_input: dict) -> None:
    """Validate the user can connect to the service.

    Raise CannotConnect or InvalidAuth on failure.
    """
    session = async_get_clientsession(hass)
    client = ApiClient(
        host=user_input[CONF_HOST],
        port=user_input[CONF_PORT],
        api_key=user_input[CONF_API_KEY],
        session=session,
    )
    try:
        await client.async_test_connection()
    except ApiCannotConnect as err:
        raise CannotConnect from err
    except ApiInvalidAuth as err:
        raise InvalidAuth from err


class TemplateConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Argos Translate."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler()


    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            )
            self._abort_if_unique_id_configured()

            try:
                await _async_validate_connection(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )



class OptionsFlowHandler(OptionsFlow):
    """Handle options flow for Argos Translate."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(data={})

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_HOST,
                        default=self.config_entry.data.get(CONF_HOST, ""),
                    ): str,
                    vol.Optional(
                        CONF_PORT,
                        default=self.config_entry.data.get(CONF_PORT, DEFAULT_PORT),
                    ): int,
                    vol.Optional(
                        CONF_API_KEY,
                        default=self.config_entry.data.get(CONF_API_KEY, ""),
                    ): str,
                }
            ),
        )
