"""Sensor entities for Fluidra pool equipment."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EntityCategory,
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    COMPONENT_AIR_TEMP,
    COMPONENT_AUXILIARY_FLAG,
    COMPONENT_COLD_SIDE_TEMP,
    COMPONENT_COLD_SIDE_TEMP_2,
    COMPONENT_CONTROL_SUBMODE,
    COMPONENT_EFFECTIVE_MODE,
    COMPONENT_HOT_SIDE_TEMP,
    COMPONENT_INTERNAL_METRIC_60,
    COMPONENT_INTERNAL_METRIC_61,
    COMPONENT_INTERNAL_METRIC_75,
    COMPONENT_INTERNAL_METRIC_78,
    COMPONENT_INTERNAL_METRIC_79,
    COMPONENT_INTERNAL_TIMESTAMP,
    COMPONENT_MACHINE_CURRENT,
    COMPONENT_MACHINE_METRIC_72,
    COMPONENT_MACHINE_METRIC_73,
    COMPONENT_MACHINE_METRIC_76,
    COMPONENT_MACHINE_POWER,
    COMPONENT_MODE,
    COMPONENT_PUMP_AUTO_MODE,
    COMPONENT_PUMP_NETWORK,
    COMPONENT_PUMP_POWER,
    COMPONENT_PUMP_SCHEDULE,
    COMPONENT_PUMP_SPEED,
    COMPONENT_PUMP_SPEED_PERCENT,
    COMPONENT_RUNNING_HOURS,
    COMPONENT_SUPPLY_VOLTAGE,
    COMPONENT_SETPOINT_MAX,
    COMPONENT_SETPOINT_MIN,
    COMPONENT_TIMER_FLAG,
    COMPONENT_WATER_INLET_TEMP,
    COMPONENT_WATER_OUTLET_TEMP,
    COMPONENT_WATER_TEMP,
    MODE_LABELS,
    PUMP_SPEED_LEVEL_TO_OPTION,
)
from .coordinator import FluidraPoolCoordinator
from .entity import FluidraPoolEntity, coordinators_from_entry


@dataclass(frozen=True, kw_only=True)
class FluidraSensorDescription(SensorEntityDescription):
    """Describe a Fluidra component-backed sensor."""

    component_id: int
    divisor: float = 1.0


HEAT_PUMP_SENSOR_DESCRIPTIONS: tuple[FluidraSensorDescription, ...] = (
    FluidraSensorDescription(
        key="water_temperature",
        name="Water temperature",
        component_id=COMPONENT_WATER_TEMP,
        divisor=10.0,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    FluidraSensorDescription(
        key="air_temperature",
        name="Air temperature",
        component_id=COMPONENT_AIR_TEMP,
        divisor=10.0,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    FluidraSensorDescription(
        key="water_inlet_temperature",
        name="Water inlet temperature",
        component_id=COMPONENT_WATER_INLET_TEMP,
        divisor=10.0,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    FluidraSensorDescription(
        key="water_outlet_temperature",
        name="Water outlet temperature",
        component_id=COMPONENT_WATER_OUTLET_TEMP,
        divisor=10.0,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    FluidraSensorDescription(
        key="hot_side_temperature",
        name="Hot-side temperature",
        component_id=COMPONENT_HOT_SIDE_TEMP,
        divisor=10.0,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="cold_side_temperature",
        name="Cold-side temperature",
        component_id=COMPONENT_COLD_SIDE_TEMP,
        divisor=10.0,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="cold_side_temperature_2",
        name="Cold-side temperature 2",
        component_id=COMPONENT_COLD_SIDE_TEMP_2,
        divisor=10.0,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="operating_hours",
        name="Operating hours",
        component_id=COMPONENT_RUNNING_HOURS,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
    ),
    FluidraSensorDescription(
        key="supply_voltage",
        name="Supply voltage",
        component_id=COMPONENT_SUPPLY_VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="machine_power",
        name="Machine power",
        component_id=COMPONENT_MACHINE_POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="machine_current",
        name="Machine current",
        component_id=COMPONENT_MACHINE_CURRENT,
        divisor=10.0,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="internal_timestamp",
        name="Internal timestamp",
        component_id=COMPONENT_INTERNAL_TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="control_submode",
        name="Control submode",
        component_id=COMPONENT_CONTROL_SUBMODE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="timer_flag",
        name="Timer flag",
        component_id=COMPONENT_TIMER_FLAG,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="auxiliary_flag",
        name="Auxiliary flag",
        component_id=COMPONENT_AUXILIARY_FLAG,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="internal_metric_60",
        name="Internal metric 60",
        component_id=COMPONENT_INTERNAL_METRIC_60,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="internal_metric_61",
        name="Internal metric 61",
        component_id=COMPONENT_INTERNAL_METRIC_61,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="machine_metric_72",
        name="Machine metric 72",
        component_id=COMPONENT_MACHINE_METRIC_72,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="machine_metric_73",
        name="Machine metric 73",
        component_id=COMPONENT_MACHINE_METRIC_73,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="internal_metric_75",
        name="Internal metric 75",
        component_id=COMPONENT_INTERNAL_METRIC_75,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="machine_metric_76",
        name="Machine metric 76",
        component_id=COMPONENT_MACHINE_METRIC_76,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="internal_metric_78",
        name="Internal metric 78",
        component_id=COMPONENT_INTERNAL_METRIC_78,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="internal_metric_79",
        name="Internal metric 79",
        component_id=COMPONENT_INTERNAL_METRIC_79,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="minimum_setpoint",
        name="Minimum setpoint",
        component_id=COMPONENT_SETPOINT_MIN,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="maximum_setpoint",
        name="Maximum setpoint",
        component_id=COMPONENT_SETPOINT_MAX,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Fluidra sensor entities."""
    entities: list[SensorEntity] = []

    for coordinator in coordinators_from_entry(hass, entry):
        if coordinator.is_heat_pump:
            entities.extend(
                FluidraComponentSensor(coordinator, description)
                for description in HEAT_PUMP_SENSOR_DESCRIPTIONS
            )
            entities.extend(
                [
                    FluidraModeSensor(
                        coordinator,
                        key="requested_mode",
                        name="Requested mode",
                        component_id=COMPONENT_MODE,
                    ),
                    FluidraModeSensor(
                        coordinator,
                        key="effective_mode",
                        name="Effective mode",
                        component_id=COMPONENT_EFFECTIVE_MODE,
                    ),
                    FluidraEfficiencySensor(coordinator),
                ]
            )
        elif coordinator.is_pump:
            has_speed_percent = coordinator.has_component(COMPONENT_PUMP_SPEED_PERCENT)
            has_speed_level = coordinator.has_component(COMPONENT_PUMP_SPEED)
            if has_speed_percent or has_speed_level:
                entities.append(FluidraPumpSpeedPercentSensor(coordinator))
            if has_speed_level:
                entities.append(FluidraPumpSpeedLevelSensor(coordinator))
            entities.extend(
                FluidraPumpComponentStatusSensor(coordinator, description)
                for description in PUMP_STATUS_SENSOR_DESCRIPTIONS
                if coordinator.has_component(description.component_id)
            )

        entities.append(FluidraRawComponentsSensor(coordinator))
    async_add_entities(entities)


