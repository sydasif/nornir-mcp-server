"""Common utilities - error handling, result formatting, and config operations."""

import traceback
from datetime import datetime
from pathlib import Path
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
            formatted[host] = res.model_dump(exclude_none=True)
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
            formatted[host] = res.model_dump(exclude_none=True)
        else:
            res = HostTaskResult(success=True, output=multi_result[0].result)
            formatted[host] = res.model_dump(exclude_none=True)

    return formatted


def ensure_backup_directory(backup_dir: str | Path) -> Path:
    """Create backup directory if it doesn't exist.

    Args:
        backup_dir: Path to the backup directory to create

    Returns:
        Path object pointing to the backup directory

    Raises:
        ValueError: If the path attempts directory traversal using '..'
    """
    path_str = str(backup_dir)
    if ".." in path_str:
        raise ValueError(
            "Security Error: Directory traversal using '..' is not allowed."
        )

    path = Path(backup_dir).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def write_config_to_file(hostname: str, content: str, folder: Path) -> str:
    """Write configuration content to a file.

    Args:
        hostname: Device hostname for filename
        content: Configuration content to write
        folder: Directory path to write the file to

    Returns:
        Path to the written file as a string
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{hostname}_{timestamp}.cfg"
    filepath = folder / filename
    filepath.write_text(content, encoding="utf-8")
    return str(filepath)


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


__all__ = [
    "error_response",
    "format_results",
    "wrap_task_result",
    "ensure_backup_directory",
    "write_config_to_file",
]
