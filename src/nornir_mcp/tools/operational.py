"""Operational Tools - Read-only commands for network devices."""

from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_command

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner

# --- Helper Processors ---


def _merge_interfaces(data: dict) -> dict:
    """Merge interface status and IP data from NAPALM getters.

    Combines interface state information with IP address information into a unified
    data structure for easier consumption.

    Args:
        data: Dictionary containing raw interface data from NAPALM getters

    Returns:
        Dictionary with merged interface data where each interface name contains
        both state and IP information
    """
    for host_data in data.values():
        if not host_data.get("success"):
            continue
        raw = host_data["result"]

        interfaces = raw.get("interfaces", {})
        interfaces_ip = raw.get("interfaces_ip", {})

        merged = {}

        for name in set(interfaces) | set(interfaces_ip):
            merged[name] = {
                "state": interfaces.get(name, {}),
                "ip": interfaces_ip.get(name, {}),
            }

        host_data["result"] = merged
    return data


def _merge_lldp(data: dict) -> dict:
    """Merge LLDP summary and detail information from NAPALM getters.

    Combines LLDP neighbor summary data with detailed neighbor information into a unified
    data structure for easier consumption.

    Args:
        data: Dictionary containing raw LLDP data from NAPALM getters

    Returns:
        Dictionary with merged LLDP data where each interface contains both
        summary and detail information
    """
    for host_data in data.values():
        if not host_data.get("success"):
            continue
        raw = host_data["result"]

        lldp_summary = raw.get("lldp_neighbors", {})
        lldp_detail = raw.get("lldp_neighbors_detail", {})

        merged = {}

        for iface in set(lldp_summary) | set(lldp_detail):
            merged[iface] = {
                "summary": lldp_summary.get(iface, []),
                "detail": lldp_detail.get(iface, {}),
            }

        host_data["result"] = merged
    return data


def _merge_bgp(data: dict) -> dict:
    """Merge BGP neighbor state and address-family details from NAPALM getters.

    Combines BGP neighbor state information with address family details into a unified
    data structure for easier consumption.

    Args:
        data: Dictionary containing raw BGP data from NAPALM getters

    Returns:
        Dictionary with merged BGP data where each neighbor contains both
        state and address family information
    """
    for host_data in data.values():
        if not host_data.get("success"):
            continue
        raw = host_data["result"]

        bgp_state = raw.get("bgp_neighbors", {})
        bgp_detail = raw.get("bgp_neighbors_detail", {})

        merged = {}

        for neighbor_ip in set(bgp_state) | set(bgp_detail):
            merged[neighbor_ip] = {
                "state": bgp_state.get(neighbor_ip, {}),
                "address_families": bgp_detail.get(neighbor_ip, {}),
            }

        host_data["result"] = merged
    return data


# --- Tools ---


@mcp.tool()
async def get_device_facts(filters: DeviceFilters | None = None) -> dict:
    """Retrieve basic device information (Vendor, OS, Uptime).

    Fetches fundamental device facts including vendor, operating system,
    uptime, serial number, and model information.

    Args:
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing device facts for each targeted device
    """
    return await runner.execute(
        task=napalm_get, filters=filters, getters=["facts"], getter_name="facts"
    )


@mcp.tool()
async def get_interfaces_detailed(
    interface: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Retrieve detailed interface statistics and IP addresses.

    Fetches comprehensive interface information including operational state,
    configuration state, speed, duplex, and IP address assignments.

    Args:
        interface: Optional specific interface name to filter results
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing detailed interface information for each targeted device
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["interfaces", "interfaces_ip"],
        processor=_merge_interfaces,
    )

    # Apply optional single-interface filter
    if interface:
        for host_data in result.values():
            if host_data.get("success"):
                merged = host_data["result"]
                host_data["result"] = {
                    k: v for k, v in merged.items() if k == interface
                }

    return result


@mcp.tool()
async def get_lldp_detailed(
    interface: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Return LLDP neighbors with summary and detailed information merged per interface.

    Fetches Link Layer Discovery Protocol (LLDP) information showing neighboring devices
    connected to each interface, with both summary and detailed neighbor information.

    Args:
        interface: Optional specific interface name to filter results
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing LLDP neighbor information for each targeted device
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["lldp_neighbors", "lldp_neighbors_detail"],
        processor=_merge_lldp,
    )

    # Apply optional single-interface filter
    if interface:
        for host_data in result.values():
            if host_data.get("success"):
                merged = host_data["result"]
                host_data["result"] = {
                    k: v for k, v in merged.items() if k == interface
                }

    return result


@mcp.tool()
async def get_device_configs(
    filters: DeviceFilters | None = None,
    source: str = "running",
) -> dict:
    """Retrieve full device configuration text.

    Fetches the complete device configuration from the specified source
    (running, startup, candidate).

    Args:
        filters: DeviceFilters object containing filter criteria to target specific devices
        source: Configuration source to retrieve (default: "running")

    Returns:
        Dictionary containing the device configuration text for each targeted device
    """

    # Custom processor to extract just the text string
    def _extract_config(data: dict) -> dict:
        for hdata in data.values():
            if hdata.get("success"):
                hdata["result"] = hdata["result"].get(source, "")
        return data

    return await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["config"],
        getters_options={"config": {"retrieve": source}},
        getter_name="config",
        processor=_extract_config,
    )


@mcp.tool()
async def run_show_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict:
    """Execute raw CLI show commands via SSH.

    Executes arbitrary show commands on network devices via SSH connection.
    This provides flexibility for commands that may not be covered by other tools.

    Args:
        commands: List of show commands to execute on the devices
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing command output for each command and targeted device

    Raises:
        ValueError: If commands list is empty or contains invalid commands
    """
    if not commands:
        raise ValueError("Commands list cannot be empty")

    if not all(isinstance(cmd, str) and cmd.strip() for cmd in commands):
        raise ValueError("All commands must be non-empty strings")

    results = {}
    for cmd in commands:
        # Re-use runner for each command
        results[cmd] = await runner.execute(
            task=netmiko_send_command,
            filters=filters,
            formatter_key="output",
            command_string=cmd,
        )
    return results


@mcp.tool()
async def get_bgp_detailed(
    neighbor: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Return BGP neighbor state and address-family details merged per neighbor.

    Fetches Border Gateway Protocol (BGP) information including neighbor state,
    established sessions, and address family advertisements.

    Args:
        neighbor: Optional specific neighbor IP address to filter results
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing BGP neighbor information for each targeted device
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["bgp_neighbors", "bgp_neighbors_detail"],
        processor=_merge_bgp,
    )

    # Apply optional single-neighbor filter
    if neighbor:
        for host_data in result.values():
            if host_data.get("success"):
                merged = host_data["result"]
                host_data["result"] = {k: v for k, v in merged.items() if k == neighbor}

    return result
