from typing import Any, Literal

from pydantic import BaseModel, Field


class DeviceFilter(BaseModel):
    """Base model for device filtering."""

    devices: str = Field(
        description="Device hostname, comma-separated list, or filter (e.g., 'role=core')"
    )


class NapalmGetterRequest(BaseModel):
    """Request for NAPALM getter operations."""

    devices: str = Field(description="Device filter expression")


class NetmikoCommandRequest(BaseModel):
    """Request for Netmiko command execution."""

    devices: str = Field(description="Device filter expression")
    commands: list[str] = Field(description="List of show commands")
    use_textfsm: bool = Field(default=False, description="Parse with TextFSM")
    use_genie: bool = Field(default=False, description="Parse with Genie")


class ConfigRequest(BaseModel):
    """Request for configuration retrieval."""

    devices: str = Field(description="Device filter expression")
    retrieve: Literal["running", "startup", "candidate"] = Field(
        default="running", description="Which config to retrieve"
    )
    sanitized: bool = Field(default=True, description="Remove sensitive information")


class ConnectivityRequest(BaseModel):
    """Request for connectivity testing."""

    devices: str = Field(description="Device filter expression")
    target: str = Field(description="IP or hostname to test")
    test_type: Literal["ping", "traceroute"] = Field(default="ping")
    count: int = Field(default=5, description="Packet count for ping")
    vrf: str | None = Field(default=None, description="VRF name")


class DeviceResult(BaseModel):
    """Standard device operation result."""

    success: bool
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None


class ToolResponse(BaseModel):
    """Standard tool response format."""

    results: dict[str, DeviceResult]
    summary: str | None = None
