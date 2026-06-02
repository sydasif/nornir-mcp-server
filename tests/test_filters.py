from types import SimpleNamespace
import pytest

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

    result = apply_filters(nr)

    assert result is nr
    assert nr.filter_calls == []


def test_apply_filters_returns_original_when_filter_fields_are_empty() -> None:
    nr = FakeNornir(host_count=2)

    result = apply_filters(nr, name=None, hostname=None, group=None, platform=None)

    assert result is nr
    assert nr.filter_calls == []


def test_apply_filters_uses_correct_filter_expressions() -> None:
    nr = FakeNornir(host_count=2)

    apply_filters(
        nr,
        name="leaf-1",
        hostname="10.0.0.1",
        group="spine",
        platform="ios",
    )

    assert len(nr.filter_calls) == 4


def test_apply_filters_raises_when_no_hosts_match() -> None:
    nr = FakeNornir(host_count=0)

    with pytest.raises(ValueError, match="No devices matched the provided filters"):
        apply_filters(nr, hostname="leaf-1")
