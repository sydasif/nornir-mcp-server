import asyncio
from types import SimpleNamespace

from nornir_mcp.models import InventorySummary
from nornir_mcp.services.inventory import InventoryError
from nornir_mcp.tools.inventory import list_network_devices


def _host(
    name: str, hostname: str, platform: str, groups: list[str], data: dict
) -> SimpleNamespace:
    return SimpleNamespace(
        name=name,
        hostname=hostname,
        platform=platform,
        groups=[SimpleNamespace(name=group) for group in groups],
        data=data,
    )


def test_list_network_devices_rejects_invalid_query_type() -> None:
    result = asyncio.run(list_network_devices.fn(query_type="invalid"))

    assert result["error"] is True
    assert result["code"] == "invalid_query_type"


def test_list_network_devices_returns_config_error(monkeypatch) -> None:
    def raise_config_error(filters=None):
        raise InventoryError("missing config", code="config_error")

    monkeypatch.setattr("nornir_mcp.tools.inventory.get_filtered_nornir", raise_config_error)

    result = asyncio.run(list_network_devices.fn())

    assert result == {
        "error": True,
        "code": "config_error",
        "message": "missing config",
    }


def test_list_network_devices_returns_filter_error(monkeypatch) -> None:
    def raise_filter_error(filters=None):
        raise InventoryError("bad filters", code="filter_error")

    monkeypatch.setattr("nornir_mcp.tools.inventory.get_filtered_nornir", raise_filter_error)

    result = asyncio.run(list_network_devices.fn())

    assert result == {
        "error": True,
        "code": "filter_error",
        "message": "bad filters",
    }


def test_list_network_devices_returns_devices_and_groups(monkeypatch) -> None:
    nr = SimpleNamespace(
        inventory=SimpleNamespace(
            hosts={
                "leaf-1": _host(
                    name="leaf-1",
                    hostname="10.0.0.1",
                    platform="ios",
                    groups=["core", "dc1"],
                    data={"site": "dc1"},
                ),
                "leaf-2": _host(
                    name="leaf-2",
                    hostname="10.0.0.2",
                    platform="ios",
                    groups=["core"],
                    data={"site": "dc1"},
                ),
            },
            groups={"core": object(), "dc1": object()},
        )
    )

    monkeypatch.setattr("nornir_mcp.tools.inventory.get_filtered_nornir", lambda filters=None: nr)

    result = asyncio.run(list_network_devices.fn(details=True))

    assert result["devices"]["total_devices"] == 2
    assert result["devices"]["devices"][0]["data"] == {"site": "dc1"}
    assert result["groups"]["groups"]["core"]["count"] == 2
    assert result["groups"]["groups"]["dc1"]["members"] == ["leaf-1"]
    InventorySummary.model_validate(result)


def test_list_network_devices_result_always_validates_as_inventory_summary(
    monkeypatch,
) -> None:
    """Verify the tool's return value always conforms to InventorySummary."""
    nr = SimpleNamespace(
        inventory=SimpleNamespace(
            hosts={
                "leaf-1": _host(
                    name="leaf-1",
                    hostname="10.0.0.1",
                    platform="ios",
                    groups=["core"],
                    data={},
                ),
            },
            groups={"core": object()},
        )
    )
    monkeypatch.setattr("nornir_mcp.tools.inventory.get_filtered_nornir", lambda filters=None: nr)

    result = asyncio.run(list_network_devices.fn())
    InventorySummary.model_validate(result)
