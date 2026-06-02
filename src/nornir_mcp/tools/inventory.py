"""Nornir MCP Server inventory tools."""

from typing import Annotated, Any, Literal

from mcp.types import ToolAnnotations
from pydantic import Field

from ..server import mcp
from ..services.inventory import (
    InventoryError,
    get_filtered_nornir,
    get_inventory_summary,
)
from ..utils.results import error_response


@mcp.tool(
    name="list_devices",
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False),
    tags={"inventory"},
)
async def list_network_devices(
    query_type: Annotated[
        Literal["devices", "groups", "all"],
        Field(
            description="Type of inventory data to return ('devices', 'groups', 'all')"
        ),
    ] = "all",
    details: Annotated[
        bool,
        Field(
            description="Whether to return full inventory attributes (for devices query)"
        ),
    ] = False,
    filter_name: Annotated[
        str | None,
        Field(description="Filter by device name in inventory"),
    ] = None,
    filter_hostname: Annotated[
        str | None,
        Field(description="Filter by specific hostname or IP"),
    ] = None,
    filter_group: Annotated[
        str | None,
        Field(description="Filter by group membership"),
    ] = None,
    filter_platform: Annotated[
        str | None,
        Field(description="Filter by platform (e.g., 'cisco_ios', 'arista_eos')"),
    ] = None,
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
        filter_platform: Filter by platform (e.g., 'cisco_ios', 'arista_eos')

    Returns:
        Dictionary containing inventory data based on query_type
    """
    if query_type not in ("devices", "groups", "all"):
        return error_response(
            f"Invalid query_type '{query_type}'. Must be 'devices', 'groups', or 'all'",
            code="invalid_query_type",
        )

    try:
        nr = get_filtered_nornir(
            name=filter_name,
            hostname=filter_hostname,
            group=filter_group,
            platform=filter_platform,
        )
    except InventoryError as exc:
        return error_response(str(exc), code=exc.code)

    summary = get_inventory_summary(nr, details=details, query_type=query_type)
    return summary
