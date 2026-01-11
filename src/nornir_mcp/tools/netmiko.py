"""Nornir MCP Server Netmiko tools.

Provides tools for network device management using Netmiko for flexible command execution.
"""

from nornir_netmiko.tasks import netmiko_send_command

from ..server import get_nr, mcp
from ..utils.filters import apply_filters
from ..utils.formatters import format_results


@mcp.tool()
async def run_show_commands(commands: list[str], **filters) -> dict:
    """Execute show/display commands on network devices via SSH.

    Returns the raw command output. This tool can also be used for
    connectivity checks (ping/traceroute).

    Args:
        commands: List of commands to execute
        **filters: Filter criteria (hostname, group, platform, data__role, data__site, etc.)

    Returns:
        Dictionary containing command output for each targeted device

    Example:
        >>> await run_show_commands(["show version"], hostname="router-01")
        {'show version': {'router-01': {'success': True, 'output': 'Cisco IOS Software...'}}}
        >>> await run_show_commands(["show ip interface brief"], group="edge_routers")
        {'show ip interface brief': {'router-01': {...}, 'router-02': {...}}}
    """
    nr = get_nr()
    nr = apply_filters(nr, **filters)

    results = {}
    for command in commands:
        result = nr.run(
            task=netmiko_send_command,
            command_string=command,
            # We rely on the LLM to parse the raw text output,
            # removing the need for TextFSM/Genie dependencies.
        )
        results[command] = format_results(result, key="output")

    return results