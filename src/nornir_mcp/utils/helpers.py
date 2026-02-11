"""Helper functions for simplifying tool implementations."""

from collections.abc import Mapping
from typing import Any

from ..application import get_nr
from ..models import DeviceFilters
from ..services.runner import runner
from ..utils.filters import apply_filters
from .napalm_helpers import validate_getters, get_validation_error_message


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
    timeout: int | None = None,
    skip_validation: bool = False,
) -> dict[str, Any]:
    """Simplified wrapper for NAPALM getters with validation.

    Args:
        getters: List of NAPALM getters to execute
        filters: DeviceFilters object for multi-device operations
        device_name: Single device name (alternative to filters)
        getters_options: Optional getter-specific options
        timeout: Optional timeout in seconds for the operation
        skip_validation: If True, skip getter validation (not recommended)

    Returns:
        Raw NAPALM results dictionary per host, or error dict if validation fails
    """
    from nornir_napalm.plugins.tasks import napalm_get

    effective_filters = normalize_device_filters(filters, device_name)

    # Validate getters for each platform in the filtered inventory
    if not skip_validation and getters:
        nr = get_nr()
        try:
            nr = apply_filters(nr, effective_filters)
        except ValueError:
            # No devices matched, let the actual execution handle this
            pass
        else:
            validation_errors = []
            for host_name, host in nr.inventory.hosts.items():
                platform = host.platform
                if not platform:
                    continue

                valid, invalid = validate_getters(platform, getters)
                if invalid:
                    error_msg = get_validation_error_message(
                        platform, invalid, valid
                    )
                    validation_errors.append({
                        "host": host_name,
                        "platform": platform,
                        "error": error_msg,
                        "unsupported_getters": invalid,
                        "supported_getters": valid,
                    })

            if validation_errors:
                return {
                    "error": True,
                    "code": "unsupported_getters",
                    "message": "Some getters are not supported on target platforms",
                    "validation_errors": validation_errors,
                }

    task_kwargs: dict[str, Any] = {"getters": getters}
    if getters_options is not None:
        task_kwargs["getters_options"] = getters_options

    return await runner.execute(
        task=napalm_get,
        filters=effective_filters,
        timeout=timeout,
        **task_kwargs,
    )


__all__: list[str] = [
    "normalize_device_filters",
    "napalm_getter",
]
