"""Nornir MCP Server inventory tools.

Provides tools for querying and managing network device inventory.
"""

from ..server import get_nr, mcp
from ..utils.filters import filter_devices


@mcp.tool()
async def list_devices(filter: str | None = None, details: bool = False) -> dict:
    """Query network inventory with optional filters.

    Returns device names, IPs, platforms, and groups. Use 'details=true'
    for full inventory attributes.

    Args:
        filter: Optional filter expression (hostname, group, or data attribute)
        details: Whether to return full inventory attributes

    Returns:
        Dictionary containing device inventory information

    Example:
        >>> await list_devices()
        {'total_devices': 2, 'devices': [...]}
        >>> await list_devices(filter="role=core")
        {'total_devices': 1, 'devices': [...]}
        >>> await list_devices(filter="router-01", details=True)
        {'total_devices': 1, 'devices': [...]}

    """
    nr = get_nr()
    if filter:
        filtered_nr = filter_devices(nr, filter)
    else:
        filtered_nr = nr

    devices = []
    for host_name, host in filtered_nr.inventory.hosts.items():
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
