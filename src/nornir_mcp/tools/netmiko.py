"""Nornir MCP Server Netmiko tools."""

import asyncio

from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config

from ..models import DeviceFilters
from ..application import get_nr, mcp
from ..utils.filters import apply_filters
from ..utils.formatters import format_results


@mcp.tool()
async def run_show_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict:
    """Execute show/display commands on network devices via SSH.

    Returns the raw command output.

    Args:
        commands: List of commands to execute (e.g., ["show version", "show ip interface brief"])
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary containing command output for each targeted device

    Example:
        >>> await run_show_commands(["show version"], filters=DeviceFilters(hostname="router-01"))
        {'show version': {'router-01': {'success': True, 'output': 'Cisco IOS Software...'}}}
        >>> await run_show_commands(["show ip interface brief"], filters=DeviceFilters(group="edge_routers"))
        {'show ip interface brief': {'router-01': {...}, 'router-02': {...}}}
    """
    nr = get_nr()
    if filters is None:
        filters = DeviceFilters()
    nr = apply_filters(nr, filters)

    results = {}
    for command in commands:
        result = await asyncio.to_thread(
            nr.run,
            task=netmiko_send_command,
            command_string=command,
            # We rely on the LLM to parse the raw text output,
            # removing the need for TextFSM/Genie dependencies.
        )
        results[command] = format_results(result, key="output")

    return results


@mcp.tool()
async def send_config_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict:
    """Send configuration commands to network devices via SSH.

    ⚠️ WARNING: This tool modifies device configuration. Netmiko will automatically enter and exit config mode.


    Args:
        commands: List of commands to execute (e.g., ["router bgp 65000", "neighbor 1.1.1.1 remote-as 65001"])
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary containing the configuration session output for each device

    Example:
        >>> await send_config_commands(["interface Loopback100", "description MCP_ADDED"], filters=DeviceFilters(hostname="router-01"))
    """
    nr = get_nr()
    if filters is None:
        filters = DeviceFilters()
    nr = apply_filters(nr, filters)

    result = await asyncio.to_thread(
        nr.run,
        task=netmiko_send_config,
        config_commands=commands,
    )

    return format_results(result, key="output")
