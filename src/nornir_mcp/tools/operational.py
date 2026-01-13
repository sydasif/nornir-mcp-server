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

    Args:
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM facts dictionary per host.
    """
    return await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["facts"]
    )


@mcp.tool()
async def get_interfaces_detailed(
    interface: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Retrieve raw interface statistics and IP addresses.

    Args:
        interface: Optional specific interface name to filter results
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM interface data per host.
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["interfaces", "interfaces_ip"],
    )

    # Minimal filtering only to reduce token usage if specific interface requested
    if interface:
        for host, data in result.items():
            # Skip failed hosts or unexpected structures
            if not isinstance(data, dict):
                continue

            # Filter 'interfaces' key
            if "interfaces" in data and isinstance(data["interfaces"], dict):
                if interface in data["interfaces"]:
                    data["interfaces"] = {interface: data["interfaces"][interface]}
                else:
                    data["interfaces"] = {}

            # Filter 'interfaces_ip' key
            if "interfaces_ip" in data and isinstance(data["interfaces_ip"], dict):
                if interface in data["interfaces_ip"]:
                    data["interfaces_ip"] = {interface: data["interfaces_ip"][interface]}
                else:
                    data["interfaces_ip"] = {}

    return result


@mcp.tool()
async def get_lldp_detailed(
    interface: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Return raw LLDP neighbors information.

    Args:
        interface: Optional specific interface name to filter results
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM LLDP data per host.
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["lldp_neighbors", "lldp_neighbors_detail"],
    )

    if interface:
        for host, data in result.items():
            if not isinstance(data, dict):
                continue

            if "lldp_neighbors" in data and isinstance(data["lldp_neighbors"], dict):
                if interface in data["lldp_neighbors"]:
                    data["lldp_neighbors"] = {interface: data["lldp_neighbors"][interface]}
                else:
                    data["lldp_neighbors"] = {}

            if "lldp_neighbors_detail" in data and isinstance(data["lldp_neighbors_detail"], dict):
                if interface in data["lldp_neighbors_detail"]:
                    data["lldp_neighbors_detail"] = {interface: data["lldp_neighbors_detail"][interface]}
                else:
                    data["lldp_neighbors_detail"] = {}

    return result


@mcp.tool()
async def get_device_configs(
    filters: DeviceFilters | None = None,
    source: str = "running",
) -> dict:
    """Retrieve raw device configuration data.

    Args:
        filters: DeviceFilters object containing filter criteria
        source: Configuration source (running, startup, candidate)

    Returns:
        Raw NAPALM config dictionary per host.
    """
    return await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["config"],
        getters_options={"config": {"retrieve": source}},
    )


@mcp.tool()
async def run_show_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict:
    """Execute raw CLI show commands via SSH.

    Args:
        commands: List of show commands to execute
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary mapping command -> host -> raw output
    """
    if not commands:
        raise ValueError("Commands list cannot be empty")

    for cmd in commands:
        cmd_lower = cmd.strip().lower()
        if not cmd_lower.startswith("show"):
            raise ValueError(
                f"Only 'show' commands are allowed. Invalid: '{cmd}'"
            )

    results = {}
    for cmd in commands:
        results[cmd] = await runner.execute(
            task=netmiko_send_command,
            filters=filters,
            command_string=cmd,
        )
    return results


@mcp.tool()
async def get_bgp_detailed(
    neighbor: str | None = None,
    filters: DeviceFilters | None = None,
) -> dict:
    """Return raw BGP neighbor information.

    Args:
        neighbor: Optional specific neighbor IP to filter results
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM BGP data per host.
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["bgp_neighbors", "bgp_neighbors_detail"],
    )

    if neighbor:
        for host, data in result.items():
            if not isinstance(data, dict):
                continue

            if "bgp_neighbors" in data and isinstance(data["bgp_neighbors"], dict):
                if neighbor in data["bgp_neighbors"]:
                    data["bgp_neighbors"] = {neighbor: data["bgp_neighbors"][neighbor]}
                else:
                    data["bgp_neighbors"] = {}

            if "bgp_neighbors_detail" in data and isinstance(data["bgp_neighbors_detail"], dict):
                if neighbor in data["bgp_neighbors_detail"]:
                    data["bgp_neighbors_detail"] = {neighbor: data["bgp_neighbors_detail"][neighbor]}
                else:
                    data["bgp_neighbors_detail"] = {}

    return result
