"""Binary sensors for Fluidra pool equipment."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COMPONENT_ACTIVE, COMPONENT_NO_FLOW, DOMAIN
from .coordinator import FluidraPoolCoordinator
from .entity import FluidraPoolEntity


@dataclass(frozen=True, kw_only=True)
class FluidraBinarySensorDescription(BinarySensorEntityDescription):
    """Describe a Fluidra binary sensor."""

    component_id: int


BINARY_SENSOR_DESCRIPTIONS: tuple[FluidraBinarySensorDescription, ...] = (
    FluidraBinarySensorDescription(
        key="running",
        name="Running",
        component_id=COMPONENT_ACTIVE,
        device_class=BinarySensorDeviceClass.RUNNING,
    ),
    FluidraBinarySensorDescription(
        key="no_flow",
        name="No flow",
        component_id=COMPONENT_NO_FLOW,
        device_class=BinarySensorDeviceClass.PROBLEM,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fluidra binary sensors."""
    coordinator: FluidraPoolCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    if not coordinator.is_heat_pump:
        return
    async_add_entities(
        FluidraComponentBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class FluidraComponentBinarySensor(FluidraPoolEntity, BinarySensorEntity):
    """Binary sensor backed by a single component."""

    entity_description: FluidraBinarySensorDescription

    def __init__(
        self,
        coordinator: FluidraPoolCoordinator,
        description: FluidraBinarySensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        raw_value = self.component_value(self.entity_description.component_id)
        if raw_value is None:
            return None
        return bool(raw_value)
