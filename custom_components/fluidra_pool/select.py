"""Select entities for Fluidra pool equipment."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    COMPONENT_PUMP_SPEED,
    DOMAIN,
    PUMP_SPEED_LEVEL_TO_OPTION,
    PUMP_SPEED_OPTION_TO_LEVEL,
    PUMP_SPEED_OPTIONS,
)
from .coordinator import FluidraPoolCoordinator
from .entity import FluidraPoolEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fluidra select entities."""
    coordinator: FluidraPoolCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    if not coordinator.is_pump or not coordinator.has_component(COMPONENT_PUMP_SPEED):
        return

    async_add_entities([FluidraPumpSpeedSelect(coordinator)])


class FluidraPumpSpeedSelect(FluidraPoolEntity, SelectEntity):
    """Pump speed selector."""

    _attr_name = "Speed"
    _attr_options = list(PUMP_SPEED_OPTIONS)

    def __init__(self, coordinator: FluidraPoolCoordinator) -> None:
        super().__init__(coordinator, "pump_speed")

    @property
    def current_option(self) -> str | None:
        """Return the selected speed option."""
        speed_level = self.coordinator.get_pump_speed_level()
        if speed_level is None:
            return None
        return PUMP_SPEED_LEVEL_TO_OPTION.get(speed_level)

    async def async_select_option(self, option: str) -> None:
        """Select a pump speed."""
        speed_level = PUMP_SPEED_OPTION_TO_LEVEL[option]
        await self.coordinator.async_set_pump_speed_level(speed_level)
