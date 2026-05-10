"""Shared inventory loading and filtering helpers."""

from nornir.core import Nornir
from typing import Any

from ..application import get_nornir
from ..models import DeviceFilters
from ..utils.filters import apply_filters


class InventoryError(ValueError):
    """Raised when inventory operations fail."""

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def get_filtered_nornir(filters: DeviceFilters | None = None) -> Nornir:
    """Load Nornir from disk and apply optional inventory filters.

    This helper intentionally reloads ``config.yaml`` and inventory data on every
    call to preserve per-invocation behavior across all MCP tools.
    """
    try:
        nr = get_nornir()
    except Exception as exc:
        raise InventoryError(f"Nornir initialization failed: {exc}", code="config_error") from exc

    try:
        return apply_filters(nr, filters)
    except ValueError as exc:
        raise InventoryError(str(exc), code="filter_error") from exc


def get_inventory_summary(
    nr: Nornir, details: bool = False, query_type: str = "all"
) -> dict[str, Any]:
    """Aggregate device and group information from the Nornir inventory.

    Args:
        nr: Nornir instance
        details: Whether to include full device data
        query_type: Type of summary to generate ("devices", "groups", "all")

    Returns:
        Dictionary containing 'devices' and 'groups' summaries
    """
    result: dict[str, Any] = {}

    # 1. Aggregate Devices - Use nr.inventory.hosts which is the filtered set
    if query_type in ("devices", "all"):
        devices = []
        for host_name, host in nr.inventory.hosts.items():
            device_info = {
                "name": host_name,
                "hostname": host.hostname,
                "platform": host.platform,
                "groups": [g.name for g in host.groups],
            }

            if details:
                device_info["data"] = host.data

            devices.append(device_info)
        result["devices"] = {"total_devices": len(devices), "devices": devices}

    # 2. Aggregate Groups - ONLY for devices in the current filtered set
    if query_type in ("groups", "all"):
        groups = {name: {"count": 0, "members": []} for name in nr.inventory.groups}
        for host_name, host in nr.inventory.hosts.items():
            for group in host.groups:
                if group.name in groups:
                    groups[group.name]["count"] += 1
                    groups[group.name]["members"].append(host_name)

        # Filter out empty groups for a cleaner summary
        filtered_groups = {name: info for name, info in groups.items() if info["count"] > 0}
        result["groups"] = {"groups": filtered_groups}

    return result


__all__ = [
    "InventoryError",
    "get_filtered_nornir",
    "get_inventory_summary",
]
