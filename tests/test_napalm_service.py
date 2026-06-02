import asyncio

from nornir_mcp.services.napalm import napalm_get, run_napalm_get


def test_run_napalm_get_calls_runner_with_required_arguments(monkeypatch) -> None:
    calls = []

    async def fake_execute(**kwargs):
        calls.append(kwargs)
        return {"leaf-1": {"facts": {"hostname": "leaf-1"}}}

    monkeypatch.setattr("nornir_mcp.services.napalm.execute", fake_execute)

    result = asyncio.run(run_napalm_get(getters=["facts"], hostname="leaf-1"))

    assert result == {"leaf-1": {"facts": {"hostname": "leaf-1"}}}
    assert calls == [
        {
            "task": napalm_get,
            "name": None,
            "hostname": "leaf-1",
            "group": None,
            "platform": None,
            "getters": ["facts"],
        }
    ]


def test_run_napalm_get_includes_getter_options(monkeypatch) -> None:
    calls = []
    getters_options = {"config": {"retrieve": "running"}}

    async def fake_execute(**kwargs):
        calls.append(kwargs)
        return {"leaf-1": {"config": {"running": "hostname leaf-1"}}}

    monkeypatch.setattr("nornir_mcp.services.napalm.execute", fake_execute)

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
            "name": None,
            "hostname": None,
            "group": None,
            "platform": None,
            "getters": ["config"],
            "getters_options": getters_options,
        }
    ]
