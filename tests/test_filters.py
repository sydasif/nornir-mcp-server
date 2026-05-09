from types import SimpleNamespace

import pytest

from nornir_mcp.models import DeviceFilters
from nornir_mcp.utils.filters import apply_filters


class FakeNornir:
    def __init__(self, host_count: int) -> None:
        self.inventory = SimpleNamespace(
            hosts={f"host-{idx}": object() for idx in range(host_count)}
        )
        self.filter_calls: list[object] = []

    def filter(self, expression: object) -> "FakeNornir":
        self.filter_calls.append(expression)
        return self


def test_apply_filters_returns_original_when_filters_missing() -> None:
    nr = FakeNornir(host_count=2)

    result = apply_filters(nr, None)

    assert result is nr
    assert nr.filter_calls == []


def test_apply_filters_returns_original_when_filter_fields_are_empty() -> None:
    nr = FakeNornir(host_count=2)

    result = apply_filters(nr, DeviceFilters())

    assert result is nr
    assert nr.filter_calls == []


def test_apply_filters_raises_when_no_hosts_match() -> None:
    nr = FakeNornir(host_count=0)

    with pytest.raises(ValueError, match="No devices matched the provided filters"):
        apply_filters(nr, DeviceFilters(hostname="leaf-1"))
