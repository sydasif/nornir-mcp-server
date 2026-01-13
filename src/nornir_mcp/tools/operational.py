"""Operational Tools - Read-only commands for network devices."""

from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_command

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner

# --- Tools ---


@mcp.tool()
async def get_device_facts(filters: DeviceFilters | None = None) -> dict:
    """Retrieve basic device information (Vendor, OS, Uptime).

    Fetches fundamental device facts including vendor, operating system,
    uptime, serial number, and model information directly from NAPALM without processing.

    Args:
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing raw device facts as returned by NAPALM for each targeted device
    """
    return await runner.execute(
        task=napalm_get, filters=filters, getters=["facts"], getter_name="facts"
    )


@mcp.tool()
async def get_interfaces_detailed(
    interface: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Retrieve raw interface statistics and IP addresses from NAPALM.

    Fetches raw interface information including operational state,
    configuration state, speed, duplex, and IP address assignments directly from NAPALM
    without any merging or processing.

    Args:
        interface: Optional specific interface name to filter results
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing raw interface data as returned by NAPALM for each targeted device
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["interfaces", "interfaces_ip"],
    )

    # Apply optional single-interface filter to raw data
    if interface:
        for host_data in result.values():
            if host_data.get("success"):
                raw = host_data["result"]
                filtered_result = {}

                # Extract interfaces and interfaces_ip separately
                interfaces = raw.get("interfaces", {})
                interfaces_ip = raw.get("interfaces_ip", {})

                # Filter both dictionaries for the specific interface
                if interface in interfaces:
                    filtered_result["interfaces"] = {interface: interfaces[interface]}
                if interface in interfaces_ip:
                    filtered_result["interfaces_ip"] = {
                        interface: interfaces_ip[interface]
                    }

                host_data["result"] = filtered_result

    return result


@mcp.tool()
async def get_lldp_detailed(
    interface: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Return raw LLDP neighbors information from NAPALM without merging.

    Fetches raw Link Layer Discovery Protocol (LLDP) information showing neighboring devices
    connected to each interface, with both summary and detailed neighbor information
    returned separately as provided by NAPALM.

    Args:
        interface: Optional specific interface name to filter results
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing raw LLDP neighbor information as returned by NAPALM for each targeted device
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["lldp_neighbors", "lldp_neighbors_detail"],
    )

    # Apply optional single-interface filter to raw data
    if interface:
        for host_data in result.values():
            if host_data.get("success"):
                raw = host_data["result"]
                filtered_result = {}

                # Extract lldp_neighbors and lldp_neighbors_detail separately
                lldp_neighbors = raw.get("lldp_neighbors", {})
                lldp_neighbors_detail = raw.get("lldp_neighbors_detail", {})

                # Filter both dictionaries for the specific interface
                if interface in lldp_neighbors:
                    filtered_result["lldp_neighbors"] = {
                        interface: lldp_neighbors[interface]
                    }
                if interface in lldp_neighbors_detail:
                    filtered_result["lldp_neighbors_detail"] = {
                        interface: lldp_neighbors_detail[interface]
                    }

                host_data["result"] = filtered_result

    return result


@mcp.tool()
async def get_device_configs(
    filters: DeviceFilters | None = None,
    source: str = "running",
) -> dict:
    """Retrieve raw device configuration data from NAPALM.

    Fetches the raw device configuration data from the specified source
    (running, startup, candidate) as returned by NAPALM without any processing.

    Args:
        filters: DeviceFilters object containing filter criteria to target specific devices
        source: Configuration source to retrieve (default: "running")

    Returns:
        Dictionary containing raw configuration data as returned by NAPALM for each targeted device
    """
    return await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["config"],
        getters_options={"config": {"retrieve": source}},
        getter_name="config",
    )


@mcp.tool()
async def run_show_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict:
    """Execute raw CLI show commands via SSH.

    Executes arbitrary show commands on network devices via SSH connection.
    This provides flexibility for commands that may not be covered by other tools.
    Only 'show' commands are allowed to enforce read-only operations.

    Args:
        commands: List of show commands to execute on the devices
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing raw command output as returned by Netmiko for each command and targeted device

    Raises:
        ValueError: If commands list is empty, contains invalid commands, or non-show commands
    """
    if not commands:
        raise ValueError("Commands list cannot be empty")

    if not all(isinstance(cmd, str) and cmd.strip() for cmd in commands):
        raise ValueError("All commands must be non-empty strings")

    # Validate that all commands are show commands for read-only enforcement
    for cmd in commands:
        cmd_lower = cmd.strip().lower()
        if not cmd_lower.startswith("show"):
            raise ValueError(
                f"Only 'show' commands are allowed for read-only operations. Invalid command: '{cmd}'"
            )

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
    """Return raw BGP neighbor information from NAPALM without merging.

    Fetches raw Border Gateway Protocol (BGP) information including neighbor state,
    established sessions, and address family advertisements as provided by NAPALM.

    Args:
        neighbor: Optional specific neighbor IP address to filter results
        filters: DeviceFilters object containing filter criteria to target specific devices

    Returns:
        Dictionary containing raw BGP neighbor information as returned by NAPALM for each targeted device
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["bgp_neighbors", "bgp_neighbors_detail"],
    )

    # Apply optional single-neighbor filter to raw data
    if neighbor:
        for host_data in result.values():
            if host_data.get("success"):
                raw = host_data["result"]
                filtered_result = {}

                # Extract bgp_neighbors and bgp_neighbors_detail separately
                bgp_neighbors = raw.get("bgp_neighbors", {})
                bgp_neighbors_detail = raw.get("bgp_neighbors_detail", {})

                # Filter both dictionaries for the specific neighbor
                if neighbor in bgp_neighbors:
                    filtered_result["bgp_neighbors"] = {
                        neighbor: bgp_neighbors[neighbor]
                    }
                if neighbor in bgp_neighbors_detail:
                    filtered_result["bgp_neighbors_detail"] = {
                        neighbor: bgp_neighbors_detail[neighbor]
                    }

                host_data["result"] = filtered_result

    return result
