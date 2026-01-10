from nornir_netmiko.tasks import netmiko_send_command

from ..models import ConnectivityRequest, NetmikoCommandRequest
from ..server import mcp, get_nr
from ..utils.filters import filter_devices
from ..utils.formatters import format_command_results


def build_ping_cmd(
    platform: str, target: str, test_type: str, count: int, vrf: str | None = None
) -> str:
    """Build platform-specific ping or traceroute command."""
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
    else:  # traceroute
        if platform == "cisco_ios":
            cmd = f"traceroute {target}"
            if vrf:
                cmd = f"traceroute vrf {vrf} {target}"
        elif platform == "cisco_nxos":
            cmd = f"traceroute {target}"
            if vrf:
                cmd = f"traceroute vrf {vrf} {target}"
        elif platform == "arista_eos":
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
async def run_show_commands(devices: str, commands: list[str], use_textfsm: bool = False, use_genie: bool = False) -> dict:
    """
    Execute show/display commands on network devices via SSH.

    Supports automatic platform detection and optional parsing with
    TextFSM or Cisco Genie for structured output.

    Example commands by platform:
    - Cisco IOS: show ip interface brief, show version
    - Cisco NX-OS: show interface brief, show vpc
    - Arista: show interfaces status, show ip route
    - Juniper: show interfaces terse, show route
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
async def check_connectivity(devices: str, target: str, test_type: str = "ping", count: int = 5, vrf: str | None = None) -> dict:
    """
    Execute ping or traceroute from network devices to test reachability.

    Automatically formats the correct command based on device platform
    and test type. Supports VRF-aware testing.
    """
    nr = get_nr()
    filtered_nr = filter_devices(nr, devices)

    # Build platform-specific command
    def build_ping_command(task):
        platform = task.host.platform
        cmd = build_ping_cmd(
            platform, target, test_type, count, vrf
        )
        return task.run(task=netmiko_send_command, command_string=cmd)

    result = filtered_nr.run(task=build_ping_command)
    return format_command_results(result)
