"""Nornir MCP Server Netmiko tools.

Provides tools for network device management using Netmiko for flexible command execution.
"""

from nornir_netmiko.tasks import netmiko_send_command

from ..server import get_nr, mcp
from ..utils.filters import apply_filters
from ..utils.formatters import format_results


def _build_filters_dict(
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    data_role: str | None = None,
    data_site: str | None = None,
) -> dict:
    """Helper function to build filters dict from individual parameters.

    Args:
        hostname: Optional hostname to filter by
        group: Optional group name to filter by
        platform: Optional platform to filter by
        data_role: Optional role in data to filter by (e.g., "core", "edge")
        data_site: Optional site in data to filter by

    Returns:
        Dictionary of filters to pass to apply_filters
    """
    filters = {}
    if hostname is not None:
        filters["hostname"] = hostname
    if group is not None:
        filters["group"] = group
    if platform is not None:
        filters["platform"] = platform
    if data_role is not None:
        filters["data__role"] = data_role
    if data_site is not None:
        filters["data__site"] = data_site

    return filters


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

    Returns the raw command output. This tool can also be used for
    connectivity checks (ping/traceroute).

    Args:
        commands: List of commands to execute
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
    filters = _build_filters_dict(hostname, group, platform, data_role, data_site)
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
