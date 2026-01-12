"""Nornir MCP Server Netmiko tools."""

from nornir_netmiko.tasks import netmiko_send_command

from ..server import get_nr, mcp
from ..utils.filters import apply_filters, build_filters_dict
from ..utils.formatters import format_results


@mcp.tool()
async def run_show_commands(
    commands: list[str],
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Execute show/display commands on network devices via SSH.

    Returns the raw command output.

    Args:
        commands: List of commands to execute (e.g., ["show version", "show ip interface brief"])
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary containing command output for each targeted device

    Example:
        >>> await run_show_commands(["show version"], hostname="router-01")
        {'show version': {'router-01': {'success': True, 'output': 'Cisco IOS Software...'}}}
        >>> await run_show_commands(["show ip interface brief"], group="edge_routers")
        {'show ip interface brief': {'router-01': {...}, 'router-02': {...}}}
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
