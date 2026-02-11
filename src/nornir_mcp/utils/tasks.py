"""Centralized Nornir task imports for consistent access across modules."""

from nornir_netmiko.tasks import (
    netmiko_send_command,
    netmiko_send_config,
)

__all__: list[str] = [
    "netmiko_send_command",
    "netmiko_send_config",
]
