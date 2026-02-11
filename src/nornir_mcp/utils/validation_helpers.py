"""Validation helpers and factory functions."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol, get_origin

from pydantic import BaseModel, ValidationError

from ..models import (
    BGPConfigModel,
    BGPNeighborsDetailModel,
    DeviceNameModel,
    GetConfigModel,
    LLDPNeighborsDetailModel,
    NetworkInstancesModel,
    SendCommandModel,
)
from ..utils.errors import error_response

logger = logging.getLogger("nornir-mcp.validation")

# Model map (input + result models)
MODEL_MAP: dict[str, type[BaseModel]] = {
    "DeviceNameModel": DeviceNameModel,
    "GetConfigModel": GetConfigModel,
    "SendCommandModel": SendCommandModel,
    "BGPConfigModel": BGPConfigModel,
    "BGPNeighborsDetailModel": BGPNeighborsDetailModel,
    "LLDPNeighborsDetailModel": LLDPNeighborsDetailModel,
    "NetworkInstancesModel": NetworkInstancesModel,
}


def _example_from_model(cls: type[BaseModel]) -> dict[str, Any]:
    example: dict[str, Any] = {}
    # Pydantic v2: use model_fields and FieldInfo.is_required
    fields = getattr(cls, "model_fields", None)
    if fields is None:
        # fallback for older pydantic versions
        fields = getattr(cls, "__fields__", {})

    for name, field in fields.items():
        # FieldInfo in pydantic v2 exposes `is_required`
        is_required = getattr(field, "is_required", None)
        if is_required is None:
            # pydantic v1 compatibility: Field has 'required'
            is_required = getattr(field, "required", False)

        if is_required:
            ft = getattr(field, "annotation", None) or getattr(
                field, "outer_type_", None
            )
            origin = get_origin(ft)
            if ft is int or (origin is not None and origin is int):
                example[name] = 0
            elif ft is float or (origin is not None and origin is float):
                example[name] = 0.0
            elif ft is bool or (origin is not None and origin is bool):
                example[name] = False
            elif origin is list or ft is list:
                example[name] = []
            else:
                example[name] = "<str>"
        else:
            # get default value when present
            default = None
            if hasattr(field, "default"):
                default = field.default
            elif (
                hasattr(field, "default_factory") and field.default_factory is not None
            ):
                default = field.default_factory()
            else:
                default = field.default
            example[name] = default
    return example


def _model_info(model_cls: type[BaseModel]) -> dict[str, Any]:
    schema = model_cls.model_json_schema()
    return {
        "model_schema": schema,
        "model_schema_json": schema,
        "correct_example": _example_from_model(model_cls),
    }


def _format_validation_error(exc: ValidationError) -> dict[str, Any]:
    errors = exc.errors()
    return {
        "errors": errors,
        "summary": errors[0]["msg"] if errors else "validation failed",
        "json": exc.json(),
    }


class HostLister(Protocol):
    def list_hosts(self) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class NornirHostLister:
    get_nr: Callable[[], Any]

    def list_hosts(self) -> list[dict[str, Any]]:
        nr = self.get_nr()
        hosts_info: list[dict[str, Any]] = []
        sensitive_keys = {"password", "secret"}
        for name, host_obj in nr.inventory.hosts.items():
            safe_data = {
                k: v
                for k, v in (host_obj.data or {}).items()
                if k not in sensitive_keys
            }
            hosts_info.append(
                {
                    "name": name,
                    "hostname": host_obj.hostname,
                    "platform": host_obj.platform,
                    "groups": [g.name for g in host_obj.groups],
                    "data": safe_data,
                }
            )
        return hosts_info


def register_validate_params(mcp: Any, get_nr: Callable[[], Any]) -> None:
    """Register the validate_params tool using the provided MCP instance."""
    try:
        mcp.tool(
            description="Validate input payloads against known Pydantic models; returns success, validation details, model schema, and example."
        )(make_validate_params(NornirHostLister(get_nr)))
    except (ValueError, RuntimeError) as exc:
        logger.warning("Failed to register 'validate_params' tool: %s", exc)


def make_validate_params(nr_mgr: HostLister):
    """Return an async validate_params function bound to the provided nr_mgr.

    This avoids circular imports: server creates nr_mgr then registers
    mcp.tool()(make_validate_params(nr_mgr)).
    """

    async def validate_params(
        raw: dict[str, Any], model_name: str = "DeviceNameModel"
    ) -> dict[str, Any]:
        logger.info(f"[Tool] validate_params called for model {model_name}")
        model_cls = MODEL_MAP.get(model_name)
        if model_cls is None:
            return {
                "success": False,
                **error_response(
                    f"Unknown model '{model_name}'",
                    code="unknown_model",
                    available_models=list(MODEL_MAP.keys()),
                ),
            }

        try:
            model_cls.model_validate(raw)
            return {
                "success": True,
                "validated": raw,
                **_model_info(model_cls),
            }
        except ValidationError as ve:
            missing_required = _get_missing_required_fields(model_cls, raw)
            suggested_payload = _build_suggested_payload(raw, missing_required, nr_mgr)

            formatted = _format_validation_error(ve)
            if "device_name" in missing_required:
                formatted["summary"] = "'device_name' is a required property"
                friendly = formatted.get("friendly", [])
                friendly.insert(0, formatted["summary"])
                formatted["friendly"] = friendly

            return {
                "success": False,
                **error_response(
                    "Validation failed",
                    code="validation_failed",
                ),
                "validation": formatted,
                **_model_info(model_cls),
                "suggested_payload": suggested_payload,
                "note": "If you provided 'name' or 'hostname', map it to the inventory 'name' and send it as 'device_name'. Call list_all_hosts() to discover inventory names.",
            }

    return validate_params


def _get_missing_required_fields(
    model_cls: type[BaseModel], raw: dict[str, Any]
) -> list[str]:
    """Helper function to extract missing required fields from validation error."""
    missing_required = []
    if isinstance(raw, dict):
        # pydantic v2: model_fields -> FieldInfo with is_required
        fields = getattr(model_cls, "model_fields", None)
        if fields is None:
            # fallback for older pydantic versions
            fields = getattr(model_cls, "__fields__", {})
        for fname, field in fields.items():
            is_required = getattr(field, "is_required", None)
            if is_required is None:
                # pydantic v1 compatibility: Field has 'required'
                is_required = getattr(field, "required", False)
            if is_required and fname not in raw:
                missing_required.append(fname)
    return missing_required


def _build_suggested_payload(
    raw: dict[str, Any], missing_required: list[str], nr_mgr: HostLister
) -> dict[str, Any] | None:
    """Helper function to build suggested payload for common validation errors."""
    suggested_payload = None
    if isinstance(raw, dict):
        if "name" in raw and "device_name" in missing_required:
            suggested_payload = {"device_name": raw.get("name")}
        elif "hostname" in raw and "device_name" in missing_required:
            try:
                hosts = nr_mgr.list_hosts()
                match = next(
                    (h for h in hosts if h.get("hostname") == raw.get("hostname")),
                    None,
                )
                if match:
                    suggested_payload = {"device_name": match.get("name")}
                else:
                    suggested_payload = {
                        "device_name": f"<name from list_all_hosts for hostname {raw.get('hostname')}>"
                    }
            except Exception:
                suggested_payload = {"device_name": "<inventory_name>"}
    return suggested_payload
