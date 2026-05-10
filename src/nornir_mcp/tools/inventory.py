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
