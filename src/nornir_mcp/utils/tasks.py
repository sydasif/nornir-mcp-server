"""Centralized Nornir task imports for consistent access across modules."""

from nornir_napalm.plugins.tasks import napalm_get
from nornir_netmiko.tasks import (
    netmiko_file_transfer,
    netmiko_send_command,
    netmiko_send_config,
)

__all__ = [
    "napalm_get",
    "netmiko_send_command",
    "netmiko_file_transfer",
    "netmiko_send_config",
]
