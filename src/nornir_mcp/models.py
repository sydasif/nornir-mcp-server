"""Nornir MCP Server models module.

Contains Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field


class DeviceFilter(BaseModel):
    """Base model for device filtering."""

    devices: str = Field(description="Device hostname, comma-separated list, or filter (e.g., 'role=core')")
