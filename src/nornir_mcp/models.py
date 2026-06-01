"""Nornir MCP Server data models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class DeviceFilters(BaseModel):
    """Filter parameters for device selection."""

    name: str | None = Field(None, description="Filter by device name in inventory")
    hostname: str | None = Field(None, description="Filter by specific hostname or IP")
    group: str | None = Field(None, description="Filter by group membership")
    platform: str | None = Field(
        None, description="Filter by platform (e.g., cisco_ios)"
    )


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

    def model_dump_hosts(self) -> dict[str, Any]:
        """Returns the hosts dictionary as a plain dict."""
        return self.model_dump()["hosts"]


class BackupFileInfo(BaseModel):
    """Metadata for a successfully written backup file."""

    model_config = ConfigDict(extra="forbid")

    path: str
    size_bytes: int
    written_at: str
    status: str = "success"


class BackupResult(BaseModel):
    """Aggregated result of a backup run."""

    model_config = ConfigDict(extra="forbid")

    hosts: dict[str, BackupFileInfo | ErrorResponse]


class GroupSummary(BaseModel):
    """Summary of a device group."""

    model_config = ConfigDict(extra="forbid")

    count: int
    members: list[str]


class DeviceSummary(BaseModel):
    """Summary of a single device."""

    model_config = ConfigDict(extra="forbid")

    name: str
    hostname: str | None
    platform: str | None
    groups: list[str]
    data: dict[str, Any] | None = None


class DevicesSummary(BaseModel):
    """Aggregated summary of devices."""

    model_config = ConfigDict(extra="forbid")

    total_devices: int
    devices: list[DeviceSummary]


class GroupsSummary(BaseModel):
    """Aggregated summary of groups."""

    model_config = ConfigDict(extra="forbid")

    groups: dict[str, GroupSummary]


class InventorySummary(BaseModel):
    """Complete inventory summary."""

    model_config = ConfigDict(extra="forbid")

    devices: DevicesSummary | None = None
    groups: GroupsSummary | None = None


__all__: list[str] = [
    "DeviceFilters",
    "ErrorResponse",
    "HostTaskResult",
    "TaskResult",
    "BackupFileInfo",
    "BackupResult",
    "GroupSummary",
    "DeviceSummary",
    "DevicesSummary",
    "GroupsSummary",
    "InventorySummary",
]
