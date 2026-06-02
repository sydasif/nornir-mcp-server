"""Netmiko task helpers."""

from typing import Any

from nornir.core.task import Result, Task
from nornir_netmiko.tasks import netmiko_send_command


def send_commands(task: Task, commands: list[str]) -> Result:
    """Send multiple show commands over a single SSH connection."""
    output: dict[str, Any] = {}
    for cmd in commands:
        result = task.run(task=netmiko_send_command, command_string=cmd)
        output[cmd] = result[0].result
    return Result(host=task.host, result=output)


__all__: list[str] = ["send_commands"]
