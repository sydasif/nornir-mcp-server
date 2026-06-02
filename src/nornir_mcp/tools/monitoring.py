"""NAPALM Tools - Structured data retrieval from network devices."""

from collections.abc import Mapping
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from pydantic import Field

from ..server import mcp
from ..services.netmiko import send_commands
from ..services.napalm import run_napalm_get
from ..services.runner import execute
from ..utils.results import error_response, wrap_or_passthrough
from ..utils.security import validate_commands


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
    filter_name: Annotated[
        str | None,
        Field(description="Filter by device name in inventory"),
    ] = None,
    filter_hostname: Annotated[
        str | None,
        Field(description="Filter by specific hostname or IP"),
    ] = None,
    filter_group: Annotated[
        str | None,
        Field(description="Filter by group membership"),
    ] = None,
    filter_platform: Annotated[
        str | None,
        Field(description="Filter by platform (e.g., 'cisco_ios', 'arista_eos')"),
    ] = None,
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

    return wrap_or_passthrough(result)


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
    filter_name: Annotated[
        str | None,
        Field(description="Filter by device name in inventory"),
    ] = None,
    filter_hostname: Annotated[
        str | None,
        Field(description="Filter by specific hostname or IP"),
    ] = None,
    filter_group: Annotated[
        str | None,
        Field(description="Filter by group membership"),
    ] = None,
    filter_platform: Annotated[
        str | None,
        Field(description="Filter by platform (e.g., 'cisco_ios', 'arista_eos')"),
    ] = None,
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
        task=send_commands,
        name=filter_name,
        hostname=filter_hostname,
        group=filter_group,
        platform=filter_platform,
        commands=commands,
    )

    return wrap_or_passthrough(raw)
