"""Helper functions for simplifying tool implementations."""

from collections.abc import Mapping
from typing import Any

from ..models import DeviceFilters
from ..services.runner import runner


def normalize_device_filters(
    filters: DeviceFilters | None, device_name: str | None = None
) -> DeviceFilters | None:
    """Normalize device_name and filters into a single DeviceFilters object.

    Args:
        filters: DeviceFilters object for multi-device operations
        device_name: Single device name (alternative to filters)

    Returns:
        Normalized DeviceFilters object

    Raises:
        ValueError: If both filters and device_name are specified
    """
    if device_name and filters:
        raise ValueError("Cannot specify both 'filters' and 'device_name'")

    if device_name:
        return DeviceFilters(hostname=device_name)

    return filters


async def napalm_getter(
    getters: list[str],
    filters: DeviceFilters | None = None,
    device_name: str | None = None,
    getters_options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Simplified wrapper for NAPALM getters.

    Args:
        getters: List of NAPALM getters to execute
        filters: DeviceFilters object for multi-device operations
        device_name: Single device name (alternative to filters)
        getters_options: Optional getter-specific options

    Returns:
        Raw NAPALM results dictionary per host
    """
    from nornir_napalm.plugins.tasks import napalm_get

    effective_filters = normalize_device_filters(filters, device_name)

    if getters_options:
        return await runner.execute(
            task=napalm_get,
            filters=effective_filters,
            getters=getters,
            getters_options=getters_options,
        )
    else:
        return await runner.execute(
            task=napalm_get, filters=effective_filters, getters=getters
        )
