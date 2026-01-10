from ..server import mcp, get_nr
from ..utils.filters import filter_devices


@mcp.tool()
async def list_devices(filter: str | None = None, details: bool = False) -> dict:
    """
    Query network inventory with optional filters.

    Returns device names, IPs, platforms, and groups. Use 'details=true'
    for full inventory attributes.

    Filter examples:
    - 'role=core' - devices where data.role is 'core'
    - 'site=dc1' - devices at datacenter 1
    - 'edge_routers' - devices in edge_routers group
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
    """
    List all inventory groups and their member counts.

    Useful for discovering available device groupings like roles,
    sites, or device types.
    """
    nr = get_nr()
    groups = {}
    for group_name, group in nr.inventory.groups.items():
        members = [h.name for h in nr.inventory.hosts.values() if group in h.groups]
        groups[group_name] = {"count": len(members), "members": members}

    return {"groups": groups}
