"""Result and error response shaping."""

import traceback
from typing import Any

from nornir.core.task import AggregatedResult

from ..models import ErrorResponse, HostTaskResult, TaskResult


def error_response(
    message: str,
    code: str = "error",
    exception: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized error response dictionary.

    Args:
        message: Human-readable error description
        code: Error code for programmatic handling
        exception: Stringified exception
        details: Additional error context information

    Returns:
        Standardized error response dictionary
    """
    return ErrorResponse(
        message=message,
        code=code,
        exception=exception,
        details=details,
    ).model_dump(exclude_none=True)


def format_results(result: AggregatedResult) -> dict[str, Any]:
    """Extract Nornir results into a standardized dictionary format.

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
            res = HostTaskResult(
                success=False,
                error=ErrorResponse(code="empty_result", message="No results returned"),
            )
        elif multi_result.failed:
            exc = next((r.exception for r in multi_result if r.exception), None)
            res = HostTaskResult(
                success=False,
                error=ErrorResponse(
                    code="task_failed",
                    message="Task failed",
                    exception=str(exc) if exc else "Unknown error",
                    details={
                        "traceback": "".join(traceback.format_tb(exc.__traceback__))
                    }
                    if exc
                    else None,
                ),
            )
        else:
            res = HostTaskResult(success=True, output=multi_result[0].result)

        formatted[host] = res.model_dump(exclude_none=True)

    return formatted


def wrap_task_result(raw: dict[str, Any]) -> dict[str, Any]:
    """Wrap raw Nornir results into a standardized TaskResult dictionary.

    Validates each entry against the HostTaskResult schema. The caller must
    guard against GLOBAL_ERROR_HOST entries before calling this function.

    Args:
        raw: Dictionary mapping hostname to raw task results or error responses

    Returns:
        Dictionary with 'hosts' key conforming to TaskResult shape
    """
    return TaskResult(
        hosts={host: HostTaskResult.model_validate(data) for host, data in raw.items()}
    ).model_dump(exclude_none=True)


__all__: list[str] = [
    "error_response",
    "format_results",
    "wrap_task_result",
]
