"""NAPALM Tools - Structured data retrieval from network devices."""

import logging
from collections.abc import Mapping
from typing import Any

from nornir_napalm.plugins.tasks import napalm_get

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner

logger = logging.getLogger(__name__)


async def _run_napalm_getters(
    getters: list[str],
    filters: DeviceFilters | None = None,
    getters_options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute one or more NAPALM getters via the shared runner."""
    kwargs: dict[str, Any] = {"getters": getters}
    if getters_options is not None:
        kwargs["getters_options"] = getters_options

    return await runner.execute(
        task=napalm_get,
        filters=filters,
        **kwargs,
    )


@mcp.tool()
async def get_device_facts(
    filters: DeviceFilters | None = None,
) -> dict[str, Any]:
    """Retrieve basic device information (Vendor, OS, Uptime).

    Args:
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM facts dictionary per host.
    """
    return await _run_napalm_getters(["facts"], filters=filters)


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
    return await _run_napalm_getters(
        ["config"],
        filters=filters,
        getters_options={"config": {"retrieve": source}},
    )


@mcp.tool()
async def get_bgp_neighbors(
    filters: DeviceFilters | None = None,
) -> dict[str, Any]:
    """Get BGP neighbor information.

    Args:
        filters: DeviceFilters object containing filter criteria
    """
    return await _run_napalm_getters(["bgp_neighbors"], filters=filters)


@mcp.tool()
async def get_interfaces(
    filters: DeviceFilters | None = None,
) -> dict[str, Any]:
    """Get interface information.

    Args:
        filters: DeviceFilters object containing filter criteria
    """
    return await _run_napalm_getters(["interfaces"], filters=filters)


@mcp.tool()
async def get_interfaces_ip(
    filters: DeviceFilters | None = None,
) -> dict[str, Any]:
    """Get interface IP information.

    Args:
        filters: DeviceFilters object containing filter criteria
    """
    return await _run_napalm_getters(["interfaces_ip"], filters=filters)


@mcp.tool()
async def run_napalm_getter(
    getters: list[str],
    filters: DeviceFilters | None = None,
    getters_options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute one or more NAPALM getters on network devices.

    Args:
        getters: List of NAPALM getter names (e.g., ['facts', 'interfaces', 'arp_table'])
        filters: DeviceFilters for multi-device operations
        getters_options: Optional getter-specific options

    Returns:
        Structured NAPALM data per host
    """
    return await _run_napalm_getters(
        getters,
        filters=filters,
        getters_options=getters_options,
    )
