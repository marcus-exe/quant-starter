from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.risk.sizing import fixed_fraction, kelly
from src.strategies.sma_cross import SmaCross


def _trending_close(n: int = 300, seed: int = 0, symbols: tuple[str, ...] = ("AAA",)) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    cols = {}
    for i, sym in enumerate(symbols):
        drift = np.linspace(0, 0.5 + 0.1 * i, n)
        noise = rng.normal(0, 0.01, n)
        cols[sym] = 100 * np.exp(np.cumsum(noise) + drift / n)
    return pd.DataFrame(cols, index=idx)


def test_sma_cross_signals_align():
    s = SmaCross(fast=10, slow=50)
    close = _trending_close()
    sig = s.signals(close)
    assert sig.index.equals(close.index)
    assert sig.shape == close.shape
    assert (sig.dtypes == bool).all()


def test_sma_cross_multi_asset():
    s = SmaCross(fast=10, slow=50)
    close = _trending_close(symbols=("AAA", "BBB", "CCC"))
    sig = s.signals(close)
    assert list(sig.columns) == ["AAA", "BBB", "CCC"]


def test_sma_cross_rejects_bad_params():
    with pytest.raises(ValueError):
        SmaCross(fast=200, slow=50)


def test_fixed_fraction_floors_qty():
    assert fixed_fraction(10_000, 0.1, 99) == 10


def test_kelly_caps_at_limit():
    assert kelly(0.99, 100, cap=0.1) == 0.1


def test_kelly_zero_when_negative_edge():
    assert kelly(0.4, 1.0) == 0.0
