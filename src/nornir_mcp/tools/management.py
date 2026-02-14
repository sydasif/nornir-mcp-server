"""Netmiko Tools - CLI commands and file operations for network devices."""

import logging
from typing import Any

from nornir.core.task import Result, Task
from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config

from ..application import mcp
from ..models import DeviceFilters
from ..services.runner import runner
from ..utils.common import ensure_backup_directory, error_response, write_config_to_file
from ..utils.security import validate_command

logger = logging.getLogger(__name__)


def _netmiko_send_commands(task: Task, commands: list[str]) -> Result:
    """Send multiple show commands over a single SSH connection.

    Args:
        task: Nornir Task object
        commands: List of show commands to execute

    Returns:
        Result with dict mapping command to output
    """
    output: dict[str, Any] = {}
    for cmd in commands:
        result = task.run(task=netmiko_send_command, command_string=cmd)
        output[cmd] = result[0].result
    return Result(host=task.host, result=output)


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
    result = await runner.execute(
        task=napalm_get,
        filters=filters,
        getters=["config"],
        getters_options={"config": {"retrieve": "running"}},
    )

    try:
        backup_path = ensure_backup_directory(path)
    except ValueError as e:
        return error_response(str(e), code="security_error")

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
        task=_netmiko_send_commands,
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
