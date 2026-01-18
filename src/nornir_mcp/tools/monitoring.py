"""Operational Tools - Read-only commands for network devices."""

import logging

from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_command

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner
from ..utils.security import CommandValidator

logger = logging.getLogger(__name__)

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
        getters=["facts"],
    )


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
    # Initialize command validator to prevent dangerous commands
    validator = CommandValidator()

    # Validate each command before execution
    for cmd in commands:
        validation_error = validator.validate(cmd)
        if validation_error:
            logger.warning(f"Command validation failed for '{cmd}': {validation_error}")
            return {
                "error": True,
                "validation_error": validation_error,
                "failed_command": cmd,
            }

    results = {}
    for cmd in commands:
        results[cmd] = await runner.execute(
            task=netmiko_send_command,
            filters=filters,
            command_string=cmd,
        )
    return results


@mcp.tool()
async def get_arp_table(
    filters: DeviceFilters | None = None,
) -> dict:
    """Retrieve the ARP table for network devices.

    Useful for identifying IP-to-MAC mappings and detecting duplicate IPs.

    Args:
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM ARP data per host.
    """
    return await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["arp_table"],
    )


@mcp.tool()
async def get_mac_address_table(
    filters: DeviceFilters | None = None,
    mac_address: str | None = None,
) -> dict:
    """Retrieve the MAC address table (CAM table) for switches.

    Args:
        filters: DeviceFilters object containing filter criteria
        mac_address: Optional specific MAC address to filter results (format: "00:11:22:33:44:55")

    Returns:
        Raw NAPALM MAC table data per host.
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["mac_address_table"],
    )

    # Optional client-side filtering for a specific MAC
    if mac_address:
        for _host, data in result.items():
            if isinstance(data, dict) and "mac_address_table" in data:
                # Filter the list of entries where 'mac' matches
                filtered_entries = [
                    entry
                    for entry in data["mac_address_table"]
                    if entry.get("mac") == mac_address
                ]
                data["mac_address_table"] = filtered_entries

    return result


@mcp.tool()
async def get_routing_table(
    filters: DeviceFilters | None = None,
    vrf: str | None = None,
) -> dict:
    """Retrieve routing information from network devices.

    Args:
        filters: DeviceFilters object containing filter criteria
        vrf: Optional specific VRF to filter results

    Returns:
        Raw NAPALM network_instances data per host containing routing tables.
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["network_instances"],
    )

    if vrf:
        for _host, data in result.items():
            if isinstance(data, dict) and "network_instances" in data:
                if vrf in data["network_instances"]:
                    data["network_instances"] = {vrf: data["network_instances"][vrf]}

    return result


@mcp.tool()
async def get_users(
    filters: DeviceFilters | None = None,
) -> dict:
    """Retrieve user account information from network devices.

    Useful for auditing and managing user accounts.

    Args:
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw NAPALM users data per host.
    """
    return await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["users"],
    )


@mcp.tool()
async def get_vlans(
    filters: DeviceFilters | None = None,
    vlan_id: str | None = None,
) -> dict:
    """Retrieve VLAN configuration details from network devices.

    Args:
        filters: DeviceFilters object containing filter criteria
        vlan_id: Optional specific VLAN ID to filter results

    Returns:
        Raw NAPALM VLANs data per host.
    """
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["vlans"],
    )

    if vlan_id:
        for _host, data in result.items():
            if isinstance(data, dict) and "vlans" in data:
                if vlan_id in data["vlans"]:
                    data["vlans"] = {vlan_id: data["vlans"][vlan_id]}

    return result


@mcp.tool()
async def get_bgp_neighbors(
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
) -> dict:
    """Get BGP neighbor information."""
    if device_name and filters:
        raise ValueError("Cannot specify both 'filters' and 'device_name'")

    effective_filters = filters
    if device_name:
        effective_filters = DeviceFilters(hostname=device_name)

    return await runner.execute(
        task=napalm_get,
        filters=effective_filters,
        getters=["bgp_neighbors"],
    )


@mcp.tool()
async def get_bgp_neighbors_detail(
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
) -> dict:
    """Get detailed BGP neighbor information."""
    if device_name and filters:
        raise ValueError("Cannot specify both 'filters' and 'device_name'")

    effective_filters = filters
    if device_name:
        effective_filters = DeviceFilters(hostname=device_name)

    return await runner.execute(
        task=napalm_get,
        filters=effective_filters,
        getters=["bgp_neighbors_detail"],
    )


@mcp.tool()
async def get_lldp_neighbors(
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
) -> dict:
    """Get LLDP neighbor information."""
    if device_name and filters:
        raise ValueError("Cannot specify both 'filters' and 'device_name'")

    effective_filters = filters
    if device_name:
        effective_filters = DeviceFilters(hostname=device_name)

    return await runner.execute(
        task=napalm_get,
        filters=effective_filters,
        getters=["lldp_neighbors"],
    )


@mcp.tool()
async def get_lldp_neighbors_detail(
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
) -> dict:
    """Get detailed LLDP neighbor information."""
    if device_name and filters:
        raise ValueError("Cannot specify both 'filters' and 'device_name'")

    effective_filters = filters
    if device_name:
        effective_filters = DeviceFilters(hostname=device_name)

    return await runner.execute(
        task=napalm_get,
        filters=effective_filters,
        getters=["lldp_neighbors_detail"],
    )


@mcp.tool()
async def get_interfaces(
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
) -> dict:
    """Get interface information."""
    if device_name and filters:
        raise ValueError("Cannot specify both 'filters' and 'device_name'")

    effective_filters = filters
    if device_name:
        effective_filters = DeviceFilters(hostname=device_name)

    return await runner.execute(
        task=napalm_get,
        filters=effective_filters,
        getters=["interfaces"],
    )


@mcp.tool()
async def get_interfaces_ip(
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
) -> dict:
    """Get interface IP information."""
    if device_name and filters:
        raise ValueError("Cannot specify both 'filters' and 'device_name'")

    effective_filters = filters
    if device_name:
        effective_filters = DeviceFilters(hostname=device_name)

    return await runner.execute(
        task=napalm_get,
        filters=effective_filters,
        getters=["interfaces_ip"],
    )


@mcp.tool()
async def get_bgp_config(
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
    group: str = "",
    neighbor: str = "",
) -> dict:
    """Retrieve BGP configuration from devices.

    Args:
        filters: DeviceFilters for multi-device operations
        device_name: Single device name (alternative to filters)
        group: Optional BGP group to filter
        neighbor: Optional BGP neighbor to filter

    Returns:
        BGP configuration information
    """
    if device_name and filters:
        raise ValueError("Cannot specify both 'filters' and 'device_name'")

    effective_filters = filters
    if device_name:
        effective_filters = DeviceFilters(hostname=device_name)

    return await runner.execute(
        task=napalm_get, filters=effective_filters, getters=["bgp_config"]
    )
