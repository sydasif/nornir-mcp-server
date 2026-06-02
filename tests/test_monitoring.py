import asyncio

from nornir_mcp.models import TaskResult
from nornir_mcp.services.runner import GLOBAL_ERROR_HOST
from nornir_mcp.tools.monitoring import get_structured_data


def test_get_structured_data_forwards_getters_and_options(monkeypatch) -> None:
    calls = []
    getters_options = {"interfaces": {"interface": "Ethernet1"}}

    async def fake_run_napalm_get(**kwargs):
        calls.append(kwargs)
        return {"leaf-1": {"success": True, "output": {"interfaces": {}}}}

    monkeypatch.setattr(
        "nornir_mcp.tools.monitoring.run_napalm_get",
        fake_run_napalm_get,
    )

    result = asyncio.run(
        get_structured_data.fn(
            getters=["interfaces"],
            getters_options=getters_options,
            filter_group="core",
        )
    )

    assert "leaf-1" in result["hosts"]
    assert result["hosts"]["leaf-1"]["output"] == {"interfaces": {}}
    TaskResult.model_validate(result)
    assert calls == [
        {
            "getters": ["interfaces"],
            "name": None,
            "hostname": None,
            "group": "core",
            "platform": None,
            "getters_options": getters_options,
        }
    ]


def test_get_structured_data_passes_through_global_error(monkeypatch) -> None:
    """Verify that global errors are passed through unchanged."""

    async def fake_run_napalm_get(**kwargs):
        return {
            GLOBAL_ERROR_HOST: {
                "error": True,
                "code": "config_error",
                "message": "missing config",
            }
        }

    monkeypatch.setattr(
        "nornir_mcp.tools.monitoring.run_napalm_get",
        fake_run_napalm_get,
    )

    result = asyncio.run(get_structured_data.fn(getters=["facts"]))

    assert result[GLOBAL_ERROR_HOST]["error"] is True
    assert result[GLOBAL_ERROR_HOST]["code"] == "config_error"
