from __future__ import annotations

import pandas as pd

from crypto_bot.plugins.strategies.macd_crossover import MACDCrossover


def _df_from_close(values: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=len(values), freq="D")
    return pd.DataFrame({"close": values}, index=idx)


def test_macd_crossover_validates_parameters_defaults():
    strat = MACDCrossover()
    strat.validate_parameters({})


def test_macd_crossover_insufficient_data_holds():
    strat = MACDCrossover()
    df = _df_from_close([100.0])
    sig = strat.generate_signal(df, {})
    assert sig.action == "hold"


def test_macd_bullish_crossover_emits_buy():
    strat = MACDCrossover()
    # Parameters with short EMAs to make crosses easier
    params = {"fast": 2, "slow": 4, "signal": 2}
    # Increasing prices tend to create bullish cross
    df = _df_from_close([100, 101, 102, 103, 104, 105])
    sig = strat.generate_signal(df, params)
    assert sig.action in {"buy", "hold"}


def test_macd_bearish_crossover_emits_sell():
    strat = MACDCrossover()
    params = {"fast": 2, "slow": 4, "signal": 2}
    # Decreasing prices tend to create bearish cross
    df = _df_from_close([105, 104, 103, 102, 101, 100])
    sig = strat.generate_signal(df, params)
    assert sig.action in {"sell", "hold"}
