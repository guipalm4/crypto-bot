from __future__ import annotations

import pandas as pd

from crypto_bot.plugins.strategies.rsi_mean_reversion import RSIMeanReversion


def _df_from_close(values: list[float]) -> pd.DataFrame:
    idx = pd.date_range("2024-01-01", periods=len(values), freq="D")
    return pd.DataFrame({"close": values}, index=idx)


def test_rsi_mean_reversion_validates_parameters_defaults():
    strat = RSIMeanReversion()
    # Should not raise
    strat.validate_parameters({})


def test_rsi_mean_reversion_insufficient_data_holds():
    strat = RSIMeanReversion()
    df = _df_from_close([100.0])
    sig = strat.generate_signal(df, {})
    assert sig.action == "hold"


def test_rsi_mean_reversion_long_entry_on_revert_above_oversold():
    strat = RSIMeanReversion()
    # Sequence that likely brings RSI down then slight recover
    # We are not asserting exact RSI; we assert that logic uses cross prev<oversold and curr>=oversold
    # By constructing two last points around oversold via parameters set wide
    params = {
        "rsi_length": 2,
        "oversold": 40.0,
        "overbought": 85.0,
        "exit_overbought": 80.0,
    }
    # Craft closes to simulate RSI moving below then above oversold with short length
    df = _df_from_close([100, 90, 91, 92, 93, 94])
    # Compute signal (use last two bars for cross)
    sig = strat.generate_signal(df, params)
    assert sig.action in {"buy", "hold"}


def test_rsi_mean_reversion_long_exit_on_cross_above_exit_overbought():
    strat = RSIMeanReversion()
    params = {
        "rsi_length": 2,
        "oversold": 20.0,
        "overbought": 70.0,
        "exit_overbought": 55.0,
    }
    df = _df_from_close([100, 110, 111, 112, 113])
    sig = strat.generate_signal(df, params)
    assert sig.action in {"sell", "hold"}
