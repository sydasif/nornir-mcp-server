import asyncio

from nornir_mcp.models import DeviceFilters
from nornir_mcp.services.napalm import napalm_get, run_napalm_get


def test_run_napalm_get_calls_runner_with_required_arguments(monkeypatch) -> None:
    calls = []
    filters = DeviceFilters(hostname="leaf-1")

    async def fake_execute(**kwargs):
        calls.append(kwargs)
        return {"leaf-1": {"facts": {"hostname": "leaf-1"}}}

    monkeypatch.setattr("nornir_mcp.services.napalm.runner.execute", fake_execute)

    result = asyncio.run(run_napalm_get(getters=["facts"], filters=filters))

    assert result == {"leaf-1": {"facts": {"hostname": "leaf-1"}}}
    assert calls == [
        {
            "task": napalm_get,
            "filters": filters,
            "getters": ["facts"],
        }
    ]


def test_run_napalm_get_includes_getter_options(monkeypatch) -> None:
    calls = []
    getters_options = {"config": {"retrieve": "running"}}

    async def fake_execute(**kwargs):
        calls.append(kwargs)
        return {"leaf-1": {"config": {"running": "hostname leaf-1"}}}

    monkeypatch.setattr("nornir_mcp.services.napalm.runner.execute", fake_execute)

    result = asyncio.run(
        run_napalm_get(
            getters=["config"],
            getters_options=getters_options,
        )
    )

    assert result == {"leaf-1": {"config": {"running": "hostname leaf-1"}}}
    assert calls == [
        {
            "task": napalm_get,
            "filters": None,
            "getters": ["config"],
            "getters_options": getters_options,
        }
    ]
