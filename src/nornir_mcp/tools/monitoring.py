"""NAPALM Tools - Structured data retrieval from network devices."""

import logging
from collections.abc import Mapping
from typing import Any

from ..application import mcp
from ..models import DeviceFilters
from ..utils.helpers import napalm_getter

logger = logging.getLogger(__name__)

# --- Tools ---


@mcp.tool()
async def get_device_facts(filters: DeviceFilters | None = None) -> dict[str, Any]:
    """Retrieve basic device information (Vendor, OS, Uptime).

    Args:
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM facts dictionary per host.
    """
    return await napalm_getter(getters=["facts"], filters=filters)


@mcp.tool()
async def get_device_configs(
    filters: DeviceFilters | None = None,
    source: str = "running",
) -> dict[str, Any]:
    """Retrieve raw device configuration data.

    Args:
        filters: DeviceFilters object containing filter criteria
        source: Configuration source (running, startup, candidate)

    Returns:
        Raw NAPALM config dictionary per host.
    """
    return await napalm_getter(
        getters=["config"],
        filters=filters,
        getters_options={"config": {"retrieve": source}},
    )


@mcp.tool()
async def get_bgp_neighbors(
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
) -> dict[str, Any]:
    """Get BGP neighbor information."""
    return await napalm_getter(
        getters=["bgp_neighbors"],
        filters=filters,
        device_name=device_name,
    )


@mcp.tool()
async def get_interfaces(
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
) -> dict[str, Any]:
    """Get interface information."""
    return await napalm_getter(
        getters=["interfaces"],
        filters=filters,
        device_name=device_name,
    )


@mcp.tool()
async def get_interfaces_ip(
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
) -> dict[str, Any]:
    """Get interface IP information."""
    return await napalm_getter(
        getters=["interfaces_ip"],
        filters=filters,
        device_name=device_name,
    )


@mcp.tool()
async def run_napalm_getter(
    getters: list[str],
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
    getters_options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute one or more NAPALM getters on network devices.

    Args:
        getters: List of NAPALM getter names (e.g., ['facts', 'interfaces', 'arp_table'])
        filters: DeviceFilters for multi-device operations
        device_name: Single device name (alternative to filters)
        getters_options: Optional getter-specific options

    Returns:
        Structured NAPALM data per host
    """
    return await napalm_getter(
        getters=getters,
        filters=filters,
        device_name=device_name,
        getters_options=getters_options,
    )
