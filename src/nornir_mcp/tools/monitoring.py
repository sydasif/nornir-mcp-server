"""NAPALM Tools - Structured data retrieval from network devices."""

from collections.abc import Mapping
from typing import Any

from mcp.types import ToolAnnotations
from ..application import mcp
from ..models import DeviceFilters
from ..services.napalm import run_napalm_get


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def run_napalm_getter(
    getters: list[str],
    getters_options: Mapping[str, Any] | None = None,
    filter_name: str | None = None,
    filter_hostname: str | None = None,
    filter_group: str | None = None,
    filter_platform: str | None = None,
) -> dict[str, Any]:
    """Execute one or more NAPALM getters on network devices.

    Common available getters:
    - "facts": Basic device information (vendor, model, uptime).
    - "interfaces": Interface status, speed, and error statistics.
    - "interfaces_ip": IP address assignments per interface.
    - "bgp_neighbors": BGP session states and neighbors.
    - "config": Retrieve Running/Startup/Candidate configs.

    Args:
        getters: List of NAPALM getter names (e.g., ['facts', 'interfaces', 'arp_table'])
        getters_options: Optional getter-specific options
        filter_name: Filter by device name in inventory
        filter_hostname: Filter by specific hostname or IP
        filter_group: Filter by group membership
        filter_platform: Filter by platform (e.g., cisco_ios)

    Returns:
        Structured NAPALM data per host
    """
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

    return await run_napalm_get(
        getters=getters,
        filters=filters,
        getters_options=getters_options,
    )
