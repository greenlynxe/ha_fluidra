"""Coordinator for the Fluidra Z250iQ integration."""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from typing import Any

from aiohttp import WSMsgType
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FluidraApiClient, FluidraApiError, device_display_name, is_supported_device
from .auth import FluidraAuthenticationError
from .const import (
    COMPONENT_EFFECTIVE_MODE,
    COMPONENT_MODE,
    COMPONENT_POWER,
    COMPONENT_SETPOINT,
    COMPONENT_SETPOINT_MAX,
    COMPONENT_SETPOINT_MIN,
    CONF_DEVICE_ID,
    CONF_DEVICE_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MIN_SCAN_INTERVAL,
    WS_RECONNECT_DELAY,
    WS_URL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class FluidraDeviceState:
    """Current Z250iQ state cached by the coordinator."""

    device: dict[str, Any]
    detail: dict[str, Any]
    components: dict[int, dict[str, Any]]
    uiconfig: dict[str, Any]
    last_refresh: datetime
    last_push: datetime | None = None
    websocket_connected: bool = False


class FluidraZ250IQCoordinator(DataUpdateCoordinator[FluidraDeviceState]):
    """Coordinate API polling and WebSocket updates for one Z250iQ."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: FluidraApiClient,
    ) -> None:
        scan_interval = entry.options.get(
            CONF_SCAN_INTERVAL, entry.data.get(CONF_SCAN_INTERVAL, 5)
        )
        update_interval = DEFAULT_SCAN_INTERVAL
        if isinstance(scan_interval, int):
            update_interval = timedelta(minutes=scan_interval)
        update_interval = min(MAX_SCAN_INTERVAL, max(MIN_SCAN_INTERVAL, update_interval))

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )

        self.entry = entry
        self.api = api
        self.device_id = entry.data[CONF_DEVICE_ID]
        self.device_name = entry.data.get(CONF_DEVICE_NAME, self.device_id)
        self._uiconfig: dict[str, Any] = {}
        self._ws_task: asyncio.Task[None] | None = None
        self._ws_running = False
        self._delayed_refresh_task: asyncio.Task[None] | None = None

    async def async_shutdown(self) -> None:
        """Cancel background tasks."""
        self._ws_running = False
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
        if self._delayed_refresh_task and not self._delayed_refresh_task.done():
            self._delayed_refresh_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._delayed_refresh_task

    async def _async_update_data(self) -> FluidraDeviceState:
        """Fetch the latest device state from the cloud API."""
        try:
            detail = await self.api.async_get_device_detail(self.device_id)
            if not is_supported_device(detail):
                raise UpdateFailed("The configured device is not a supported Z250iQ")

            components = await self.api.async_get_device_components(self.device_id)
            if not self._uiconfig:
                self._uiconfig = await self.api.async_get_device_uiconfig(self.device_id)

            device = {
                "id": detail.get("id", self.device_id),
                "name": device_display_name(detail),
                "model": detail.get("info", {}).get("name")
                or detail.get("info", {}).get("family"),
                "serial_number": detail.get("sn") or detail.get("serialNumber"),
                "firmware": detail.get("vr") or detail.get("currentFirmwareVersion"),
                "sku": detail.get("sku"),
            }
            state = FluidraDeviceState(
                device=device,
                detail=detail,
                components=components,
                uiconfig=self._uiconfig,
                last_refresh=datetime.now(timezone.utc),
                last_push=self.data.last_push if self.data else None,
                websocket_connected=self.data.websocket_connected if self.data else False,
            )
            self._ensure_websocket_started()
            return state
        except FluidraAuthenticationError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except FluidraApiError as err:
            raise UpdateFailed(str(err)) from err

    def _ensure_websocket_started(self) -> None:
        """Start the WebSocket listener once."""
        if self._ws_task is None or self._ws_task.done():
            self._ws_running = True
            self._ws_task = self.hass.async_create_task(self._websocket_loop())

    async def _websocket_loop(self) -> None:
        """Subscribe to push updates for the configured device."""
        while self._ws_running:
            try:
                token = await self.api.async_get_access_token(force=True)
                ws_url = f"{WS_URL}?token={token}"
                async with self.api._session.ws_connect(ws_url, heartbeat=30) as ws:
                    await ws.send_json(
                        {
                            "action": "subsDevice",
                            "deviceType": "connected",
                            "deviceId": self.device_id,
                        }
                    )
                    self._set_websocket_connected(True)
                    async for message in ws:
                        if message.type == WSMsgType.TEXT:
                            await self._handle_websocket_message(message.data)
                        elif message.type == WSMsgType.ERROR:
                            break
                        elif message.type in (WSMsgType.CLOSE, WSMsgType.CLOSED):
                            break
            except asyncio.CancelledError:
                return
            except Exception as err:  # pragma: no cover - network/runtime behaviour
                _LOGGER.debug("Fluidra WebSocket disconnected: %s", err)
            finally:
                self._set_websocket_connected(False)

            if self._ws_running:
                await asyncio.sleep(WS_RECONNECT_DELAY)

    async def _handle_websocket_message(self, payload: str) -> None:
        """Merge a push event into the current component cache."""
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            return
        if self.data is None:
            return

        component_events = self._extract_component_events(event)
        if not component_events:
            return

        components = dict(self.data.components)
        did_update = False
        for item in component_events:
            device_id = item.get("deviceId") or item.get("device_id")
            if device_id and device_id != self.device_id:
                continue

            component_id = (
                item.get("componentId") or item.get("id") or item.get("componentID")
            )
            reported_value = (
                item.get("reportedValue")
                if "reportedValue" in item
                else item.get("value", item.get("desiredValue"))
            )
            if component_id is None or reported_value is None:
                continue

            try:
                component_key = int(component_id)
            except (TypeError, ValueError):
                continue

            component = dict(components.get(component_key, {"id": component_key}))
            component["reportedValue"] = reported_value
            if "desiredValue" in item:
                component["desiredValue"] = item["desiredValue"]
            if "ts" in item:
                component["ts"] = item["ts"]
            components[component_key] = component
            did_update = True

        if not did_update:
            return

        self.async_set_updated_data(
            replace(
                self.data,
                components=components,
                last_push=datetime.now(timezone.utc),
                websocket_connected=True,
            )
        )

    def _extract_component_events(self, event: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract component events from top-level and nested WebSocket payloads."""
        candidates: list[Any] = [event]
        body = event.get("body")
        if isinstance(body, str):
            with contextlib.suppress(json.JSONDecodeError):
                candidates.append(json.loads(body))
        elif isinstance(body, (dict, list)):
            candidates.append(body)

        extracted: list[dict[str, Any]] = []
        for candidate in candidates:
            extracted.extend(self._normalize_component_payload(candidate))
        return extracted

    def _normalize_component_payload(self, payload: Any) -> list[dict[str, Any]]:
        """Normalize known WebSocket payload shapes into a flat list of updates."""
        if isinstance(payload, list):
            result: list[dict[str, Any]] = []
            for item in payload:
                result.extend(self._normalize_component_payload(item))
            return result

        if not isinstance(payload, dict):
            return []

        nested_items: list[dict[str, Any]] = []
        for key in ("records", "components", "data", "items"):
            value = payload.get(key)
            if isinstance(value, list):
                for item in value:
                    nested_items.extend(self._normalize_component_payload(item))
            elif isinstance(value, dict):
                nested_items.extend(self._normalize_component_payload(value))

        if nested_items:
            return nested_items

        return [payload]

    def _set_websocket_connected(self, connected: bool) -> None:
        """Update the connection status in the cached state."""
        if self.data is None or self.data.websocket_connected == connected:
            return

        self.async_set_updated_data(replace(self.data, websocket_connected=connected))

    def get_component_value(self, component_id: int, default: Any = None) -> Any:
        """Return a raw reported component value."""
        if self.data is None:
            return default
        component = self.data.components.get(component_id)
        if component is None:
            return default
        return component.get("reportedValue", default)

    def get_scaled_component_value(
        self, component_id: int, *, divisor: float = 10.0
    ) -> float | None:
        """Return a scaled numeric value."""
        raw_value = self.get_component_value(component_id)
        if not isinstance(raw_value, (int, float)):
            return None
        return raw_value / divisor

    def get_effective_mode(self) -> int | None:
        """Return the effective mode, falling back to the requested mode."""
        raw_mode = self.get_component_value(COMPONENT_EFFECTIVE_MODE)
        if isinstance(raw_mode, int):
            return raw_mode
        requested_mode = self.get_component_value(COMPONENT_MODE)
        return requested_mode if isinstance(requested_mode, int) else None

    def get_setpoint_bounds(self) -> tuple[float, float]:
        """Return dynamic setpoint bounds reported by the heat pump."""
        min_temp = self.get_component_value(COMPONENT_SETPOINT_MIN)
        max_temp = self.get_component_value(COMPONENT_SETPOINT_MAX)
        if not isinstance(min_temp, (int, float)):
            min_temp = 15
        if not isinstance(max_temp, (int, float)):
            max_temp = 40
        return float(min_temp), float(max_temp)

    async def async_set_power(self, enabled: bool) -> None:
        """Turn the heat pump on or off."""
        await self._async_set_component(COMPONENT_POWER, 1 if enabled else 0)

    async def async_set_mode(self, mode: int) -> None:
        """Set the requested operating mode."""
        await self._async_set_component(COMPONENT_MODE, mode)

    async def async_set_target_temperature(self, temperature_c: float) -> None:
        """Set the target temperature."""
        rounded = round(temperature_c)
        await self._async_set_component(COMPONENT_SETPOINT, int(rounded * 10))

    async def _async_set_component(self, component_id: int, value: int | float) -> None:
        """Write a component, update cache optimistically and refresh."""
        response = await self.api.async_set_component_value(
            self.device_id, component_id, value
        )
        new_value = response.get("reportedValue", response.get("desiredValue", value))
        self._apply_local_component_update(component_id, new_value)
        self.hass.async_create_task(self.async_request_refresh())
        self._schedule_delayed_refresh()

    def _apply_local_component_update(self, component_id: int, value: Any) -> None:
        """Update the local cache right away after a successful write."""
        if self.data is None:
            return

        components = dict(self.data.components)
        component = dict(components.get(component_id, {"id": component_id}))
        component["reportedValue"] = value
        components[component_id] = component

        if component_id == COMPONENT_MODE:
            effective = dict(
                components.get(COMPONENT_EFFECTIVE_MODE, {"id": COMPONENT_EFFECTIVE_MODE})
            )
            effective["reportedValue"] = value
            components[COMPONENT_EFFECTIVE_MODE] = effective

        self.async_set_updated_data(
            replace(
                self.data,
                components=components,
                last_push=datetime.now(timezone.utc),
            )
        )

    def _schedule_delayed_refresh(self, delay_seconds: int = 4) -> None:
        """Refresh shortly after a write to catch cloud-applied values."""
        if self._delayed_refresh_task and not self._delayed_refresh_task.done():
            self._delayed_refresh_task.cancel()
        self._delayed_refresh_task = self.hass.async_create_task(
            self._async_delayed_refresh(delay_seconds)
        )

    async def _async_delayed_refresh(self, delay_seconds: int) -> None:
        """Run a delayed refresh after a write."""
        try:
            await asyncio.sleep(delay_seconds)
            await self.async_request_refresh()
        except asyncio.CancelledError:
            raise
