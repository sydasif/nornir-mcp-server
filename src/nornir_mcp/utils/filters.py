"""Nornir MCP Server device filtering utilities.

Contains functions to apply filters to Nornir inventory using the F object.
"""

from nornir.core import Nornir
from nornir.core.filter import F


def apply_filters(
    nr: Nornir,
    name: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
) -> Nornir:
    """Apply filters to Nornir inventory using the F object.

    If no filters are provided, returns the unfiltered Nornir instance,
    which targets all hosts in the inventory (Nornir's default behavior).

    Args:
        nr: Nornir instance to filter
        name: Filter by device name
        hostname: Filter by hostname
        group: Filter by group
        platform: Filter by platform

    Returns:
        Filtered Nornir instance (or unfiltered if no filters provided)

    Raises:
        ValueError: If filters result in zero matching hosts
    """
    if not any((name, hostname, group, platform)):
        return nr

    original_count = len(nr.inventory.hosts)

    if name:
        nr = nr.filter(F(name=name))

    if hostname:
        nr = nr.filter(F(name=hostname) | F(hostname=hostname))

    if group:
        nr = nr.filter(F(groups__contains=group))

    if platform:
        nr = nr.filter(F(platform=platform))

    if len(nr.inventory.hosts) == 0:
        raise ValueError(
            f"No devices matched the provided filters. "
            f"Original inventory had {original_count} devices. "
            f"Try calling 'list_network_devices' with query_type='devices' to verify available names and platforms."
        )

    return nr


__all__: list[str] = ["apply_filters"]
