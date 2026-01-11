"""Nornir MCP Server NAPALM tools.

Provides tools for network device management using NAPALM for normalized multi-vendor support.
"""

import re

from nornir_napalm.plugins.tasks import napalm_get

from ..server import get_nr, mcp
from ..utils.filters import apply_filters, build_filters_dict
from ..utils.formatters import format_results


def sanitize_configs(configs):
    """Remove sensitive information from configurations.

    Args:
        configs: Dictionary containing configuration data that may contain sensitive information

    Returns:
        Dictionary with sanitized configuration data with sensitive information removed
    """
    sanitized = {}
    for device, data in configs.items():
        if data.get("success") and data.get("result"):
            config_data = data["result"]

            # Iterate through all config types returned (running, startup, candidate)
            # instead of hardcoding just "running"
            for config_type, config_content in config_data.items():
                if isinstance(config_content, str):
                    # Remove password lines
                    cleaned = re.sub(
                        r"password \S+", "password <removed>", config_content
                    )
                    cleaned = re.sub(r"secret \S+", "secret <removed>", cleaned)
                    config_data[config_type] = cleaned

            sanitized[device] = {"success": True, "result": config_data}
        else:
            sanitized[device] = data
    return sanitized


@mcp.tool()
async def get_facts(
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Retrieve basic device information including vendor, model, OS version, uptime, serial number, and hostname.

    This tool uses NAPALM's get_facts getter which provides normalized
    output across different vendor platforms.

    If no filters are provided, retrieves facts from all devices in the inventory.

    Args:
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing device facts for each targeted device

    Example:
        >>> await get_facts()  # All devices
        {'router-01': {...}, 'router-02': {...}, 'switch-01': {...}}
        >>> await get_facts(hostname="router-01")
        {'router-01': {'success': True, 'result': {...}}}
        >>> await get_facts(group="edge_routers")
        {'router-01': {'success': True, 'result': {...}}, ...}
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

    result = nr.run(task=napalm_get, getters=["facts"])
    return format_results(result, getter_name="facts")


@mcp.tool()
async def get_interfaces(
    interface: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Return interface state and IP information merged per interface."""
    nr = get_nr()
    filters = build_filters_dict(
        hostname=hostname,
        group=group,
        platform=platform,
        data_role=data_role,
        data_site=data_site,
    )
    nr = apply_filters(nr, **filters)

    # Run NAPALM getters in a single call
    result = nr.run(
        task=napalm_get,
        getters=["interfaces", "interfaces_ip"],
    )

    formatted = format_results(result, getter_name=None)

    for _, data in formatted.items():
        if not data.get("success"):
            continue

        raw = data["result"]

        interfaces = raw.get("interfaces", {})
        interfaces_ip = raw.get("interfaces_ip", {})

        merged = {}

        for name in set(interfaces) | set(interfaces_ip):
            merged[name] = {
                "state": interfaces.get(name, {}),
                "ip": interfaces_ip.get(name, {}),
            }

        # Optional single-interface filter
        if interface:
            merged = {k: v for k, v in merged.items() if k == interface}

        data["result"] = merged

    return formatted


@mcp.tool()
async def get_bgp_neighbors(
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Get BGP neighbor status and statistics including state, uptime, remote AS, and prefix counts.

    Args:
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing BGP neighbor information for each targeted device

    Example:
        >>> await get_bgp_neighbors(hostname="router-01")
        {'router-01': {'success': True, 'result': {...}}}
        >>> await get_bgp_neighbors(group="edge_routers")
        {'router-01': {'success': True, 'result': {...}}, ...}
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

    result = nr.run(task=napalm_get, getters=["bgp_neighbors"])
    return format_results(result, getter_name="bgp_neighbors")


@mcp.tool()
async def get_lldp_neighbors(
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Discover network topology via LLDP, showing connected devices and ports for each interface.

    Args:
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing LLDP neighbor information for each targeted device

    Example:
        >>> await get_lldp_neighbors(hostname="switch-01")
        {'switch-01': {'success': True, 'result': {...}}}
        >>> await get_lldp_neighbors(data_role="core")
        {'switch-01': {'success': True, 'result': {...}}, ...}
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

    result = nr.run(task=napalm_get, getters=["lldp_neighbors"])
    return format_results(result, getter_name="lldp_neighbors")


@mcp.tool()
async def get_config(
    retrieve: str = "running",
    sanitized: bool = True,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Retrieve device configuration (running, startup, or candidate). Sensitive information like passwords is removed by default.

    Args:
        retrieve: Type of configuration to retrieve ('running', 'startup', 'candidate')
        sanitized: Whether to remove sensitive information like passwords
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing device configuration for each targeted device

    Example:
        >>> await get_config(hostname="router-01")
        {'router-01': {'success': True, 'result': {...}}}
        >>> await get_config(group="edge_routers", retrieve="startup", sanitized=False)
        {'router-01': {'success': True, 'result': {...}}, ...}
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

    result = nr.run(
        task=napalm_get,
        getters=["config"],
        getters_options={"config": {"retrieve": retrieve}},
    )

    formatted = format_results(result, getter_name="config")

    # Sanitize if requested
    if sanitized:
        formatted = sanitize_configs(formatted)

    return formatted
