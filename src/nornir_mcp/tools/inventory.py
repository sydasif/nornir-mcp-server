"""Nornir MCP Server inventory tools."""

from typing import Any

from ..application import get_nr, mcp
from ..models import DeviceFilters
from ..utils.errors import error_response
from ..utils.filters import apply_filters


@mcp.tool()
async def list_network_devices(
    query_type: str = "all",
    details: bool = False,
    filters: DeviceFilters | None = None,
) -> dict[str, Any]:
    """List network devices and inventory information.

    Consolidated tool that provides flexible access to inventory data including
    devices, groups, or both. Use 'details=true' for full device attributes.

    Args:
        query_type: Type of inventory data to return ("devices", "groups", "all")
        details: Whether to return full inventory attributes (for devices query)
        filters: DeviceFilters object containing filter criteria (applies to devices and all queries)

    Returns:
        Dictionary containing inventory data based on query_type
    """
    if query_type not in ("devices", "groups", "all"):
        return error_response(
            f"Invalid query_type '{query_type}'. Must be 'devices', 'groups', or 'all'",
            code="invalid_query_type",
        )

    nr = get_nr()
    nr = apply_filters(nr, filters)

    result: dict[str, Any] = {}

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

    if query_type in ("groups", "all"):
        groups = {name: {"count": 0, "members": []} for name in nr.inventory.groups}

        for host_name, host in nr.inventory.hosts.items():
            for group in host.groups:
                if group.name in groups:
                    groups[group.name]["count"] += 1
                    groups[group.name]["members"].append(host_name)

        result["groups"] = {"groups": groups}

    return result
