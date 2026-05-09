from __future__ import annotations

import numpy as np
import pandas as pd

from src.strategies.bollinger import BollingerFade
from src.strategies.donchian import Donchian
from src.strategies.rsi2 import Rsi2
from src.strategies.seasonality import TurnOfMonth


def _mean_reverting(n: int = 500, seed: int = 0, symbols: tuple[str, ...] = ("AAA",)) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    cols = {}
    for sym in symbols:
        x = np.zeros(n)
        for i in range(1, n):
            x[i] = 0.7 * x[i - 1] + rng.normal(0, 1)
        cols[sym] = 100.0 + x
    return pd.DataFrame(cols, index=idx)


def _trending(n: int = 500, seed: int = 0, symbols: tuple[str, ...] = ("AAA",)) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    cols = {sym: 100 * np.exp(np.cumsum(rng.normal(0.0008, 0.01, n))) for sym in symbols}
    return pd.DataFrame(cols, index=idx)


def test_rsi2_signals_shape_dtype():
    close = _mean_reverting()
    sig = Rsi2().signals(close)
    assert sig.shape == close.shape
    assert (sig.dtypes == bool).all()
    assert sig.index.equals(close.index)


def test_rsi2_fires_on_mean_reverting():
    sig = Rsi2(period=2, entry=10, exit=70).signals(_mean_reverting(n=1000))
    transitions = (sig.astype(int).diff().abs() > 0).sum().sum()
    assert transitions > 5


def test_rsi2_rejects_bad_params():
    import pytest
    with pytest.raises(ValueError):
        Rsi2(entry=80, exit=10)


def test_bollinger_signals_shape():
    close = _mean_reverting()
    sig = BollingerFade(period=20, n_std=2.0).signals(close)
    assert sig.shape == close.shape
    assert (sig.dtypes == bool).all()


def test_bollinger_fires_on_extreme_dip():
    close = _mean_reverting(n=800, seed=42)
    sig = BollingerFade(period=20, n_std=1.0).signals(close)
    assert sig.sum().sum() > 0


def test_donchian_shape_dtype():
    close = _trending(n=500)
    sig = Donchian(entry_lookback=20, exit_lookback=10).signals(close)
    assert sig.shape == close.shape
    assert (sig.dtypes == bool).all()


def test_donchian_enters_on_breakout():
    close = pd.DataFrame(
        {"AAA": [100.0] * 25 + list(np.linspace(101, 130, 50))},
        index=pd.date_range("2020-01-01", periods=75, freq="B"),
    )
    sig = Donchian(entry_lookback=20, exit_lookback=10).signals(close)
    assert sig["AAA"].iloc[26:].any()


def test_donchian_rejects_bad_params():
    import pytest
    with pytest.raises(ValueError):
        Donchian(entry_lookback=10, exit_lookback=20)


def test_turn_of_month_active_dates():
    idx = pd.date_range("2023-01-01", "2023-03-31", freq="B")
    close = pd.DataFrame({"AAA": np.arange(len(idx), dtype=float)}, index=idx)
    sig = TurnOfMonth(days_end=4, days_start=3).signals(close)
    assert sig.shape == close.shape
    assert (sig.dtypes == bool).all()
    jan = sig.loc["2023-01"]
    assert jan["AAA"].iloc[:3].all()
    assert jan["AAA"].iloc[-4:].all()
    mid = jan["AAA"].iloc[8:14]
    assert not mid.any()


def test_turn_of_month_rejects_zero_window():
    import pytest
    with pytest.raises(ValueError):
        TurnOfMonth(days_end=0, days_start=0)


def test_pairs_emits_opposite_signs_on_cointegrated_synthetic():
    from src.strategies.pairs import Pairs

    rng = np.random.default_rng(0)
    n = 800
    idx = pd.date_range("2018-01-01", periods=n, freq="B")
    common = np.cumsum(rng.normal(0, 0.5, n))
    a = 50.0 + common + rng.normal(0, 0.5, n)
    b = 100.0 + 1.5 * common + rng.normal(0, 0.5, n)
    close = pd.DataFrame({"AAA": a, "BBB": b}, index=idx)

    strat = Pairs(window=60, entry_z=1.5, exit_z=0.3, leg_size=0.5)
    w = strat.weights(close)
    assert w.shape == close.shape

    nz = w[(w["AAA"] != 0) | (w["BBB"] != 0)]
    assert len(nz) > 10
    same_sign = (np.sign(nz["AAA"]) == np.sign(nz["BBB"])).sum()
    assert same_sign == 0


def test_pairs_rejects_wrong_column_count():
    import pytest
    from src.strategies.pairs import Pairs

    close = pd.DataFrame({"X": [1.0, 2.0, 3.0]}, index=pd.date_range("2020", periods=3))
    with pytest.raises(ValueError):
        Pairs().weights(close)


def test_vix_carry_signal_only_on_target():
    from src.strategies.vix_carry import VixCarry

    idx = pd.date_range("2020-01-02", periods=30, freq="B")
    close = pd.DataFrame({"SVXY": np.linspace(100, 110, 30)}, index=idx)

    class _StubVix(VixCarry):
        def _term_ratio(self, index):
            vals = np.where(np.arange(len(index)) % 2 == 0, 0.95, 1.05)
            return pd.Series(vals, index=index)

    strat = _StubVix(target="SVXY", smooth=1)
    sig = strat.signals(close)
    assert list(sig.columns) == ["SVXY"]
    assert sig["SVXY"].sum() == 15
    assert sig["SVXY"].dtype == bool
