import asyncio

from nornir_mcp.models import DeviceFilters
from nornir_mcp.tools.monitoring import get_device_facts, run_napalm_getter


def test_get_device_facts_runs_facts_getter(monkeypatch) -> None:
    calls = []
    filters = DeviceFilters(platform="ios")

    async def fake_run_napalm_get(**kwargs):
        calls.append(kwargs)
        return {"leaf-1": {"facts": {"vendor": "Cisco"}}}

    monkeypatch.setattr(
        "nornir_mcp.tools.monitoring.run_napalm_get",
        fake_run_napalm_get,
    )

    result = asyncio.run(get_device_facts.fn(filters=filters))

    assert result == {"leaf-1": {"facts": {"vendor": "Cisco"}}}
    assert calls == [
        {
            "getters": ["facts"],
            "filters": filters,
        }
    ]


def test_run_napalm_getter_forwards_getters_and_options(monkeypatch) -> None:
    calls = []
    filters = DeviceFilters(group="core")
    getters_options = {"interfaces": {"interface": "Ethernet1"}}

    async def fake_run_napalm_get(**kwargs):
        calls.append(kwargs)
        return {"leaf-1": {"interfaces": {}}}

    monkeypatch.setattr(
        "nornir_mcp.tools.monitoring.run_napalm_get",
        fake_run_napalm_get,
    )

    result = asyncio.run(
        run_napalm_getter.fn(
            getters=["interfaces"],
            filters=filters,
            getters_options=getters_options,
        )
    )

    assert result == {"leaf-1": {"interfaces": {}}}
    assert calls == [
        {
            "getters": ["interfaces"],
            "filters": filters,
            "getters_options": getters_options,
        }
    ]