PUMP_STATUS_SENSOR_DESCRIPTIONS: tuple[FluidraSensorDescription, ...] = (
    FluidraSensorDescription(
        key="pump_power_value",
        name="Pump power value",
        component_id=COMPONENT_PUMP_POWER,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="pump_auto_mode_value",
        name="Auto mode value",
        component_id=COMPONENT_PUMP_AUTO_MODE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="pump_schedule_value",
        name="Schedule value",
        component_id=COMPONENT_PUMP_SCHEDULE,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    FluidraSensorDescription(
        key="pump_network_value",
        name="Network value",
        component_id=COMPONENT_PUMP_NETWORK,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


class FluidraComponentSensor(FluidraPoolEntity, SensorEntity):
    """Sensor backed by a single Fluidra component."""

    entity_description: FluidraSensorDescription

    def __init__(
        self,
        coordinator: FluidraPoolCoordinator,
        description: FluidraSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name

    @property
    def native_value(self) -> float | int | None:
        """Return the current sensor value."""
        raw_value = self.component_value(self.entity_description.component_id)
        if raw_value is None:
            return None

        if self.entity_description.divisor != 1.0:
            if not isinstance(raw_value, (int, float)):
                return None
            return raw_value / self.entity_description.divisor

        if isinstance(raw_value, (int, float)):
            return raw_value
        return None


class FluidraModeSensor(FluidraPoolEntity, SensorEntity):
    """Text sensor describing a requested or effective mode."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(
        self,
        coordinator: FluidraPoolCoordinator,
        *,
        key: str,
        name: str,
        component_id: int,
    ) -> None:
        super().__init__(coordinator, key)
        self._attr_name = name
        self._component_id = component_id

    @property
    def native_value(self) -> str | None:
        """Return the current mode label."""
        raw_value = self.component_value(self._component_id)
        if not isinstance(raw_value, int):
            return None
        return MODE_LABELS.get(raw_value, f"Mode {raw_value}")

    @property
    def extra_state_attributes(self) -> dict[str, int] | None:
        """Expose the raw mode code."""
        raw_value = self.component_value(self._component_id)
        if not isinstance(raw_value, int):
            return None
        return {"mode_code": raw_value}


class FluidraPumpSpeedPercentSensor(FluidraPoolEntity, SensorEntity):
    """Sensor exposing the pump speed percentage."""

    _attr_name = "Speed percent"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: FluidraPoolCoordinator) -> None:
        super().__init__(coordinator, "pump_speed_percent")

    @property
    def native_value(self) -> int:
        """Return the pump speed percentage."""
        return self.coordinator.get_pump_speed_percent()


class FluidraPumpSpeedLevelSensor(FluidraPoolEntity, SensorEntity):
    """Diagnostic sensor exposing the raw pump speed level."""

    _attr_name = "Speed level"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: FluidraPoolCoordinator) -> None:
        super().__init__(coordinator, "pump_speed_level")

    @property
    def native_value(self) -> int | None:
        """Return the raw pump speed level."""
        return self.coordinator.get_pump_speed_level()

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Expose the level label used by the select entity."""
        speed_level = self.coordinator.get_pump_speed_level()
        if speed_level is None:
            return None
        option = PUMP_SPEED_LEVEL_TO_OPTION.get(speed_level)
        if option is None:
            return None
        return {"option": option}


class FluidraPumpComponentStatusSensor(FluidraPoolEntity, SensorEntity):
    """Diagnostic sensor exposing a raw pump component value."""

    entity_description: FluidraSensorDescription

    def __init__(
        self,
        coordinator: FluidraPoolCoordinator,
        description: FluidraSensorDescription,
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_name = description.name

    @property
    def native_value(self) -> str | int | float | None:
        """Return a compact state for the raw component."""
        raw_value = self.component_value(self.entity_description.component_id)
        if raw_value is None:
            return None
        if isinstance(raw_value, bool):
            return int(raw_value)
        if isinstance(raw_value, (int, float, str)):
            return raw_value
        return "available"

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Expose the raw component value when it is structured."""
        raw_value = self.component_value(self.entity_description.component_id)
        if raw_value is None or isinstance(raw_value, (bool, int, float, str)):
            return None
        return {"raw_value": raw_value}


class FluidraEfficiencySensor(FluidraPoolEntity, SensorEntity):
    """Derived efficiency proxy based on absorbed power and water delta."""

    _attr_name = "Efficience"
    _attr_native_unit_of_measurement = "W/degC"
    _attr_suggested_display_precision = 1
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: FluidraPoolCoordinator) -> None:
        super().__init__(coordinator, "efficiency_ratio")

    @property
    def native_value(self) -> float | None:
        """Return power divided by the absolute inlet/outlet water delta."""
        values = self._source_values()
        if values is None:
            return None

        power, inlet_temp, outlet_temp = values
        delta = abs(outlet_temp - inlet_temp)
        if delta <= 0:
            return None
        return power / delta

    @property
    def extra_state_attributes(self) -> dict[str, float | None] | None:
        """Expose the values used to compute the ratio."""
        values = self._source_values()
        if values is None:
            return None

        power, inlet_temp, outlet_temp = values
        signed_delta = outlet_temp - inlet_temp
        absolute_delta = abs(signed_delta)
        return {
            "machine_power_w": power,
            "water_inlet_temperature_c": inlet_temp,
            "water_outlet_temperature_c": outlet_temp,
            "signed_delta_c": signed_delta,
            "absolute_delta_c": absolute_delta,
        }

    def _source_values(self) -> tuple[float, float, float] | None:
        """Return the source values needed for the efficiency calculation."""
        power = self.component_value(COMPONENT_MACHINE_POWER)
        inlet_temp = self.scaled_component_value(COMPONENT_WATER_INLET_TEMP)
        outlet_temp = self.scaled_component_value(COMPONENT_WATER_OUTLET_TEMP)
        if not isinstance(power, (int, float)):
            return None
        if inlet_temp is None or outlet_temp is None:
            return None
        return float(power), inlet_temp, outlet_temp


class FluidraRawComponentsSensor(FluidraPoolEntity, SensorEntity):
    """Diagnostic sensor exposing the raw component table."""

    _attr_name = "Raw components"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: FluidraPoolCoordinator) -> None:
        super().__init__(coordinator, "raw_components")

    @property
    def native_value(self) -> int | None:
        """Return the number of cached components."""
        if self.coordinator.data is None:
            return None
        return len(self.coordinator.data.components)

    @property
    def extra_state_attributes(self) -> dict[str, object] | None:
        """Expose raw component values and coordinator timestamps."""
        if self.coordinator.data is None:
            return None

        raw_values = {
            str(component_id): component.get("reportedValue")
            for component_id, component in sorted(self.coordinator.data.components.items())
        }
        desired_values = {
            str(component_id): component["desiredValue"]
            for component_id, component in sorted(self.coordinator.data.components.items())
            if "desiredValue" in component
        }
        return {
            "component_values": raw_values,
            "desired_values": desired_values,
            "websocket_connected": self.coordinator.data.websocket_connected,
            "last_refresh": _as_iso(self.coordinator.data.last_refresh),
            "last_push": _as_iso(self.coordinator.data.last_push),
        }


def _as_iso(value: datetime | None) -> str | None:
    """Serialize datetimes for sensor attributes."""
    if value is None:
        return None
    return value.isoformat()
