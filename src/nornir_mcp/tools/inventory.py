"""Nornir MCP Server inventory tools.

Provides tools for querying and managing network device inventory.
"""

from ..server import get_nr, mcp
from ..utils.filters import apply_filters


def _build_filters_dict(
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Helper function to build filters dict from individual parameters.

    Args:
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary of filters to pass to apply_filters
    """
    filters = {}
    if hostname is not None:
        filters["hostname"] = hostname
    if group is not None:
        filters["group"] = group
    if platform is not None:
        filters["platform"] = platform
    if data_role is not None:
        filters["data__role"] = data_role
    if data_site is not None:
        filters["data__site"] = data_site

    return filters


@mcp.tool()
async def list_devices(
    details: bool = False,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Query network inventory with optional filters.

    Returns device names, IPs, platforms, and groups. Use 'details=true'
    for full inventory attributes.

    If no filters are provided, returns all devices in the inventory.

    Args:
        details: Whether to return full inventory attributes
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing device inventory information

    Example:
        >>> await list_devices()  # All devices
        {'total_devices': 10, 'devices': [...]}
        >>> await list_devices(group="edge_routers")
        {'total_devices': 3, 'devices': [...]}
        >>> await list_devices(data_role="core")
        {'total_devices': 2, 'devices': [...]}
        >>> await list_devices(hostname="router-01", details=True)
        {'total_devices': 1, 'devices': [...]}
    """
    nr = get_nr()
    filters = _build_filters_dict(hostname, group, platform, data_role, data_site)
    nr = apply_filters(nr, **filters)

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
async def get_device_groups() -> dict:
    """List all inventory groups and their member counts.

    Useful for discovering available device groupings like roles,
    sites, or device types.

    Returns:
        Dictionary containing all inventory groups and their member counts

    Example:
        >>> await get_device_groups()
        {'groups': {'core_routers': {'count': 2, 'members': [...]}}}
    """
    nr = get_nr()
    groups = {}
    for group_name, group in nr.inventory.groups.items():
        members = [h.name for h in nr.inventory.hosts.values() if group in h.groups]
        groups[group_name] = {"count": len(members), "members": members}

    return {"groups": groups}
