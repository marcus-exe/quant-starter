from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.risk.sizing import fixed_fraction, kelly
from src.strategies.sma_cross import SmaCross


def _trending_prices(n: int = 300, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    drift = np.linspace(0, 0.5, n)
    noise = rng.normal(0, 0.01, n)
    close = 100 * np.exp(np.cumsum(noise) + drift / n)
    idx = pd.date_range("2020-01-01", periods=n, freq="D")
    return pd.DataFrame({"close": close}, index=idx)


def test_sma_cross_signals_align():
    s = SmaCross(fast=10, slow=50)
    prices = _trending_prices()
    sig = s.signals(prices)
    assert sig.index.equals(prices.index)
    assert sig.dtype == bool


def test_sma_cross_rejects_bad_params():
    with pytest.raises(ValueError):
        SmaCross(fast=200, slow=50)


def test_fixed_fraction_floors_qty():
    assert fixed_fraction(10_000, 0.1, 99) == 10


def test_kelly_caps_at_limit():
    assert kelly(0.99, 100, cap=0.1) == 0.1


def test_kelly_zero_when_negative_edge():
    assert kelly(0.4, 1.0) == 0.0
