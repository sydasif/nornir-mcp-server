"""Nornir MCP Server result formatters.

Contains functions to format Nornir results into standard response formats.
"""

from typing import Any

from nornir.core.task import AggregatedResult

from .errors import error_response


def format_results(result: AggregatedResult) -> dict[str, Any]:
    """Simple extraction of Nornir results.

    Returns a dictionary mapping hostname to the raw result data.
    If a task failed, the error information is returned instead of the result.

    Args:
        result: The aggregated result from Nornir task execution

    Returns:
        Dictionary {hostname: raw_result_data | error_dict}
    """
    formatted: dict[str, Any] = {}

    for host, multi_result in result.items():
        if not multi_result:
            formatted[host] = error_response(
                "No results returned",
                code="empty_result",
            )
        elif multi_result.failed:
            exc = multi_result[0].exception
            formatted[host] = error_response(
                "Task failed",
                code="task_failed",
                exception=str(exc) if exc else "Unknown error",
                traceback=getattr(exc, "traceback", None),
            )
        else:
            formatted[host] = multi_result[0].result

    return formatted
