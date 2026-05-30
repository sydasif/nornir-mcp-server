"""Nornir MCP Server device filtering utilities.

Contains functions to apply filters to Nornir inventory using the F object.
"""

from nornir.core import Nornir
from nornir.core.filter import F

from ..models import DeviceFilters


def build_filters(
    name: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
) -> DeviceFilters | None:
    """Build a DeviceFilters object if any criteria are provided.

    Args:
        name: Filter by device name
        hostname: Filter by hostname
        group: Filter by group
        platform: Filter by platform

    Returns:
        DeviceFilters object or None if no criteria provided
    """
    if not any((name, hostname, group, platform)):
        return None
    return DeviceFilters(name=name, hostname=hostname, group=group, platform=platform)


def apply_filters(nr: Nornir, filters: DeviceFilters | None) -> Nornir:
    """Apply filters to Nornir inventory using the F object.

    If no filters are provided, returns the unfiltered Nornir instance,
    which targets all hosts in the inventory (Nornir's default behavior).

    Args:
        nr: Nornir instance to filter
        filters: DeviceFilters object containing filter criteria

    Returns:
        Filtered Nornir instance (or unfiltered if no filters provided)

    Raises:
        ValueError: If filters result in zero matching hosts
    """
    original_count = len(nr.inventory.hosts)

    if filters is None:
        return nr

    # Apply filters based on the DeviceFilters object
    if filters.name:
        nr = nr.filter(F(name=filters.name))

    if filters.hostname:
        nr = nr.filter(F(name=filters.hostname) | F(hostname=filters.hostname))

    if filters.group:
        nr = nr.filter(F(groups__contains=filters.group))

    if filters.platform:
        nr = nr.filter(F(platform=filters.platform))

    # Validate that filters matched at least one host
    if len(nr.inventory.hosts) == 0:
        raise ValueError(
            f"No devices matched the provided filters. "
            f"Original inventory had {original_count} devices."
        )

    return nr


__all__: list[str] = ["apply_filters", "build_filters"]
