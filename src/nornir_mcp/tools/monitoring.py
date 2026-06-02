"""NAPALM Tools - Structured data retrieval from network devices."""

from collections.abc import Mapping
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from nornir.core.task import Result, Task
from nornir_netmiko.tasks import netmiko_send_command
from pydantic import Field

from ..server import mcp
from ..services.napalm import run_napalm_get
from ..services.runner import GLOBAL_ERROR_HOST, execute
from ..utils.common import error_response, wrap_task_result
from ..utils.security import validate_commands


def _netmiko_send_commands(task: Task, commands: list[str]) -> Result:
    """Send multiple show commands over a single SSH connection."""
    output: dict[str, Any] = {}
    for cmd in commands:
        result = task.run(task=netmiko_send_command, command_string=cmd)
        output[cmd] = result[0].result
    return Result(host=task.host, result=output)


@mcp.tool(
    name="fetch_data",
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    tags={"monitoring"},
)
async def get_structured_data(
    getters: Annotated[
        list[str],
        Field(
            description="NAPALM getter names (e.g., ['facts', 'interfaces', 'bgp_neighbors'])"
        ),
    ],
    getters_options: Mapping[str, Any] | None = None,
    filter_name: str | None = None,
    filter_hostname: str | None = None,
    filter_group: str | None = None,
    filter_platform: str | None = None,
) -> dict[str, Any]:
    """Execute one or more NAPALM getters to retrieve structured data from network devices.

    Common available getters:
    - "facts": Basic device information (vendor, model, uptime).
    - "interfaces": Interface status, speed, and error statistics.
    - "interfaces_ip": IP address assignments per interface.
    - "bgp_neighbors": BGP session states and neighbors.
    - "config": Retrieve Running/Startup/Candidate configs.

    Args:
        getters: List of NAPALM getter names (e.g., ['facts', 'interfaces'])
        getters_options: Optional getter-specific options
        filter_name: Filter by device name in inventory
        filter_hostname: Filter by specific hostname or IP
        filter_group: Filter by group membership
        filter_platform: Filter by platform (e.g., 'cisco_ios', 'arista_eos')

    Returns:
        Structured data per host mapping hostname -> result
    """
    result = await run_napalm_get(
        getters=getters,
        name=filter_name,
        hostname=filter_hostname,
        group=filter_group,
        platform=filter_platform,
        getters_options=getters_options,
    )

    if GLOBAL_ERROR_HOST in result:
        return result

    return wrap_task_result(result)


@mcp.tool(
    name="show_commands",
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    tags={"monitoring"},
)
async def run_show_commands(
    commands: Annotated[
        list[str],
        Field(
            description="Show commands to execute (e.g., ['show version', 'show ip interface brief'])"
        ),
    ],
    filter_name: str | None = None,
    filter_hostname: str | None = None,
    filter_group: str | None = None,
    filter_platform: str | None = None,
) -> dict[str, Any]:
    """Execute raw CLI show commands via SSH.

    Args:
        commands: List of show commands to execute
        filter_name: Filter by device name in inventory
        filter_hostname: Filter by specific hostname or IP
        filter_group: Filter by group membership
        filter_platform: Filter by platform (e.g., 'cisco_ios', 'arista_eos')

    Returns:
        Dictionary with 'hosts' key mapping hostname -> task result (success or error).
    """
    if not commands:
        return error_response("Command list cannot be empty", code="empty_commands")

    validation_error = validate_commands(commands, read_only=True)
    if validation_error:
        return error_response(
            "Command validation failed",
            code="command_validation_failed",
            details={"validation_error": validation_error},
        )

    raw = await execute(
        task=_netmiko_send_commands,
        name=filter_name,
        hostname=filter_hostname,
        group=filter_group,
        platform=filter_platform,
        commands=commands,
    )

    if GLOBAL_ERROR_HOST in raw:
        return raw

    return wrap_task_result(raw)
