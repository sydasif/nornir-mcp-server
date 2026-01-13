"""Nornir MCP Server inventory tools."""

from ..application import get_nr, mcp
from ..models import DeviceFilters
from ..utils.filters import apply_filters


@mcp.tool()
async def list_devices(
    details: bool = False,
    filters: DeviceFilters | None = None,
) -> dict:
    """Query network inventory with optional filters.

    Returns device names, IPs, platforms, and groups.
    Use 'details=true' for full inventory attributes.

    If no filters are provided, returns all devices in the inventory.

    Args:
        details: Whether to return full inventory attributes
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary containing device inventory information
    """
    nr = get_nr()
    if filters is None:
        filters = DeviceFilters()
    nr = apply_filters(nr, filters)

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

    return {"total_devices": len(devices), "devices": devices}


@mcp.tool()
async def list_device_groups() -> dict:
    """List all inventory groups and their member counts.

    Useful for discovering available device groupings like roles,
    sites, or device types.

    Returns:
        Dictionary containing all inventory groups and their member counts
    """
    nr = get_nr()
    groups = {name: {"count": 0, "members": []} for name in nr.inventory.groups}

    for host_name, host in nr.inventory.hosts.items():
        for group in host.groups:
            if group.name in groups:
                groups[group.name]["count"] += 1
                groups[group.name]["members"].append(host_name)

    return {"groups": groups}
