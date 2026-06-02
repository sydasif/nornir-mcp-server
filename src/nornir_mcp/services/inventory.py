"""Shared inventory loading and filtering helpers.

Provides access to the Nornir inventory with optional filter parameters.
Uses Nornir's native inventory summaries (devices, groups) without custom
Pydantic wrappers.
"""

from collections import defaultdict
from pathlib import Path

from nornir import InitNornir
from nornir.core import Nornir

from ..utils.filters import apply_filters


class InventoryError(ValueError):
    """Raised when inventory operations fail."""

    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def _get_nornir() -> Nornir:
    """Initialize and return a Nornir instance from configuration file.

    Looks for ``config.yaml`` in the current working directory.

    Raises:
        ValueError: If no configuration file is found.
    """
    config_file = Path.cwd() / "config.yaml"
    if not config_file.exists():
        raise ValueError(
            "No Nornir config found. Create config.yaml in current directory",
        )
    return InitNornir(config_file=str(config_file))


def get_filtered_nornir(
    name: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
) -> Nornir:
    """Load Nornir from disk and apply optional inventory filters.

    This helper intentionally reloads ``config.yaml`` and inventory data on every
    call to preserve per-invocation behavior across all MCP tools.
    """
    try:
        nr = _get_nornir()
    except Exception as exc:
        raise InventoryError(
            f"Nornir initialization failed: {exc}", code="config_error"
        ) from exc

    try:
        return apply_filters(
            nr, name=name, hostname=hostname, group=group, platform=platform
        )
    except ValueError as exc:
        raise InventoryError(str(exc), code="filter_error") from exc


def get_inventory_summary(
    nr: Nornir, details: bool = False, query_type: str = "all"
) -> dict:
    """Aggregate device and group information from the Nornir inventory.

    Args:
        nr: Nornir instance
        details: Whether to include full device data
        query_type: Type of summary to generate ("devices", "groups", "all")

    Returns:
        Dictionary with 'devices' and/or 'groups' summaries
    """
    result: dict = {}

    if query_type in ("devices", "all"):
        devices = [
            {
                "name": host_name,
                "hostname": host.hostname,
                "platform": host.platform,
                "groups": [g.name for g in host.groups],
                "data": host.data if details else None,
            }
            for host_name, host in nr.inventory.hosts.items()
        ]
        result["devices"] = {"total_devices": len(devices), "devices": devices}

    if query_type in ("groups", "all"):
        groups: dict[str, list[str]] = defaultdict(list)
        for host_name, host in nr.inventory.hosts.items():
            for group in host.groups:
                groups[group.name].append(host_name)

        result["groups"] = {
            "groups": {
                name: {"count": len(members), "members": members}
                for name, members in groups.items()
            }
        }

    return result


__all__ = [
    "InventoryError",
    "get_filtered_nornir",
    "get_inventory_summary",
]
