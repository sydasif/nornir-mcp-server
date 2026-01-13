"""Nornir MCP Server NAPALM tools."""

import asyncio

from nornir_napalm.plugins.tasks import napalm_get

from ..application import get_nr, mcp
from ..models import DeviceFilters
from ..utils.config import ensure_backup_directory, write_config_to_file
from ..utils.filters import apply_filters
from ..utils.formatters import format_results


@mcp.tool()
async def get_device_facts(
    filters: DeviceFilters | None = None,
) -> dict:
    """Retrieve basic device information including vendor, model, OS version, uptime, serial number, and hostname.

    If no filters are provided, retrieves facts from all devices in the inventory.

    Args:
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary containing device facts for each targeted device
    """
    nr = get_nr()
    if filters is None:
        filters = DeviceFilters()
    nr = apply_filters(nr, filters)

    result = await asyncio.to_thread(nr.run, task=napalm_get, getters=["facts"])
    return format_results(result, getter_name="facts")


@mcp.tool()
async def get_interfaces_detailed(
    interface: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Retrieve interface state and IP information merged per interface.

    Args:
        interface: Optional specific interface name to filter by (e.g., "GigabitEthernet0/0")
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary containing merged interface state and IP information for each targeted device
    """
    nr = get_nr()
    if filters is None:
        filters = DeviceFilters()
    nr = apply_filters(nr, filters)

    # Run NAPALM getters in a single call
    result = await asyncio.to_thread(
        nr.run,
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
    filters: DeviceFilters | None = None,
) -> dict:
    """Return LLDP neighbors with summary and detailed information merged per interface.

    Args:
        interface: Optional specific interface name to filter by (e.g., "GigabitEthernet0/0")
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary containing merged LLDP summary and detail information for each targeted device
    """
    nr = get_nr()
    if filters is None:
        filters = DeviceFilters()
    nr = apply_filters(nr, filters)

    # Run both LLDP getters in one call
    result = await asyncio.to_thread(
        nr.run,
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
    filters: DeviceFilters | None = None,
    source: str = "running",
) -> dict:
    """Read and return device configuration text.

    Args:
        filters: DeviceFilters object containing filter criteria
        source: Type of configuration to retrieve ('running', 'startup', 'candidate')

    Returns:
        Dictionary containing device configuration text for each targeted device
    """
    nr = get_nr()
    if filters is None:
        filters = DeviceFilters()
    nr = apply_filters(nr, filters)

    # Run NAPALM getter to retrieve configuration
    result = await asyncio.to_thread(
        nr.run,
        task=napalm_get,
        getters=["config"],
        getters_options={"config": {"retrieve": source}},
    )

    # Format the results to return config text directly
    formatted = format_results(result, getter_name="config")

    # Extract just the configuration text from the result
    for _hostname, data in formatted.items():
        if data.get("success"):
            config_data = data.get("result", {})
            config_content = config_data.get(source, "")
            data["result"] = config_content

    return formatted


@mcp.tool()
async def backup_device_configs(
    filters: DeviceFilters | None = None,
    path: str = "./backups",
) -> dict:
    """Save device configuration to the local disk.

    Args:
        filters: DeviceFilters object containing filter criteria
        path: Directory path to save backup files (default: "./backups")

    Returns:
        Dictionary containing summary of saved file paths for each targeted device
    """
    nr = get_nr()
    if filters is None:
        filters = DeviceFilters()
    nr = apply_filters(nr, filters)

    # Run NAPALM getter to retrieve configuration
    result = await asyncio.to_thread(
        nr.run,
        task=napalm_get,
        getters=["config"],
        getters_options={"config": {"retrieve": "running"}},
    )

    # Format the results
    formatted = format_results(result, getter_name="config")

    # Validate the backup directory
    backup_path = ensure_backup_directory(path)

    backup_results = {}
    for hostname, data in formatted.items():
        if data.get("success"):
            # Extract the configuration content
            config_data = data.get("result", {})
            config_content = config_data.get("running", "")

            if config_content:
                # Write the configuration to file using helper function
                file_path = write_config_to_file(hostname, config_content, backup_path)

                backup_results[hostname] = {
                    "success": True,
                    "result": f"Configuration backed up to {file_path}",
                }
            else:
                backup_results[hostname] = {
                    "success": False,
                    "result": "No configuration content found to backup",
                }
        else:
            # Pass through the original error
            backup_results[hostname] = data

    return backup_results


@mcp.tool()
async def get_bgp_detailed(
    neighbor: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Return BGP neighbor state and address-family details merged per neighbor.

    Args:
        neighbor: Optional specific neighbor IP address to filter by (e.g., "192.0.2.1")
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary containing merged BGP neighbor state and address-family details for each targeted device
    """
    nr = get_nr()
    if filters is None:
        filters = DeviceFilters()
    nr = apply_filters(nr, filters)

    # Run both BGP getters in a single call
    result = await asyncio.to_thread(
        nr.run,
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
