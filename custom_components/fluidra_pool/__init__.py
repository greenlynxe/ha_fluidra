"""Fluidra pool equipment integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import FluidraApiClient, FluidraApiError
from .auth import FluidraAuthenticationError
from .const import CONF_PASSWORD, CONF_USERNAME, DATA_COORDINATORS, DOMAIN
from .coordinator import FluidraPoolCoordinator
from .device_profile import identify_device_profile

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.CLIMATE,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Fluidra pool equipment from a config entry."""
    session = async_get_clientsession(hass)
    api = FluidraApiClient(
        session,
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )

    try:
        devices = await api.async_get_supported_devices()
    except FluidraAuthenticationError as err:
        raise ConfigEntryAuthFailed(str(err)) from err
    except FluidraApiError as err:
        raise ConfigEntryNotReady(str(err)) from err

    if not devices:
        raise ConfigEntryNotReady("No supported Fluidra devices found")

    coordinators: dict[str, FluidraPoolCoordinator] = {}
    try:
        for device in devices:
            coordinator = FluidraPoolCoordinator(
                hass,
                entry,
                api,
                device,
                identify_device_profile(device),
            )
            await coordinator.async_config_entry_first_refresh()
            coordinators[coordinator.device_id] = coordinator
    except Exception:
        for coordinator in coordinators.values():
            await coordinator.async_shutdown()
        raise

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATORS: coordinators
    }
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinators: dict[str, FluidraPoolCoordinator] = hass.data[DOMAIN][
            entry.entry_id
        ][DATA_COORDINATORS]
        for coordinator in coordinators.values():
            await coordinator.async_shutdown()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
