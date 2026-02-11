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


def netmiko_send_config_atomic(
    task: Task,
    commands: list[str],
    exit_on_error: bool = True,
) -> Result:
    """Send configuration commands with atomic error handling.

    Sends commands one by one and checks for errors after each.
    If exit_on_error is True (default), stops execution on first error
    and returns partial results with error details.

    Args:
        task: Nornir Task object (provides the connection)
        commands: List of configuration commands to execute
        exit_on_error: If True, stop on first error. If False, continue.

    Returns:
        Result with dict containing:
        - commands: dict of {command: output} for successful commands
        - failed_command: the command that failed (if any)
        - error_output: error message from failed command (if any)
    """
    output: dict[str, Any] = {"commands": {}, "failed_command": None, "error_output": None}

    for i, cmd in enumerate(commands):
        # Send one command at a time with error pattern detection
        result = task.run(
            task=netmiko_send_config,
            config_commands=[cmd],
            error_pattern=r"^%.*",  # Match Cisco error patterns like "% Invalid input"
        )

        # Check if the command failed
        if result[0].failed:
            output["failed_command"] = cmd
            output["error_output"] = str(result[0].exception) if result[0].exception else "Unknown error"
            output["commands_executed"] = i
            output["total_commands"] = len(commands)

            if exit_on_error:
                # Preserve per-command error details in the formatted output.
                return Result(host=task.host, result=output)
        else:
            # Store successful command output
            output["commands"][cmd] = result[0].result

    return Result(host=task.host, result=output)


__all__: list[str] = [
    "netmiko_send_command",
    "netmiko_send_config",
    "netmiko_send_commands",
    "netmiko_send_config_atomic",
]
