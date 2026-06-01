"""Netmiko Service - CLI execution logic for network devices."""

from typing import Any

from nornir.core.task import Result, Task
from nornir_netmiko.tasks import netmiko_send_command, netmiko_send_config

from ..models import DeviceFilters
from .runner import execute


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


async def run_netmiko_commands(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict[str, Any]:
    """Execute multiple Netmiko commands via the shared runner.

    Args:
        commands: List of CLI commands to execute
        filters: DeviceFilters object containing filter criteria

    Returns:
        Standardized dictionary mapping host to results
    """
    return await execute(
        task=_netmiko_send_commands,
        filters=filters,
        commands=commands,
    )


async def run_netmiko_config(
    commands: list[str],
    filters: DeviceFilters | None = None,
) -> dict[str, Any]:
    """Execute configuration commands via the shared runner.

    Args:
        commands: List of configuration commands to apply
        filters: DeviceFilters object containing filter criteria

    Returns:
        Standardized dictionary mapping host to results
    """
    return await execute(
        task=netmiko_send_config,
        filters=filters,
        config_commands=commands,
    )


__all__ = ["run_netmiko_commands", "run_netmiko_config"]
