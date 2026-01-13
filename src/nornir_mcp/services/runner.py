"""Nornir Execution Service."""

import asyncio
from collections.abc import Callable
from typing import Any

from nornir.core.task import Result

from ..application import get_nr
from ..models import DeviceFilters
from ..utils.filters import apply_filters
from ..utils.formatters import format_results


class NornirRunner:
    """Orchestrates Nornir task execution, filtering, and result formatting."""

    async def execute(
        self,
        task: Callable[..., Result],
        filters: DeviceFilters | None = None,
        formatter_key: str = "result",
        getter_name: str | None = None,
        processor: Callable[[dict], dict] | None = None,
        **task_kwargs: Any,
    ) -> dict:
        """
        Standardized execution pipeline.

        1. Gets fresh Nornir instance
        2. Applies Filters
        3. Offloads blocking task to thread
        4. Formats results
        5. (Optional) Post-processes complex data
        """
        # 1. Setup & Filter
        nr = get_nr()
        if filters is None:
            filters = DeviceFilters()

        try:
            nr = apply_filters(nr, filters)
        except ValueError as e:
            return {"error": str(e), "success": False}

        # 2. Execute in Thread (Non-blocking)
        # We pass task_kwargs explicitly to the Nornir task
        result = await asyncio.to_thread(nr.run, task=task, **task_kwargs)

        # 3. Standardize Output
        formatted = format_results(result, key=formatter_key, getter_name=getter_name)

        # 4. Optional Post-Processing (e.g., merging interface data)
        if processor:
            formatted = processor(formatted)

        return formatted


# Singleton instance for easy import
runner = NornirRunner()
