"""Nornir MCP Server system and validation tools."""

from typing import Any

from pydantic import ValidationError

from ..application import mcp
from ..models import DeviceFilters


@mcp.tool()
async def validate_params(
    model_name: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Verify inputs against Pydantic models.

    Args:
        model_name: Name of the model to validate against (e.g., 'DeviceFilters')
        params: Dictionary of parameters to validate

    Returns:
        Validation result with success status or error details.
    """
    models = {
        "DeviceFilters": DeviceFilters,
    }

    if model_name not in models:
        return {
            "valid": False,
            "error": f"Model '{model_name}' not found. Available models: {list(models.keys())}",
        }

    try:
        models[model_name](**params)
        return {"valid": True, "model": model_name}
    except ValidationError as e:
        return {
            "valid": False,
            "error": "Validation failed",
            "details": e.errors(include_url=False, include_context=False),
        }
