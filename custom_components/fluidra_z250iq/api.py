"""Fluidra cloud API client for Z250iQ heat pumps."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from time import monotonic
from typing import Any

from aiohttp import ClientError, ClientResponseError, ClientSession

from .auth import FluidraAuth, FluidraAuthenticationError
from .const import (
    API_REQUEST_MIN_INTERVAL,
    API_ENDPOINT_DEVICE_COMPONENTS,
    API_ENDPOINT_DEVICE_DETAIL,
    API_ENDPOINT_DEVICE_UICONFIG,
    API_ENDPOINT_DEVICES,
    API_ENDPOINT_SET_COMPONENT,
    SUPPORTED_MODEL_HINTS,
    SUPPORTED_SKUS,
)


class FluidraApiError(Exception):
    """Raised on Fluidra API failures."""


class FluidraApiClient:
    """Minimal Fluidra cloud client focused on Z250iQ devices."""

    def __init__(self, session: ClientSession, username: str, password: str) -> None:
        self._session = session
        self._auth = FluidraAuth(username, password)
        self._request_lock = asyncio.Lock()
        self._last_request_monotonic = 0.0

    async def async_get_access_token(self, *, force: bool = False) -> str:
        """Return a valid access token."""
        return await self._auth.async_get_access_token(force=force)

    async def async_get_supported_devices(self) -> list[dict[str, Any]]:
        """Return only supported Z250iQ-like devices."""
        devices = await self.async_get_devices()
        return [device for device in devices if is_supported_device(device)]

    async def async_get_devices(self) -> list[dict[str, Any]]:
        """Return the raw device list."""
        payload = await self._request_json("GET", API_ENDPOINT_DEVICES)
        if isinstance(payload, list):
            return payload
        if isinstance(payload, Mapping) and isinstance(payload.get("data"), list):
            return list(payload["data"])
        raise FluidraApiError("Unexpected devices payload")

    async def async_get_device_detail(self, device_id: str) -> dict[str, Any]:
        """Return one device detail."""
        payload = await self._request_json(
            "GET", API_ENDPOINT_DEVICE_DETAIL.format(device_id=device_id)
        )
        if not isinstance(payload, Mapping):
            raise FluidraApiError("Unexpected device detail payload")
        return dict(payload)

    async def async_get_device_components(
        self, device_id: str
    ) -> dict[int, dict[str, Any]]:
        """Return normalized component data keyed by component id."""
        payload = await self._request_json(
            "GET", API_ENDPOINT_DEVICE_COMPONENTS.format(device_id=device_id)
        )
        components: dict[int, dict[str, Any]] = {}
        raw_components: list[Mapping[str, Any]]
        if isinstance(payload, list):
            raw_components = payload
        elif isinstance(payload, Mapping) and isinstance(payload.get("data"), list):
            raw_components = payload["data"]
        else:
            raise FluidraApiError("Unexpected components payload")

        for component in raw_components:
            component_id = component.get("id")
            if isinstance(component_id, int):
                components[component_id] = dict(component)

        return components

    async def async_get_device_uiconfig(self, device_id: str) -> dict[str, Any]:
        """Return the UI config payload."""
        payload = await self._request_json(
            "GET", API_ENDPOINT_DEVICE_UICONFIG.format(device_id=device_id)
        )
        if not isinstance(payload, Mapping):
            raise FluidraApiError("Unexpected uiconfig payload")
        return dict(payload)

    async def async_set_component_value(
        self, device_id: str, component_id: int, value: int | float | str
    ) -> dict[str, Any]:
        """Write a component value."""
        payload = await self._request_json(
            "PUT",
            API_ENDPOINT_SET_COMPONENT.format(
                device_id=device_id, component_id=component_id
            ),
            json_body={"desiredValue": value},
        )
        if not isinstance(payload, Mapping):
            raise FluidraApiError("Unexpected component write payload")
        return dict(payload)

    async def _request_json(
        self,
        method: str,
        url: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Perform an authenticated JSON request."""
        async with self._request_lock:
            await self._async_wait_for_rate_limit()
            return await self._async_request_json(method, url, json_body=json_body)

    async def _async_wait_for_rate_limit(self) -> None:
        """Space out cloud API calls to avoid short bursts."""
        elapsed = monotonic() - self._last_request_monotonic
        delay = API_REQUEST_MIN_INTERVAL - elapsed
        if delay > 0:
            await asyncio.sleep(delay)
        self._last_request_monotonic = monotonic()

    async def _async_request_json(
        self,
        method: str,
        url: str,
        *,
        json_body: dict[str, Any] | None = None,
    ) -> Any:
        """Perform one authenticated JSON request."""
        try:
            headers = await self._auth.async_get_headers()
            async with self._session.request(
                method, url, headers=headers, json=json_body
            ) as response:
                if response.status == 401:
                    await self._auth.async_get_access_token(force=True)
                    headers = await self._auth.async_get_headers()
                    async with self._session.request(
                        method, url, headers=headers, json=json_body
                    ) as retry_response:
                        retry_response.raise_for_status()
                        return await retry_response.json()

                response.raise_for_status()
                return await response.json()
        except FluidraAuthenticationError:
            raise
        except ClientResponseError as err:
            raise FluidraApiError(
                f"HTTP {err.status} while calling Fluidra API: {url}"
            ) from err
        except ClientError as err:
            raise FluidraApiError(f"Error while calling Fluidra API: {url}") from err


def is_supported_device(device: Mapping[str, Any]) -> bool:
    """Return True for devices that look like a Z250iQ."""
    info = device.get("info", {})
    name = str(device.get("name") or info.get("name") or "").lower()
    family = str(info.get("family") or "").lower()
    thing_type = str(device.get("thingType") or "").lower()
    sku = str(device.get("sku") or "").upper()

    if sku in SUPPORTED_SKUS:
        return True

    haystack = " ".join((name, family, thing_type))
    return any(hint in haystack for hint in SUPPORTED_MODEL_HINTS)


def device_display_name(device: Mapping[str, Any]) -> str:
    """Return the best display name for a device."""
    info = device.get("info", {})
    return str(device.get("name") or info.get("name") or device.get("id") or "Z250iQ")
