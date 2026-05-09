"""Shared helpers for NAPALM task execution."""

from collections.abc import Mapping
from typing import Any

from nornir_napalm.plugins.tasks import napalm_get

from ..models import DeviceFilters
from .runner import execute


async def run_napalm_get(
    getters: list[str],
    filters: DeviceFilters | None = None,
    getters_options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute one or more NAPALM getters via the shared runner."""
    task_kwargs: dict[str, Any] = {"getters": getters}
    if getters_options is not None:
        task_kwargs["getters_options"] = getters_options

    return await execute(
        task=napalm_get,
        filters=filters,
        **task_kwargs,
    )


__all__ = ["run_napalm_get"]
