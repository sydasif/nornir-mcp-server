"""Netmiko Tools - CLI commands and file operations for network devices."""

from typing import Annotated, Any

from mcp.types import ToolAnnotations
from nornir_netmiko.tasks import netmiko_send_config
from pydantic import Field

from ..server import mcp
from ..services.backup import backup_device_configs as run_backup
from ..services.runner import execute
from ..utils.results import error_response, wrap_or_passthrough
from ..utils.security import validate_commands


@mcp.tool(
    name="apply_config",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=True,
        idempotentHint=False,
        openWorldHint=True,
    ),
    tags={"management"},
)
async def send_config_commands(
    commands: Annotated[
        list[str],
        Field(
            description="Configuration commands to apply (e.g., ['int lo0', 'ip addr 10.0.0.1/24'])"
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
    """Send configuration commands to network devices.

    Args:
        commands: List of configuration commands
        filter_name: Filter by device name in inventory
        filter_hostname: Filter by specific hostname or IP
        filter_group: Filter by group membership
        filter_platform: Filter by platform (e.g., 'cisco_ios', 'arista_eos')

    Returns:
        Dictionary with 'hosts' key mapping hostname -> task result (success or error).
    """
    if not commands:
        return error_response("Command list cannot be empty", code="empty_commands")

    validation_error = validate_commands(commands, read_only=False)
    if validation_error:
        return error_response(
            "Command validation failed",
            code="command_validation_failed",
            details={"validation_error": validation_error},
        )

    raw = await execute(
        task=netmiko_send_config,
        name=filter_name,
        hostname=filter_hostname,
        group=filter_group,
        platform=filter_platform,
        config_commands=commands,
    )

    return wrap_or_passthrough(raw)


@mcp.tool(
    name="backup_configs",
    annotations=ToolAnnotations(
        readOnlyHint=False,
        destructiveHint=False,
        idempotentHint=True,
        openWorldHint=True,
    ),
    tags={"management"},
)
async def backup_device_configs(
    path: Annotated[
        str, Field(description="Directory path to save backup files")
    ] = "./backups",
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
    """Save device configuration to the local disk.

    Args:
        path: Directory path to save backup files
        filter_name: Filter by device name in inventory
        filter_hostname: Filter by specific hostname or IP
        filter_group: Filter by group membership
        filter_platform: Filter by platform (e.g., 'cisco_ios', 'arista_eos')

    Returns:
        Summary of saved file paths.
    """
    try:
        return await run_backup(
            path=path,
            name=filter_name,
            hostname=filter_hostname,
            group=filter_group,
            platform=filter_platform,
        )
    except ValueError as exc:
        return error_response(str(exc), code="security_error")
