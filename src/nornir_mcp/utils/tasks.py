"""Centralized Nornir task imports for consistent access across modules."""

from typing import Any

from nornir.core.task import Result, Task
from nornir_netmiko.tasks import (
    netmiko_send_command,
    netmiko_send_config,
)


def netmiko_send_commands(task: Task, commands: list[str]) -> Result:
    """Send multiple show commands over a single SSH connection.

    Opens one Netmiko connection per device, executes all commands
    sequentially, and returns a dict mapping each command to its output.

    Args:
        task: Nornir Task object (provides the connection)
        commands: List of show commands to execute

    Returns:
        Result with dict {command_string: output_string}
    """
    output: dict[str, Any] = {}
    for cmd in commands:
        result = task.run(task=netmiko_send_command, command_string=cmd)
        output[cmd] = result[0].result
    return Result(host=task.host, result=output)


__all__: list[str] = [
    "netmiko_send_command",
    "netmiko_send_config",
    "netmiko_send_commands",
]
