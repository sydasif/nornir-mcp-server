"""Shared error response helpers."""

from typing import Any


def error_response(message: str, code: str = "error", **details: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": True, "code": code, "message": message}
    if details:
        payload["details"] = details
    return payload
