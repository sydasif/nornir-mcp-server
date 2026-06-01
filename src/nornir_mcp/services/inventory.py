"""Shared inventory loading and filtering helpers."""

from collections import defaultdict

from nornir.core import Nornir

from ..application import get_nornir
from ..models import (
    DeviceFilters,
    DevicesSummary,
    DeviceSummary,
    GroupsSummary,
    GroupSummary,
    InventorySummary,
)
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
        raise InventoryError(
            f"Nornir initialization failed: {exc}", code="config_error"
        ) from exc

    try:
        return apply_filters(nr, filters)
    except ValueError as exc:
        raise InventoryError(str(exc), code="filter_error") from exc


def get_inventory_summary(
    nr: Nornir, details: bool = False, query_type: str = "all"
) -> InventorySummary:
    """Aggregate device and group information from the Nornir inventory.

    Args:
        nr: Nornir instance
        details: Whether to include full device data
        query_type: Type of summary to generate ("devices", "groups", "all")

    Returns:
        InventorySummary model containing 'devices' and 'groups' summaries
    """
    devices_summary = None
    groups_summary = None

    # 1. Aggregate Devices - Use nr.inventory.hosts which is the filtered set
    if query_type in ("devices", "all"):
        devices = [
            DeviceSummary(
                name=host_name,
                hostname=host.hostname,
                platform=host.platform,
                groups=[g.name for g in host.groups],
                data=host.data if details else None,
            )
            for host_name, host in nr.inventory.hosts.items()
        ]
        devices_summary = DevicesSummary(total_devices=len(devices), devices=devices)

    # 2. Aggregate Groups - ONLY for devices in the current filtered set
    if query_type in ("groups", "all"):
        groups: dict[str, list[str]] = defaultdict(list)
        for host_name, host in nr.inventory.hosts.items():
            for group in host.groups:
                groups[group.name].append(host_name)

        groups_summary = GroupsSummary(
            groups={
                name: GroupSummary(count=len(members), members=members)
                for name, members in groups.items()
            }
        )

    return InventorySummary(devices=devices_summary, groups=groups_summary)


__all__ = [
    "InventoryError",
    "get_filtered_nornir",
    "get_inventory_summary",
]
