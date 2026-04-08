"""Shared entity helpers for Fluidra Z250iQ entities."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FluidraZ250IQCoordinator


class FluidraZ250IQEntity(CoordinatorEntity[FluidraZ250IQCoordinator]):
    """Common base entity for the integration."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FluidraZ250IQCoordinator, unique_suffix: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.device_id}_{unique_suffix}"

    @property
    def available(self) -> bool:
        """Return True when we have current coordinator data."""
        return self.coordinator.data is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Describe the physical heat pump."""
        device = self.coordinator.data.device if self.coordinator.data else {}
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.device_id)},
            manufacturer="Fluidra",
            model=device.get("model") or "Z250iQ",
            name=device.get("name") or self.coordinator.device_name,
            serial_number=device.get("serial_number"),
            sw_version=device.get("firmware"),
        )

    def component_value(self, component_id: int, default: Any = None) -> Any:
        """Return a raw component value."""
        return self.coordinator.get_component_value(component_id, default)

    def scaled_component_value(
        self, component_id: int, *, divisor: float = 10.0
    ) -> float | None:
        """Return a scaled component value."""
        return self.coordinator.get_scaled_component_value(component_id, divisor=divisor)
