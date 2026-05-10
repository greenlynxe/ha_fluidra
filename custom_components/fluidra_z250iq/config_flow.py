"""Config flow for Fluidra Z250iQ."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FluidraApiClient, FluidraApiError, device_display_name
from .auth import FluidraAuthenticationError
from .const import (
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
)


_LOGGER = logging.getLogger(__name__)


class FluidraZ250IQConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle configuration for Fluidra Z250iQ."""

    VERSION = 1

    def __init__(self) -> None:
        self._user_input: dict[str, Any] | None = None
        self._devices: list[dict[str, Any]] = []

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Authenticate and discover Z250iQ devices."""
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
                elif len(devices) == 1:
                    return await self._async_create_entry(user_input, devices[0])
                else:
                    self._user_input = user_input
                    self._devices = devices
                    return await self.async_step_select_device()

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

    async def async_step_select_device(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select a device when multiple Z250iQ-like devices are found."""
        if self._user_input is None:
            return await self.async_step_user()

        if user_input is not None:
            selected_id = user_input[CONF_DEVICE_ID]
            selected = next(
                device for device in self._devices if str(device.get("id")) == selected_id
            )
            return await self._async_create_entry(self._user_input, selected)

        options = {
            str(device["id"]): device_display_name(device) for device in self._devices
        }
        return self.async_show_form(
            step_id="select_device",
            data_schema=vol.Schema(
                {vol.Required(CONF_DEVICE_ID): vol.In(options)}
            ),
        )

    async def _async_create_entry(
        self, credentials: dict[str, Any], device: dict[str, Any]
    ) -> FlowResult:
        """Create the config entry for the selected device."""
        device_id = str(device["id"])
        await self.async_set_unique_id(device_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=device_display_name(device),
            data={
                CONF_USERNAME: credentials[CONF_USERNAME],
                CONF_PASSWORD: credentials[CONF_PASSWORD],
                CONF_DEVICE_ID: device_id,
                CONF_DEVICE_NAME: device_display_name(device),
                CONF_SCAN_INTERVAL: int(DEFAULT_SCAN_INTERVAL.total_seconds() / 60),
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow."""
        return FluidraZ250IQOptionsFlow(config_entry)


class FluidraZ250IQOptionsFlow(config_entries.OptionsFlow):
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
