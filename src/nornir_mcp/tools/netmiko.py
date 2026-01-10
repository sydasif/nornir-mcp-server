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
    use_textfsm: bool = False,
    use_genie: bool = False,
) -> dict:
    """Execute show/display commands on network devices via SSH.

    Supports automatic platform detection and optional parsing with
    TextFSM or Cisco Genie for structured output. This tool can also be
    used for connectivity checks (ping/traceroute) by providing the
    appropriate command string for the platform.

    Args:
        devices: Device filter expression (hostname, group, or pattern)
        commands: List of show commands to execute
        use_textfsm: Whether to parse output with TextFSM
        use_genie: Whether to parse output with Cisco Genie

    Returns:
        Dictionary containing command output for each targeted device

    Example:
        >>> await run_show_commands("router-01", ["show version"])
        {'show version': {'router-01': {'success': True, 'output': '...'}}}
        >>> await run_show_commands("switch-01", ["ping 8.8.8.8"])
        {'ping 8.8.8.8': {'switch-01': {'success': True, 'output': '...'}}}

    """
    nr = get_nr()
    filtered_nr = filter_devices(nr, devices)

    results = {}
    for command in commands:
        result = filtered_nr.run(
            task=netmiko_send_command,
            command_string=command,
            use_textfsm=use_textfsm,
            use_genie=use_genie,
        )
        results[command] = format_results(result, key="output")

    return results
