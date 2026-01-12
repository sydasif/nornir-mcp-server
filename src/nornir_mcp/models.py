"""Nornir MCP Server data models."""

from pydantic import BaseModel, Field


class DeviceFilters(BaseModel):
    """Filter parameters for device selection."""

    hostname: str | None = Field(
        None,
        description="Filter by specific hostname or IP"
    )
    group: str | None = Field(
        None,
        description="Filter by group membership"
    )
    platform: str | None = Field(
        None,
        description="Filter by platform (e.g., cisco_ios)"
    )