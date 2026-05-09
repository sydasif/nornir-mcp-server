from nornir_mcp.services.inventory import (
    InventoryError,
    get_filtered_nornir,
)


def test_get_filtered_nornir_reloads_inventory_on_every_call(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_get_nornir():
        calls["count"] += 1
        return f"nr-{calls['count']}"

    monkeypatch.setattr("nornir_mcp.services.inventory.get_nornir", fake_get_nornir)
    monkeypatch.setattr(
        "nornir_mcp.services.inventory.apply_filters", lambda nr, filters: nr
    )

    first = get_filtered_nornir()
    second = get_filtered_nornir()

    assert first == "nr-1"
    assert second == "nr-2"
    assert calls["count"] == 2


def test_get_filtered_nornir_wraps_config_errors(monkeypatch) -> None:
    def raise_config_error():
        raise ValueError("missing config")

    monkeypatch.setattr("nornir_mcp.services.inventory.get_nornir", raise_config_error)

    try:
        get_filtered_nornir()
    except InventoryError as exc:
        assert str(exc) == "missing config"
    else:
        raise AssertionError("Expected InventoryError")


def test_get_filtered_nornir_wraps_filter_errors(monkeypatch) -> None:
    monkeypatch.setattr("nornir_mcp.services.inventory.get_nornir", lambda: "nr")

    def raise_filter_error(nr, filters):
        raise ValueError("bad filters")

    monkeypatch.setattr(
        "nornir_mcp.services.inventory.apply_filters", raise_filter_error
    )

    try:
        get_filtered_nornir()
    except InventoryError as exc:
        assert str(exc) == "bad filters"
    else:
        raise AssertionError("Expected InventoryError")
