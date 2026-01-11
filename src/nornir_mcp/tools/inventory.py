"""Nornir MCP Server inventory tools.

Provides tools for querying and managing network device inventory.
"""

from ..server import get_nr, mcp
from ..utils.filters import apply_filters, build_filters_dict


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
    filters = build_filters_dict(
        hostname=hostname,
        group=group,
        platform=platform,
        data_role=data_role,
        data_site=data_site,
    )
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
    groups = {name: {"count": 0, "members": []} for name in nr.inventory.groups}

    for host_name, host in nr.inventory.hosts.items():
        for group in host.groups:
            if group.name in groups:
                groups[group.name]["count"] += 1
                groups[group.name]["members"].append(host_name)

    return {"groups": groups}


@mcp.tool()
async def reset_failed_hosts() -> dict:
    """Clear the 'failed' status from all hosts in the inventory.

    Use this if hosts are being skipped due to previous execution errors.
    This tool provides explicit control over the failed hosts state.

    Returns:
        Dictionary with status and message

    Example:
        >>> await reset_failed_hosts()
        {'status': 'success', 'message': 'Failed hosts state has been cleared for all devices.'}
    """
    nr = get_nr()
    nr.data.reset_failed_hosts()
    return {
        "status": "success",
        "message": "Failed hosts state has been cleared for all devices.",
    }
