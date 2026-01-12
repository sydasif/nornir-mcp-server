"""Nornir MCP Server NAPALM tools."""

from nornir_napalm.plugins.tasks import napalm_get

from ..server import get_nr, mcp
from ..utils.config import process_config_request
from ..utils.filters import apply_filters, build_filters_dict
from ..utils.formatters import format_results


@mcp.tool()
async def get_device_facts(
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Retrieve basic device information including vendor, model, OS version, uptime, serial number, and hostname.

    If no filters are provided, retrieves facts from all devices in the inventory.

    Args:
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing device facts for each targeted device
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
async def get_interfaces_detailed(
    interface: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Retrieve interface state and IP information merged per interface.

    Args:
        interface: Optional specific interface name to filter by (e.g., "GigabitEthernet0/0")
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing merged interface state and IP information for each targeted device
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
async def get_lldp_detailed(
    interface: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Return LLDP neighbors with summary and detailed information merged per interface.

    Args:
        interface: Optional specific interface name to filter by (e.g., "GigabitEthernet0/0")
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing merged LLDP summary and detail information for each targeted device
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

    # Run both LLDP getters in one call
    result = nr.run(
        task=napalm_get,
        getters=["lldp_neighbors", "lldp_neighbors_detail"],
    )

    formatted = format_results(result, getter_name=None)

    for _, data in formatted.items():
        if not data.get("success"):
            continue

        raw = data["result"]

        lldp_summary = raw.get("lldp_neighbors", {})
        lldp_detail = raw.get("lldp_neighbors_detail", {})

        merged = {}

        for iface in set(lldp_summary) | set(lldp_detail):
            merged[iface] = {
                "summary": lldp_summary.get(iface, []),
                "detail": lldp_detail.get(iface, {}),
            }

        # Optional single-interface filter
        if interface:
            merged = {k: v for k, v in merged.items() if k == interface}

        data["result"] = merged

    return formatted


@mcp.tool()
async def get_device_configs(
    retrieve: str = "running",
    backup: bool = False,
    backup_directory: str = "./backups",
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Retrieve device configuration (running, startup, or candidate).

    If backup=True, configurations are saved to files instead of returned in the response.

    Args:
        retrieve: Type of configuration to retrieve ('running', 'startup', 'candidate')
        backup: Optional, if `True`, saves configs to files in backup_directory (default: "./backups")
        backup_directory: Optional, directory to store backup files (default: "./backups")
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing device configuration or backup file paths for each targeted device
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

    return await process_config_request(
        nr=nr,
        retrieve=retrieve,
        backup=backup,
        backup_directory=backup_directory,
    )


@mcp.tool()
async def get_bgp_detailed(
    neighbor: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Return BGP neighbor state and address-family details merged per neighbor.

    Args:
        neighbor: Optional specific neighbor IP address to filter by (e.g., "192.0.2.1")
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing merged BGP neighbor state and address-family details for each targeted device
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

    # Run both BGP getters in a single call
    result = nr.run(
        task=napalm_get,
        getters=["bgp_neighbors", "bgp_neighbors_detail"],
    )

    formatted = format_results(result, getter_name=None)

    for _, data in formatted.items():
        if not data.get("success"):
            continue

        raw = data["result"]

        bgp_state = raw.get("bgp_neighbors", {})
        bgp_detail = raw.get("bgp_neighbors_detail", {})

        merged = {}

        for neighbor_ip in set(bgp_state) | set(bgp_detail):
            merged[neighbor_ip] = {
                "state": bgp_state.get(neighbor_ip, {}),
                "address_families": bgp_detail.get(neighbor_ip, {}),
            }

        # Optional single-neighbor filter
        if neighbor:
            merged = {k: v for k, v in merged.items() if k == neighbor}

        data["result"] = merged

    return formatted
