"""Shared helpers for NAPALM task execution."""

from collections.abc import Mapping
from typing import Any

from nornir_napalm.plugins.tasks import napalm_get

from .runner import execute


async def run_napalm_get(
    getters: list[str],
    name: str | None = None,
    hostname: str | None = None,
    group: str | None = None,
    platform: str | None = None,
    getters_options: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute one or more NAPALM getters via the shared runner."""
    task_kwargs: dict[str, Any] = {"getters": getters} | (
        {"getters_options": getters_options} if getters_options is not None else {}
    )

    return await execute(
        task=napalm_get,
        name=name,
        hostname=hostname,
        group=group,
        platform=platform,
        **task_kwargs,
    )


__all__ = ["run_napalm_get"]
