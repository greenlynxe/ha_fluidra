"""Climate entities for Fluidra heat pumps."""

from __future__ import annotations

from homeassistant.components.climate import ClimateEntity, ClimateEntityFeature
from homeassistant.components.climate.const import HVACAction, HVACMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    COMPONENT_ACTIVE,
    COMPONENT_POWER,
    COMPONENT_SETPOINT,
    COMPONENT_WATER_TEMP,
    COOLING_MODE_VALUES,
    DOMAIN,
    HEATING_MODE_VALUES,
    MODE_LABELS,
    MODE_SMART_AUTO,
    MODE_SMART_COOLING,
    MODE_SMART_HEATING,
    PRESET_TO_MODE,
)
from .coordinator import FluidraPoolCoordinator
from .entity import FluidraPoolEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fluidra climate entities."""
    coordinator: FluidraPoolCoordinator = hass.data[DOMAIN][entry.entry_id][
        "coordinator"
    ]
    if not coordinator.is_heat_pump:
        return
    async_add_entities([FluidraHeatPumpClimate(coordinator)])


class FluidraHeatPumpClimate(FluidraPoolEntity, ClimateEntity):
    """Represent a Fluidra heat pump as a Home Assistant climate entity."""

    _attr_name = None
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_target_temperature_step = 1.0
    _attr_supported_features = (
        ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    _attr_hvac_modes = [
        HVACMode.OFF,
        HVACMode.HEAT,
        HVACMode.COOL,
        HVACMode.HEAT_COOL,
    ]
    _attr_preset_modes = list(PRESET_TO_MODE.keys())

    def __init__(self, coordinator: FluidraPoolCoordinator) -> None:
        super().__init__(coordinator, "climate")

    @property
    def current_temperature(self) -> float | None:
        """Return measured pool water temperature."""
        return self.scaled_component_value(COMPONENT_WATER_TEMP)

    @property
    def target_temperature(self) -> float | None:
        """Return the target water temperature."""
        return self.scaled_component_value(COMPONENT_SETPOINT)

    @property
    def min_temp(self) -> float:
        """Return the current minimum setpoint bound."""
        return self.coordinator.get_setpoint_bounds()[0]

    @property
    def max_temp(self) -> float:
        """Return the current maximum setpoint bound."""
        return self.coordinator.get_setpoint_bounds()[1]

    @property
    def hvac_mode(self) -> HVACMode:
        """Map the heat pump state to a Home Assistant HVAC mode."""
        power = self.component_value(COMPONENT_POWER, 0)
        if power == 0:
            return HVACMode.OFF

        mode = self.coordinator.get_effective_mode()
        if mode in HEATING_MODE_VALUES:
            return HVACMode.HEAT
        if mode in COOLING_MODE_VALUES:
            return HVACMode.COOL
        if mode == MODE_SMART_AUTO:
            return HVACMode.HEAT_COOL
        return HVACMode.HEAT

    @property
    def hvac_action(self) -> HVACAction:
        """Return the active action based on component 11 and the effective mode."""
        if self.hvac_mode == HVACMode.OFF:
            return HVACAction.OFF

        running = self.component_value(COMPONENT_ACTIVE, 0)
        if running != 1:
            return HVACAction.IDLE

        mode = self.coordinator.get_effective_mode()
        if mode in HEATING_MODE_VALUES:
            return HVACAction.HEATING
        if mode in COOLING_MODE_VALUES:
            return HVACAction.COOLING

        current = self.current_temperature
        target = self.target_temperature
        if current is not None and target is not None and current > target:
            return HVACAction.COOLING
        return HVACAction.HEATING

    @property
    def preset_mode(self) -> str | None:
        """Return the current heat pump preset/mode label."""
        mode = self.coordinator.get_effective_mode()
        return MODE_LABELS.get(mode)

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set the operating mode."""
        if hvac_mode == HVACMode.OFF:
            await self.coordinator.async_set_power(False)
            return

        await self.coordinator.async_set_power(True)
        if hvac_mode == HVACMode.HEAT:
            await self.coordinator.async_set_mode(MODE_SMART_HEATING)
        elif hvac_mode == HVACMode.COOL:
            await self.coordinator.async_set_mode(MODE_SMART_COOLING)
        elif hvac_mode == HVACMode.HEAT_COOL:
            await self.coordinator.async_set_mode(MODE_SMART_AUTO)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set one of the validated Fluidra operating modes."""
        mode = PRESET_TO_MODE[preset_mode]
        await self.coordinator.async_set_power(True)
        await self.coordinator.async_set_mode(mode)

    async def async_set_temperature(self, **kwargs: float) -> None:
        """Set the target water temperature."""
        if ATTR_TEMPERATURE not in kwargs:
            return
        await self.coordinator.async_set_target_temperature(kwargs[ATTR_TEMPERATURE])

    async def async_turn_on(self) -> None:
        """Turn the heat pump on."""
        await self.coordinator.async_set_power(True)

    async def async_turn_off(self) -> None:
        """Turn the heat pump off."""
        await self.coordinator.async_set_power(False)
