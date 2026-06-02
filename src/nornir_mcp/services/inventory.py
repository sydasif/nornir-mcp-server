"""Shared inventory loading and filtering helpers.

Provides access to the Nornir inventory with optional filter parameters.
Uses Nornir's native inventory summaries (devices, groups) without custom
Pydantic wrappers.
"""

from collections import defaultdict
from pathlib import Path
from typing import Any, Literal, TypedDict, cast

from nornir import InitNornir
from nornir.core import Nornir

from ..utils.filters import apply_filters


class InventoryError(ValueError):
    """Raised when inventory operations fail."""

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


class DeviceEntry(TypedDict):
    """One device in the inventory summary."""

    name: str
    hostname: str
    platform: str
    groups: list[str]
    data: dict[str, Any] | None


class DevicesPayload(TypedDict):
    """Top-level devices section of the inventory summary."""

    total_devices: int
    devices: list[DeviceEntry]


class GroupPayload(TypedDict):
    """One group with its member hostnames."""

    count: int
    members: list[str]


class GroupsPayload(TypedDict):
    """All groups keyed by name."""

    groups: dict[str, GroupPayload]


class InventorySummary(TypedDict, total=False):
    """Combined inventory summary; either or both sections may be present."""

    devices: DevicesPayload
    groups: GroupsPayload


def _get_nornir() -> Nornir:
    """Initialize and return a Nornir instance from configuration file.

    Looks for ``config.yaml`` in the current working directory.

    Raises:
        ValueError: If no configuration file is found.
    """
    config_file = Path.cwd() / "config.yaml"
    if not config_file.exists():
        raise ValueError(
            "No Nornir config found. Create config.yaml in current directory",
        )
    return InitNornir(config_file=str(config_file))


def get_filtered_nornir(
    name: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
) -> Nornir:
    """Load Nornir from disk and apply optional inventory filters.

    This helper intentionally reloads ``config.yaml`` and inventory data on every
    call to preserve per-invocation behavior across all MCP tools.
    """
    try:
        nr = _get_nornir()
    except Exception as exc:
        raise InventoryError(
            f"Nornir initialization failed: {exc}", code="config_error"
        ) from exc

    try:
        return apply_filters(
            nr, name=name, hostname=hostname, group=group, platform=platform
        )
    except ValueError as exc:
        raise InventoryError(str(exc), code="filter_error") from exc


def get_inventory_summary(
    nr: Nornir,
    details: bool = False,
    query_type: Literal["devices", "groups", "all"] = "all",
) -> InventorySummary:
    """Aggregate device and group information from the Nornir inventory.

    Args:
        nr: Nornir instance
        details: Whether to include full device data
        query_type: Type of summary to generate ("devices", "groups", "all")

    Returns:
        Dictionary with 'devices' and/or 'groups' summaries
    """
    result: InventorySummary = {}

    if query_type in ("devices", "all"):
        devices: list[DeviceEntry] = cast(
            list[DeviceEntry],
            [
                {
                    "name": host_name,
                    "hostname": host.hostname,
                    "platform": host.platform,
                    "groups": [g.name for g in host.groups],
                    "data": host.data if details else None,
                }
                for host_name, host in nr.inventory.hosts.items()
            ],
        )
        result["devices"] = {"total_devices": len(devices), "devices": devices}

    if query_type in ("groups", "all"):
        groups: dict[str, list[str]] = defaultdict(list)
        for host_name, host in nr.inventory.hosts.items():
            for group in host.groups:
                groups[group.name].append(host_name)

        group_payloads: dict[str, GroupPayload] = {
            name: {"count": len(members), "members": members}
            for name, members in groups.items()
        }
        result["groups"] = {"groups": group_payloads}

    return result


__all__: list[str] = [
    "InventoryError",
    "get_filtered_nornir",
    "get_inventory_summary",
]
