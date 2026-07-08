"""Config flow for Fluidra pool equipment."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FluidraApiClient, FluidraApiError
from .auth import FluidraAuthenticationError
from .const import (
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


_LOGGER = logging.getLogger(__name__)


class FluidraPoolConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle configuration for supported Fluidra devices."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Authenticate and discover supported devices."""
        errors: dict[str, str] = {}

        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = FluidraApiClient(
                session,
                user_input[CONF_USERNAME],
                user_input[CONF_PASSWORD],
            )
            try:
                devices = await api.async_get_supported_devices()
            except FluidraAuthenticationError:
                errors["base"] = "invalid_auth"
            except FluidraApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pragma: no cover - HA runtime guardrail
                _LOGGER.exception("Unexpected error while loading the Fluidra config flow")
                errors["base"] = "cannot_connect"
            else:
                if not devices:
                    errors["base"] = "no_supported_device"
                else:
                    return await self._async_create_entry(user_input, len(devices))

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_USERNAME): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def _async_create_entry(
        self, credentials: dict[str, Any], device_count: int
    ) -> FlowResult:
        """Create the config entry for the Fluidra account."""
        username = str(credentials[CONF_USERNAME]).strip()
        normalized_username = username.lower()
        for entry in self._async_current_entries():
            configured_username = str(entry.data.get(CONF_USERNAME, "")).strip().lower()
            if configured_username == normalized_username:
                return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(normalized_username)
        self._abort_if_unique_id_configured()

        title = "Fluidra Pool"
        if device_count > 1:
            title = f"{title} ({device_count} appareils)"

        return self.async_create_entry(
            title=title,
            data={
                CONF_USERNAME: username,
                CONF_PASSWORD: credentials[CONF_PASSWORD],
                CONF_SCAN_INTERVAL: int(DEFAULT_SCAN_INTERVAL.total_seconds() / 60),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return FluidraPoolOptionsFlow(config_entry)


class FluidraPoolOptionsFlow(config_entries.OptionsFlow):
    """Manage integration options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure poll interval."""
        if user_input is not None:
            return self.async_create_entry(
                title="", data={CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL]}
            )

        default_interval = int(DEFAULT_SCAN_INTERVAL.total_seconds() / 60)
        min_interval = int(MIN_SCAN_INTERVAL.total_seconds() / 60)
        max_interval = int(MAX_SCAN_INTERVAL.total_seconds() / 60)
        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, default_interval),
        )
        if not isinstance(current_interval, int):
            current_interval = default_interval
        elif current_interval < min_interval:
            current_interval = default_interval
        current_interval = min(max_interval, max(min_interval, current_interval))
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SCAN_INTERVAL, default=current_interval): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=min_interval, max=max_interval),
                    )
                }
            ),
        )
