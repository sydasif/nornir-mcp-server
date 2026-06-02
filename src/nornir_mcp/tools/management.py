"""Netmiko Tools - CLI commands and file operations for network devices."""

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from mcp.types import ToolAnnotations
from nornir.core.task import Result, Task
from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config
from pydantic import Field

from ..server import mcp
from ..services.napalm import run_napalm_get
from ..services.runner import GLOBAL_ERROR_HOST, execute
from ..utils.common import (
    ensure_backup_directory,
    error_response,
    wrap_task_result,
)
from ..utils.security import validate_commands

logger = logging.getLogger(__name__)


def _netmiko_send_commands(task: Task, commands: list[str]) -> Result:
    """Send multiple show commands over a single SSH connection."""
    output: dict[str, Any] = {}
    for cmd in commands:
        result = task.run(task=netmiko_send_command, command_string=cmd)
        output[cmd] = result[0].result
    return Result(host=task.host, result=output)


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

    try:
        backup_path = ensure_backup_directory(path)
    except ValueError as e:
        return error_response(str(e), code="security_error")

    result = await run_napalm_get(
        getters=["config"],
        name=filter_name,
        hostname=filter_hostname,
        group=filter_group,
        platform=filter_platform,
        getters_options={"config": {"retrieve": "running"}},
    )

    if GLOBAL_ERROR_HOST in result:
        return result

    hosts: dict[str, Any] = {}
    for hostname, data in result.items():
        if isinstance(data, dict) and not data.get("success", True):
            error_info = data.get("error", {})
            hosts[hostname] = {
                "error": True,
                "code": error_info.get("code", "backup_failed"),
                "message": error_info.get("message", "Backup task failed"),
            }
            continue

        output = data.get("output", {}) if isinstance(data, dict) else {}
        config_data = output.get("config", {})
        config = config_data.get("running", "") if isinstance(config_data, dict) else ""

        if not config:
            hosts[hostname] = {
                "error": True,
                "code": "no_config",
                "message": "No config data returned",
            }
            continue

        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        file_path = backup_path / f"{hostname}_{timestamp}.cfg"
        file_path.write_text(config, encoding="utf-8")
        hosts[hostname] = {
            "path": str(file_path),
            "size_bytes": file_path.stat().st_size,
            "written_at": datetime.now(UTC).isoformat(),
            "status": "success",
        }

    return {"hosts": hosts}
