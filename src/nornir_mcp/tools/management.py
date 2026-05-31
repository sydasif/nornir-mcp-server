"""Netmiko Tools - CLI commands and file operations for network devices."""

import logging
from datetime import datetime, UTC
from pathlib import Path
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from nornir_netmiko.tasks import netmiko_send_config
from pydantic import Field

from ..application import mcp
from ..models import (
    BackupFileInfo,
    BackupResult,
    ErrorResponse,
)
from ..services.runner import execute, GLOBAL_ERROR_HOST
from ..services.napalm import run_napalm_get
from ..services.netmiko import run_netmiko_commands
from ..utils.common import (
    ensure_backup_directory,
    error_response,
    write_config_to_file,
    wrap_task_result,
)
from ..utils.filters import build_filters
from ..utils.security import validate_command

logger = logging.getLogger(__name__)


def _validate_commands(
    commands: list[str], read_only: bool = False
) -> dict[str, Any] | None:
    """Validate a list of commands against security rules.

    Args:
        commands: List of commands to validate
        read_only: Whether to enforce read-only prefixes

    Returns:
        Error response if validation fails, None if all commands are valid
    """
    if not commands:
        return error_response("Command list cannot be empty", code="empty_commands")

    for cmd in commands:
        validation_error = validate_command(cmd, read_only=read_only)
        if validation_error:
            logger.warning(
                "Command validation failed for %r: %s", cmd, validation_error
            )
            return error_response(
                "Command validation failed",
                code="command_validation_failed",
                details={"validation_error": validation_error, "failed_command": cmd},
            )

    return None


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
    filter_name: str | None = None,
    filter_hostname: str | None = None,
    filter_group: str | None = None,
    filter_platform: str | None = None,
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
    validation_error = _validate_commands(commands, read_only=False)
    if validation_error:
        return validation_error

    filters = build_filters(filter_name, filter_hostname, filter_group, filter_platform)

    raw = await execute(
        task=netmiko_send_config,
        filters=filters,
        config_commands=commands,
    )

    if GLOBAL_ERROR_HOST in raw:
        return raw

    return wrap_task_result(raw)


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
    filter_name: str | None = None,
    filter_hostname: str | None = None,
    filter_group: str | None = None,
    filter_platform: str | None = None,
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
    # 1. Setup backup directory FIRST to avoid wasted network I/O
    try:
        backup_path = ensure_backup_directory(path)
    except ValueError as e:
        return error_response(str(e), code="security_error")

    filters = build_filters(filter_name, filter_hostname, filter_group, filter_platform)

    # 2. Get configurations
    result = await run_napalm_get(
        getters=["config"],
        filters=filters,
        getters_options={"config": {"retrieve": "running"}},
    )

    # 3. Guard against global errors (e.g., inventory not found)
    if GLOBAL_ERROR_HOST in result:
        return result

    # Process results with guard clauses
    hosts: dict[str, BackupFileInfo | ErrorResponse] = {}
    for hostname, data in result.items():
        # Guard 1: Check for task execution errors
        if isinstance(data, dict) and not data.get("success", True):
            error_info = data.get("error", {})
            hosts[hostname] = ErrorResponse(
                code=error_info.get("code", "backup_failed"),
                message=error_info.get("message", "Backup task failed"),
                details=error_info.get("details"),
            )
            continue

        # Guard 2: Extract config from output
        output = data.get("output", {}) if isinstance(data, dict) else {}
        config_data = output.get("config", {})
        config = config_data.get("running", "") if isinstance(config_data, dict) else ""

        if not config:
            hosts[hostname] = ErrorResponse(
                code="no_config",
                message="No config data returned",
            )
            continue

        # Success case
        file_path_str = write_config_to_file(hostname, config, backup_path)
        file_path = Path(file_path_str)
        hosts[hostname] = BackupFileInfo(
            path=str(file_path),
            size_bytes=file_path.stat().st_size,
            written_at=datetime.now(UTC).isoformat(),
        )

    return BackupResult(hosts=hosts).model_dump(exclude_none=True)


@mcp.tool(
    name="show_commands",
    annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=True),
    tags={"management"},
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
    validation_error = _validate_commands(commands, read_only=True)
    if validation_error:
        return validation_error

    filters = build_filters(filter_name, filter_hostname, filter_group, filter_platform)

    raw = await run_netmiko_commands(
        commands=commands,
        filters=filters,
    )

    if GLOBAL_ERROR_HOST in raw:
        return raw

    return wrap_task_result(raw)
