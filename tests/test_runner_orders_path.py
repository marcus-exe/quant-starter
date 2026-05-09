from __future__ import annotations

import numpy as np
import pandas as pd

from src.backtest.runner import run
from src.strategies.base import Strategy


class _ConstWeights(Strategy):
    name = "_const_w"

    def __init__(self, w: pd.DataFrame):
        self._w = w

    def weights(self, close: pd.DataFrame) -> pd.DataFrame:
        return self._w


def _two_asset_close(n: int = 252, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
    a = 100 * np.exp(np.cumsum(rng.normal(0.0005, 0.01, n)))
    b = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, n)))
    return pd.DataFrame({"AAA": a, "BBB": b}, index=idx)


def test_orders_path_equal_weight_long_only_runs():
    close = _two_asset_close()
    w = pd.DataFrame(0.5, index=close.index, columns=close.columns)
    result = run(_ConstWeights(w), close=close) if False else run(close, _ConstWeights(w))
    assert np.isfinite(result.total_return)
    assert result.n_trades >= 1


def test_orders_path_long_short_pair_runs():
    close = _two_asset_close()
    w = pd.DataFrame({"AAA": 0.5, "BBB": -0.5}, index=close.index)
    result = run(close, _ConstWeights(w))
    assert np.isfinite(result.total_return)
    assert np.isfinite(result.sharpe)


def test_orders_path_flat_when_zero_weights():
    close = _two_asset_close()
    w = pd.DataFrame(0.0, index=close.index, columns=close.columns)
    result = run(close, _ConstWeights(w))
    assert result.n_trades == 0
