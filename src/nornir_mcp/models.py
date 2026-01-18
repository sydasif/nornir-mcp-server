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


# --- Pydantic Models for Input Validation ---
class DeviceNameModel(BaseModel):
    device_name: str = Field(
        ..., description="The unique device name as defined in the Nornir inventory."
    )


class GetConfigModel(DeviceNameModel):
    retrieve: str = Field(default="running")


class SendCommandModel(DeviceNameModel):
    command: str | None = Field(None)
    commands: list[str] | None = Field(None)


class BGPConfigModel(DeviceNameModel):
    group: str = Field(default="")
    neighbor: str = Field(default="")


class BGPNeighborsDetailModel(DeviceNameModel):
    neighbor_address: str = Field(default="")


class LLDPNeighborsDetailModel(DeviceNameModel):
    interface: str = Field(default="")


class NetworkInstancesModel(DeviceNameModel):
    name: str = Field(default="")


class PingModel(DeviceNameModel):
    destination: str
    source: str = ""
    ttl: int = 255
    timeout: int = 2
    size: int = 100
    count: int = 5
    vrf: str = ""
    source_interface: str = ""


class TracerouteModel(DeviceNameModel):
    destination: str
    source: str = ""
    ttl: int = 255
    timeout: int = 2
    vrf: str = ""


# --- Result Models ---
class PingProbe(BaseModel):
    ip_address: str
    rtt: float


class PingSuccess(BaseModel):
    probes_sent: int
    packet_loss: float
    rtt_min: float
    rtt_max: float
    rtt_avg: float
    rtt_stddev: float
    results: list[PingProbe]


class PingResultModel(BaseModel):
    success: PingSuccess | None = None
    error: str | None = None


class TracerouteHop(BaseModel):
    rtt: float
    ip_address: str
    host_name: str | None = None


class TracerouteResultModel(BaseModel):
    success: dict[str, TracerouteHop] | None = None
    error: str | None = None
