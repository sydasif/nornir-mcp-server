"""Nornir MCP Server inventory tools."""

from typing import Any

from mcp.types import ToolAnnotations
from ..application import mcp
from ..models import DeviceFilters
from ..services.inventory import (
    InventoryError,
    get_filtered_nornir,
    get_inventory_summary,
)
from ..utils.common import error_response


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_network_devices(
    query_type: str = "all",
    details: bool = False,
    filter_name: str | None = None,
    filter_hostname: str | None = None,
    filter_group: str | None = None,
    filter_platform: str | None = None,
) -> dict[str, Any]:
    """List network devices and inventory information.

    Consolidated tool that provides flexible access to inventory data including
    devices, groups, or both. Use 'details=true' for full device attributes.

    Args:
        query_type: Type of inventory data to return ("devices", "groups", "all")
        details: Whether to return full inventory attributes (for devices query)
        filter_name: Filter by device name in inventory
        filter_hostname: Filter by specific hostname or IP
        filter_group: Filter by group membership
        filter_platform: Filter by platform (e.g., cisco_ios)

    Returns:
        Dictionary containing inventory data based on query_type
    """
    if query_type not in ("devices", "groups", "all"):
        return error_response(
            f"Invalid query_type '{query_type}'. Must be 'devices', 'groups', or 'all'",
            code="invalid_query_type",
        )

    filters = (
        DeviceFilters(
            name=filter_name,
            hostname=filter_hostname,
            group=filter_group,
            platform=filter_platform,
        )
        if any([filter_name, filter_hostname, filter_group, filter_platform])
        else None
    )

    try:
        nr = get_filtered_nornir(filters)
    except InventoryError as exc:
        return error_response(str(exc), code=exc.code)

    summary = get_inventory_summary(nr, details=details)

    result: dict[str, Any] = {}

    if query_type in ("devices", "all"):
        result["devices"] = summary["devices"]

    if query_type in ("groups", "all"):
        result["groups"] = summary["groups"]

    return result
