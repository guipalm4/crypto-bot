from __future__ import annotations

from importlib.metadata import EntryPoint
from typing import Any, Mapping

import pytest

from crypto_bot.plugins.strategies.base import Strategy, StrategySignal
from crypto_bot.plugins.strategies.loader import (
    ENTRY_POINT_GROUP,
    discover_strategies,
)


class ValidStrategy(Strategy):
    name = "valid"

    def validate_parameters(
        self, params: Mapping[str, Any]
    ) -> None:  # pragma: no cover - trivial
        return None

    def generate_signal(
        self, market_data: Any, params: Mapping[str, Any]
    ) -> StrategySignal:
        return StrategySignal(action="hold", strength=0.0)

    def reset_state(self) -> None:  # pragma: no cover - trivial
        return None


class AnotherValid(Strategy):
    name = "valid"  # duplicate name on purpose

    def validate_parameters(
        self, params: Mapping[str, Any]
    ) -> None:  # pragma: no cover - trivial
        return None

    def generate_signal(
        self, market_data: Any, params: Mapping[str, Any]
    ) -> StrategySignal:
        return StrategySignal(action="sell", strength=1.0)

    def reset_state(self) -> None:  # pragma: no cover - trivial
        return None


class NotAStrategy:  # missing Strategy inheritance
    pass


def make_ep(name: str, value: str) -> EntryPoint:
    return EntryPoint(name=name, value=value, group=ENTRY_POINT_GROUP)


def clear_cache() -> None:
    # Reset cache between tests
    discover_strategies.cache_clear()  # type: ignore[attr-defined]


def test_discover_returns_valid_strategy(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_cache()

    eps = [
        make_ep(
            name="valid",
            value="tests.unit.plugins.test_strategy_loader:ValidStrategy",
        )
    ]

    monkeypatch.setattr(
        "crypto_bot.plugins.strategies.loader.entry_points", lambda **kwargs: eps
    )

    result = discover_strategies()
    assert "valid" in result
    assert result["valid"].__name__ == "ValidStrategy"


def test_discover_ignores_non_subclass(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_cache()

    eps = [
        make_ep(
            name="not_strategy",
            value="tests.unit.plugins.test_strategy_loader:NotAStrategy",
        )
    ]

    monkeypatch.setattr(
        "crypto_bot.plugins.strategies.loader.entry_points", lambda **kwargs: eps
    )

    result = discover_strategies()
    assert result == {}


def test_discover_handles_duplicate_names(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_cache()

    eps = [
        make_ep(
            name="valid",
            value="tests.unit.plugins.test_strategy_loader:ValidStrategy",
        ),
        make_ep(
            name="duplicate",
            value="tests.unit.plugins.test_strategy_loader:AnotherValid",
        ),
    ]

    monkeypatch.setattr(
        "crypto_bot.plugins.strategies.loader.entry_points", lambda **kwargs: eps
    )

    result = discover_strategies()
    # first wins
    assert set(result.keys()) == {"valid"}
    assert result["valid"].__name__ == "ValidStrategy"


def test_discover_handles_load_error(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_cache()

    class BrokenEntryPoint(EntryPoint):
        def load(self) -> Any:  # type: ignore[override]
            raise RuntimeError("boom")

    broken = BrokenEntryPoint(
        name="broken",
        value="tests.unit.plugins.test_strategy_loader:ValidStrategy",
        group=ENTRY_POINT_GROUP,
    )
    eps = [broken]

    monkeypatch.setattr(
        "crypto_bot.plugins.strategies.loader.entry_points", lambda **kwargs: eps
    )

    result = discover_strategies()
    assert result == {}


def test_discover_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    clear_cache()
    monkeypatch.setattr(
        "crypto_bot.plugins.strategies.loader.entry_points", lambda **kwargs: []
    )
    result = discover_strategies()
    assert result == {}
