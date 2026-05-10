"""Common utilities - error handling, result formatting, and config operations."""

from datetime import datetime
from pathlib import Path
from typing import Any

from nornir.core.task import AggregatedResult


def error_response(message: str, code: str = "error", **details: Any) -> dict[str, Any]:
    """Create a standardized error response dictionary.

    Args:
        message: Human-readable error description
        code: Error code for programmatic handling
        **details: Additional error context information

    Returns:
        Standardized error response dictionary
    """
    payload: dict[str, Any] = {"error": True, "code": code, "message": message}
    if details:
        payload["details"] = details
    return payload


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


def ensure_backup_directory(backup_dir: str | Path) -> Path:
    """Create backup directory if it doesn't exist.

    Args:
        backup_dir: Path to the backup directory to create

    Returns:
        Path object pointing to the backup directory

    Raises:
        ValueError: If the path attempts directory traversal outside CWD
    """
    root_path = Path.cwd().resolve()
    path = Path(backup_dir).expanduser().resolve()

    if not path.is_relative_to(root_path):
        raise ValueError(f"Security Error: Backup directory must be within {root_path}")

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


__all__ = [
    "error_response",
    "format_results",
    "ensure_backup_directory",
    "write_config_to_file",
]
