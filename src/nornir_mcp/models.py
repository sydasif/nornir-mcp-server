"""Nornir MCP Server data models."""

from typing import Any

from pydantic import BaseModel, ConfigDict


class ErrorResponse(BaseModel):
    """Standard error response payload."""

    model_config = ConfigDict(extra="forbid")

    error: bool = True
    code: str
    message: str
    exception: str | None = None
    details: dict[str, Any] | None = None


class HostTaskResult(BaseModel):
    """Result for a single device for a single task."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    output: Any = None
    error: ErrorResponse | None = None


class TaskResult(BaseModel):
    """Aggregated result across all targeted hosts."""

    model_config = ConfigDict(extra="forbid")

    hosts: dict[str, HostTaskResult]


__all__: list[str] = [
    "ErrorResponse",
    "HostTaskResult",
    "TaskResult",
]
