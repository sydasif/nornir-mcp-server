"""Netmiko Tools - CLI commands and file operations for network devices."""

import logging
from typing import Any

from mcp.types import ToolAnnotations
from nornir_netmiko.tasks import netmiko_send_config

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import execute
from ..services.napalm import run_napalm_get
from ..services.netmiko import run_netmiko_commands
from ..utils.common import (
    ensure_backup_directory,
    error_response,
    write_config_to_file,
)
from ..utils.security import validate_command

logger = logging.getLogger(__name__)


def _validate_commands(commands: list[str]) -> dict[str, Any] | None:
    """Validate a list of commands against the security denylist.

    Args:
        commands: List of commands to validate

    Returns:
        Error response if validation fails, None if all commands are valid

    Raises:
        ValueError: If commands list is empty
    """
    if not commands:
        raise ValueError("Command list cannot be empty")

    for cmd in commands:
        validation_error = validate_command(cmd)
        if validation_error:
            logger.warning(
                "Command validation failed for %r: %s", cmd, validation_error
            )
            return error_response(
                "Command validation failed",
                code="command_validation_failed",
                validation_error=validation_error,
                failed_command=cmd,
            )

    return None


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=True, idempotentHint=False
    )
)
async def send_config_commands(
    commands: list[str],
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
        filter_platform: Filter by platform (e.g., cisco_ios)

    Returns:
        Raw output from the configuration execution per host.
    """
    validation_error = _validate_commands(commands)
    if validation_error:
        return validation_error

    filters = (
        DeviceFilters(
            name=filter_name,
            hostname=filter_hostname,
            group=filter_group,
            platform=filter_platform,
        )
        if any([filter_name, filter_hostname, filter_group, filter_platform])
        else None
    )

    return await execute(
        task=netmiko_send_config,
        filters=filters,
        config_commands=commands,
    )


@mcp.tool(
    annotations=ToolAnnotations(
        readOnlyHint=False, destructiveHint=False, idempotentHint=True
    )
)
async def backup_device_configs(
    path: str = "./backups",
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
        filter_platform: Filter by platform (e.g., cisco_ios)

    Returns:
        Summary of saved file paths.
    """
    filters = (
        DeviceFilters(
            name=filter_name,
            hostname=filter_hostname,
            group=filter_group,
            platform=filter_platform,
        )
        if any([filter_name, filter_hostname, filter_group, filter_platform])
        else None
    )

    # Get configurations
    result = await run_napalm_get(
        getters=["config"],
        filters=filters,
        getters_options={"config": {"retrieve": "running"}},
    )

    # Setup backup directory
    try:
        backup_path = ensure_backup_directory(path)
    except ValueError as e:
        return error_response(str(e), code="security_error")

    # Process results - flat structure with guard clauses
    backup_results = {}
    for hostname, data in result.items():
        # Guard 1: Check for task execution errors
        if isinstance(data, dict) and data.get("error"):
            backup_error = error_response(
                "Backup task failed",
                code="backup_failed",
            )
            backup_error["details"] = data
            backup_results[hostname] = backup_error
            continue

        # Guard 2: Extract config safely using chained .get()
        config = (
            data.get("config", {}).get("running", "") if isinstance(data, dict) else ""
        )
        if not config:
            backup_results[hostname] = error_response(
                "Empty or missing configuration",
                code="empty_config",
            )
            continue

        # Success case
        file_path = write_config_to_file(hostname, config, backup_path)
        backup_results[hostname] = {
            "status": "success",
            "path": file_path,
        }

    return backup_results


@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def run_show_commands(
    commands: list[str],
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
        filter_platform: Filter by platform (e.g., cisco_ios)

    Returns:
        Dictionary mapping command -> host -> raw output
    """
    validation_error = _validate_commands(commands)
    if validation_error:
        return validation_error

    filters = (
        DeviceFilters(
            name=filter_name,
            hostname=filter_hostname,
            group=filter_group,
            platform=filter_platform,
        )
        if any([filter_name, filter_hostname, filter_group, filter_platform])
        else None
    )

    raw = await run_netmiko_commands(
        commands=commands,
        filters=filters,
    )

    return raw
