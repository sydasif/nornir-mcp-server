"""Nornir MCP Server Netmiko tools.

Provides tools for network device management using Netmiko for flexible command execution.
"""

from nornir_netmiko.tasks import netmiko_send_command

from ..server import get_nr, mcp
from ..utils.filters import filter_devices
from ..utils.formatters import format_command_results


def build_ping_cmd(platform: str, target: str, test_type: str, count: int, vrf: str | None = None) -> str:
    """Build platform-specific ping or traceroute command.

    Args:
        platform: Network device platform (e.g., 'cisco_ios', 'arista_eos', 'juniper_junos')
        target: Target IP address or hostname to ping/traceroute
        test_type: Type of test ('ping' or 'traceroute')
        count: Number of packets to send for ping
        vrf: Optional VRF name for VRF-aware testing

    Returns:
        Formatted command string for the specific platform

    """
    if test_type == "ping":
        if platform == "cisco_ios":
            cmd = f"ping {target} repeat {count}"
            if vrf:
                cmd = f"ping vrf {vrf} {target} repeat {count}"
        elif platform == "cisco_nxos":
            cmd = f"ping {target} count {count}"
            if vrf:
                cmd = f"ping {target} count {count} vrf {vrf}"
        elif platform == "arista_eos":
            cmd = f"ping {target} count {count}"
            if vrf:
                cmd = f"ping vrf {vrf} {target} count {count}"
        elif platform == "juniper_junos":
            cmd = f"ping {target} count {count}"
            if vrf:
                cmd = f"ping {target} routing-instance {vrf} count {count}"
        else:
            # Default to basic ping for other platforms
            cmd = f"ping {target} -c {count}"
    elif platform == "cisco_ios" or platform == "cisco_nxos" or platform == "arista_eos":
        cmd = f"traceroute {target}"
        if vrf:
            cmd = f"traceroute vrf {vrf} {target}"
    elif platform == "juniper_junos":
        cmd = f"traceroute {target}"
        if vrf:
            cmd = f"traceroute routing-instance {vrf} {target}"
    else:
        # Default to basic traceroute for other platforms
        cmd = f"traceroute {target}"

    return cmd


@mcp.tool()
async def run_show_commands(
    devices: str,
    commands: list[str],
    use_textfsm: bool = False,
    use_genie: bool = False,
) -> dict:
    """Execute show/display commands on network devices via SSH.

    Supports automatic platform detection and optional parsing with
    TextFSM or Cisco Genie for structured output.

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
        >>> await run_show_commands("switch-01", ["show ip interface brief"], use_textfsm=True)
        {'show ip interface brief': {'switch-01': {'success': True, 'output': [...]}}}

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
        results[command] = format_command_results(result)

    return results


@mcp.tool()
async def check_connectivity(
    devices: str,
    target: str,
    test_type: str = "ping",
    count: int = 5,
    vrf: str | None = None,
) -> dict:
    """Execute ping or traceroute from network devices to test reachability.

    Automatically formats the correct command based on device platform
    and test type. Supports VRF-aware testing.

    Args:
        devices: Device filter expression (hostname, group, or pattern)
        target: Target IP address or hostname to test connectivity to
        test_type: Type of test to perform ('ping' or 'traceroute')
        count: Number of packets to send for ping tests
        vrf: Optional VRF name for VRF-aware testing

    Returns:
        Dictionary containing connectivity test results for each targeted device

    Example:
        >>> await check_connectivity("router-01", "8.8.8.8")
        {'router-01': {'success': True, 'output': '...'}}
        >>> await check_connectivity("router-01", "8.8.8.8", test_type="traceroute")
        {'router-01': {'success': True, 'output': '...'}}

    """
    nr = get_nr()
    filtered_nr = filter_devices(nr, devices)

    # Build platform-specific command
    def build_ping_command(task):
        """Inner function to build and execute ping command on a device.

        Args:
            task: Nornir task object

        Returns:
            Result of the command execution

        """
        platform = task.host.platform
        cmd = build_ping_cmd(platform, target, test_type, count, vrf)
        return task.run(task=netmiko_send_command, command_string=cmd)

    result = filtered_nr.run(task=build_ping_command)
    return format_command_results(result)
