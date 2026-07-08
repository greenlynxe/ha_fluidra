"""Device profiles for supported Fluidra equipment."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any


DEVICE_TYPE_HEAT_PUMP = "heat_pump"
DEVICE_TYPE_PUMP = "pump"


@dataclass(frozen=True, slots=True)
class FluidraDeviceProfile:
    """Describe one supported Fluidra device family."""

    key: str
    device_type: str
    model_name: str
    identifier_patterns: tuple[str, ...] = ()
    name_patterns: tuple[str, ...] = ()
    family_patterns: tuple[str, ...] = ()
    model_patterns: tuple[str, ...] = ()
    sku_patterns: tuple[str, ...] = ()
    part_number_patterns: tuple[str, ...] = ()
    features: dict[str, Any] = field(default_factory=dict)


Z250IQ_PROFILE = FluidraDeviceProfile(
    key="z250iq",
    device_type=DEVICE_TYPE_HEAT_PUMP,
    model_name="Z250iQ",
    name_patterns=("z250iq", "z250", "z25"),
    family_patterns=("heat pump", "heat pumps"),
    model_patterns=("z250iq", "z250", "z25"),
    sku_patterns=("WH000589",),
)

VICTORIA_SMART_CONNECT_VS_PROFILE = FluidraDeviceProfile(
    key="victoria_smart_connect_vs",
    device_type=DEVICE_TYPE_PUMP,
    model_name="Victoria Smart Connect VS",
    identifier_patterns=("VS200*",),
    name_patterns=("victoria smart connect vs", "vs200", "vs 200"),
    model_patterns=("victoria smart connect vs", "vs200", "vs 200"),
    part_number_patterns=("mppvs",),
    features={
        "speed_control": True,
        "auto_mode": True,
        "schedules": True,
    },
)

SUPPORTED_PROFILES: tuple[FluidraDeviceProfile, ...] = (
    Z250IQ_PROFILE,
    VICTORIA_SMART_CONNECT_VS_PROFILE,
)
PROFILES_BY_KEY = {profile.key: profile for profile in SUPPORTED_PROFILES}


def identify_device_profile(device: Mapping[str, Any]) -> FluidraDeviceProfile | None:
    """Return the best supported profile for a Fluidra API device payload."""
    candidates = _candidate_strings(device)

    for profile in SUPPORTED_PROFILES:
        if _matches_any(candidates["sku"], profile.sku_patterns, exact=True):
            return profile
        if _matches_any(candidates["part_number"], profile.part_number_patterns):
            return profile
        if _matches_any(candidates["identifier"], profile.identifier_patterns):
            return profile
        if _matches_any(candidates["name"], profile.name_patterns):
            return profile
        if _matches_any(candidates["model"], profile.model_patterns):
            return profile
        if _matches_any(candidates["family"], profile.family_patterns):
            if profile.device_type in candidates["type_hint"]:
                return profile

    return None


def is_supported_device(device: Mapping[str, Any]) -> bool:
    """Return True when the payload matches one of the supported profiles."""
    return identify_device_profile(device) is not None


def profile_from_key(profile_key: str | None) -> FluidraDeviceProfile | None:
    """Return a profile by stored key."""
    if profile_key is None:
        return None
    return PROFILES_BY_KEY.get(profile_key)


def _candidate_strings(device: Mapping[str, Any]) -> dict[str, tuple[str, ...] | str]:
    """Extract common identity strings from Fluidra's inconsistent payloads."""
    info = device.get("info")
    if not isinstance(info, Mapping):
        info = {}

    identifiers = (
        device.get("id"),
        device.get("device_id"),
        device.get("serialNumber"),
        device.get("sn"),
        info.get("serialNumber"),
        info.get("sn"),
    )
    names = (
        device.get("name"),
        info.get("name"),
        device.get("label"),
        info.get("label"),
    )
    models = (
        device.get("model"),
        info.get("model"),
        info.get("name"),
        info.get("family"),
        device.get("thingType"),
    )
    families = (
        device.get("family"),
        info.get("family"),
    )
    part_numbers = (
        device.get("partNumber"),
        device.get("partNumbers"),
        device.get("part_numbers"),
        device.get("pn"),
        info.get("partNumber"),
        info.get("partNumbers"),
        info.get("part_numbers"),
        info.get("pn"),
    )
    skus = (device.get("sku"), info.get("sku"))
    type_hint = " ".join(
        _normalize(value)
        for value in (device.get("type"), device.get("deviceType"), device.get("thingType"))
    )

    return {
        "identifier": _normalized_values(identifiers),
        "name": _normalized_values(names),
        "model": _normalized_values(models),
        "family": _normalized_values(families),
        "part_number": _normalized_values(part_numbers),
        "sku": _normalized_values(skus),
        "type_hint": type_hint,
    }


def _normalized_values(values: Iterable[Any]) -> tuple[str, ...]:
    """Normalize non-empty values for matching."""
    return tuple(value for value in (_normalize(item) for item in values) if value)


def _normalize(value: Any) -> str:
    """Normalize a payload value to a lowercase string."""
    return str(value or "").strip().lower()


def _matches_any(
    values: tuple[str, ...] | str,
    patterns: tuple[str, ...],
    *,
    exact: bool = False,
) -> bool:
    """Return True when any value matches any configured pattern."""
    if isinstance(values, str):
        values = (values,)

    for value in values:
        for pattern in patterns:
            normalized_pattern = pattern.strip().lower()
            if not value or not normalized_pattern:
                continue
            if exact and value == normalized_pattern:
                return True
            if normalized_pattern.endswith("*"):
                if value.startswith(normalized_pattern[:-1]):
                    return True
            elif normalized_pattern in value:
                return True
    return False
