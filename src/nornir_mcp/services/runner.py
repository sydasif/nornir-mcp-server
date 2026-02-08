"""Nornir Execution Service."""

import asyncio
from collections.abc import Callable
from typing import Any

from nornir.core import Nornir
from nornir.core.task import Result

from ..application import get_nr
from ..models import DeviceFilters
from ..utils.filters import apply_filters
from ..utils.formatters import format_results


class NornirRunner:
    """Orchestrates Nornir task execution."""

    async def execute(
        self,
        task: Callable[..., Result],
        filters: DeviceFilters | None = None,
        **task_kwargs: Any,
    ) -> dict[str, Any]:
        """
        Execute a Nornir task and return raw results.

        1. Gets fresh Nornir instance
        2. Applies Filters
        3. Offloads blocking task to thread
        4. Returns raw results dictionary
        """
        # 1. Setup & Filter
        nr = get_nr()
        if filters is not None:
            try:
                nr = apply_filters(nr, filters)
            except ValueError as e:
                return {"error": str(e)}
        # else: no filters provided, use entire inventory (default behavior)

        # 2. Execute in Thread (Non-blocking)
        result = await asyncio.to_thread(nr.run, task=task, **task_kwargs)

        # 3. Standardize Output (Simple extraction)
        return format_results(result)

    def get_nr(self) -> Nornir:
        """Get a fresh Nornir instance for direct use."""
        return get_nr()


# Singleton instance for easy import
runner = NornirRunner()
