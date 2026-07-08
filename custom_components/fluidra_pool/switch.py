"""Switch entities for Fluidra pool equipment."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    COMPONENT_PUMP_AUTO_MODE,
    COMPONENT_PUMP_POWER,
    DOMAIN,
)
from .coordinator import FluidraPoolCoordinator
from .entity import FluidraPoolEntity


@dataclass(frozen=True, kw_only=True)
class FluidraSwitchDescription(SwitchEntityDescription):
    """Describe a Fluidra switch."""

    component_id: int
    setter_name: str


PUMP_SWITCH_DESCRIPTIONS: tuple[FluidraSwitchDescription, ...] = (
    FluidraSwitchDescription(
        key="pump_power",
        name="Pump",
        component_id=COMPONENT_PUMP_POWER,
        setter_name="async_set_pump_power",
    ),
    FluidraSwitchDescription(
        key="pump_auto_mode",
        name="Auto mode",
        component_id=COMPONENT_PUMP_AUTO_MODE,
        setter_name="async_set_pump_auto_mode",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fluidra switch entities."""
    coordinator: FluidraPoolCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    if not coordinator.is_pump:
        return

    async_add_entities(
        FluidraComponentSwitch(coordinator, description)
        for description in PUMP_SWITCH_DESCRIPTIONS
        if coordinator.has_component(description.component_id)
    )


class FluidraComponentSwitch(FluidraPoolEntity, SwitchEntity):
    """Switch backed by a single Fluidra component."""

    entity_description: FluidraSwitchDescription

    def __init__(
        self,
        coordinator: FluidraPoolCoordinator,
        description: FluidraSwitchDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name

    @property
    def is_on(self) -> bool | None:
        """Return the current switch state."""
        raw_value = self.component_value(self.entity_description.component_id)
        if raw_value is None:
            return None
        return bool(raw_value)

    async def async_turn_on(self, **kwargs: object) -> None:
        """Turn the switch on."""
        setter = getattr(self.coordinator, self.entity_description.setter_name)
        await setter(True)

    async def async_turn_off(self, **kwargs: object) -> None:
        """Turn the switch off."""
        setter = getattr(self.coordinator, self.entity_description.setter_name)
        await setter(False)
