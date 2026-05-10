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
    filters: DeviceFilters | None = None,
    getters_options: Mapping[str, Any] | None = None,
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
        filters: DeviceFilters for multi-device operations
        getters_options: Optional getter-specific options

    Returns:
        Structured NAPALM data per host
    """
    return await run_napalm_get(
        getters=getters,
        filters=filters,
        getters_options=getters_options,
    )
