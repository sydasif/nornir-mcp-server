"""Nornir MCP Server Netmiko tools.

Provides tools for network device management using Netmiko for flexible command execution.
"""

from nornir_netmiko.tasks import netmiko_send_command

from ..server import get_nr, mcp
from ..utils.filters import filter_devices
from ..utils.formatters import format_results


@mcp.tool()
async def run_show_commands(
    devices: str,
    commands: list[str],
) -> dict:
    """Execute show/display commands on network devices via SSH.

    Returns the raw command output. This tool can also be used for
    connectivity checks (ping/traceroute).

    Args:
        devices: Device filter expression (hostname, group, or pattern)
        commands: List of commands to execute

    Returns:
        Dictionary containing command output for each targeted device

    Example:
        >>> await run_show_commands("router-01", ["show version"])
        {'show version': {'router-01': {'success': True, 'output': 'Cisco IOS Software...'}}}

    """
    nr = get_nr()
    filtered_nr = filter_devices(nr, devices)

    results = {}
    for command in commands:
        result = filtered_nr.run(
            task=netmiko_send_command,
            command_string=command,
            # We rely on the LLM to parse the raw text output,
            # removing the need for TextFSM/Genie dependencies.
        )
        results[command] = format_results(result, key="output")

    return results
