"""Nornir MCP Server data models."""

import json
from typing import Any

from pydantic import BaseModel, Field, model_validator


class DeviceFilters(BaseModel):
    """Filter parameters for device selection."""

    hostname: str | None = Field(None, description="Filter by specific hostname or IP")
    group: str | None = Field(None, description="Filter by group membership")
    platform: str | None = Field(
        None, description="Filter by platform (e.g., cisco_ios)"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_to_json(cls, value: Any) -> Any:
        """Parse JSON string if provided."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value
