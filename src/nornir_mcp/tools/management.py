"""Netmiko Tools - CLI commands and file operations for network devices."""

import logging
from typing import Any

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner
from ..utils.config import ensure_backup_directory, write_config_to_file
from ..utils.errors import error_response
from ..utils.helpers import napalm_getter
from ..utils.security import get_command_validator
from ..utils.tasks import (
    netmiko_send_commands,
    netmiko_send_config,
)

logger = logging.getLogger(__name__)


def _validate_commands(commands: list[str]) -> dict[str, Any] | None:
    if not commands:
        raise ValueError("Command list cannot be empty")

    validator = get_command_validator()
    for cmd in commands:
        validation_error = validator.validate(cmd)
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


@mcp.tool()
async def send_config_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict[str, Any]:
    """Send configuration commands to network devices.

    Args:
        commands: List of configuration commands
        filters: DeviceFilters object containing filter criteria

    Returns:
        Raw output from the configuration execution per host.
    """
    validation_error = _validate_commands(commands)
    if validation_error:
        return validation_error

    return await runner.execute(
        task=netmiko_send_config,
        filters=filters,
        config_commands=commands,
    )


@mcp.tool()
async def backup_device_configs(
    filters: DeviceFilters | None = None,
    path: str = "./backups",
) -> dict[str, Any]:
    """Save device configuration to the local disk.

    Args:
        filters: DeviceFilters object containing filter criteria
        path: Directory path to save backup files

    Returns:
        Summary of saved file paths.
    """
    # 1. Get configurations (Raw NAPALM structure: {'config': {'running': '...'}})
    result = await napalm_getter(
        getters=["config"],
        filters=filters,
        getters_options={"config": {"retrieve": "running"}},
    )

    backup_path = ensure_backup_directory(path)
    backup_results = {}

    for hostname, data in result.items():
        # Check if the host execution failed (data would be an error dict or missing keys)
        if isinstance(data, dict) and "config" in data:
            # Extract config content from raw NAPALM structure
            config_content = data["config"].get("running", "")

            if config_content:
                file_path = write_config_to_file(hostname, config_content, backup_path)
                backup_results[hostname] = {
                    "status": "success",
                    "path": file_path,
                }
            else:
                backup_results[hostname] = error_response(
                    "Empty configuration content",
                    code="empty_config",
                )
        else:
            # Propagate error info found in data
            backup_results[hostname] = error_response(
                "Configuration backup failed",
                code="backup_failed",
                result=data,
            )

    return backup_results


@mcp.tool()
async def run_show_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict[str, Any]:
    """Execute raw CLI show commands via SSH.

    Args:
        commands: List of show commands to execute
        filters: DeviceFilters object containing filter criteria

    Returns:
        Dictionary mapping command -> host -> raw output
    """
    validation_error = _validate_commands(commands)
    if validation_error:
        return validation_error

    raw = await runner.execute(
        task=netmiko_send_commands,
        filters=filters,
        commands=commands,
    )

    results: dict[str, Any] = {cmd: {} for cmd in commands}
    for host, host_data in raw.items():
        if isinstance(host_data, dict) and "error" in host_data:
            for cmd in commands:
                results[cmd][host] = host_data
        else:
            for cmd in commands:
                results[cmd][host] = host_data.get(cmd)

    return results
