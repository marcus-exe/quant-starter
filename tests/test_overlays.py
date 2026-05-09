from __future__ import annotations

import numpy as np
import pandas as pd

from src.strategies.base import Strategy
from src.strategies.overlays.vol_target import VolTarget


class _AlwaysLong(Strategy):
    name = "_always_long"

    def signals(self, close: pd.DataFrame) -> pd.DataFrame:
        return pd.DataFrame(True, index=close.index, columns=close.columns)


def _gbm_close(n: int = 1000, n_assets: int = 4, seed: int = 0) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2018-01-01", periods=n, freq="B")
    cols = {f"A{i}": 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.012, n))) for i in range(n_assets)}
    return pd.DataFrame(cols, index=idx)


def test_vol_target_scales_when_realized_vol_high():
    close = _gbm_close()
    overlay = VolTarget(_AlwaysLong(), target_vol=0.10, lookback=20, max_leverage=3.0)
    w = overlay.weights(close)
    assert w.shape == close.shape

    returns = close.pct_change().fillna(0.0)
    port_ret = (w.shift(1) * returns).sum(axis=1)
    realized_annual = port_ret.iloc[200:].std() * np.sqrt(252)
    assert 0.05 < realized_annual < 0.20


def test_vol_target_caps_leverage():
    close = pd.DataFrame(
        {"A": 100.0 * np.ones(100)}, index=pd.date_range("2020", periods=100, freq="B")
    )
    overlay = VolTarget(_AlwaysLong(), target_vol=0.10, lookback=20, max_leverage=2.5)
    w = overlay.weights(close)
    assert (w["A"].abs() <= 2.5 + 1e-9).all()


def test_risk_parity_weights_inverse_vol_and_sum_to_one():
    from src.strategies.overlays.risk_parity import RiskParity

    rng = np.random.default_rng(1)
    n = 500
    idx = pd.date_range("2020", periods=n, freq="B")
    low_vol = 100 * np.exp(np.cumsum(rng.normal(0, 0.005, n)))
    high_vol = 100 * np.exp(np.cumsum(rng.normal(0, 0.020, n)))
    close = pd.DataFrame({"LOW": low_vol, "HIGH": high_vol}, index=idx)

    overlay = RiskParity(_AlwaysLong(), lookback=60)
    w = overlay.weights(close)

    settled = w.iloc[100:]
    row_sums = settled.sum(axis=1)
    assert np.allclose(row_sums, 1.0, atol=1e-9)
    assert (settled["LOW"] > settled["HIGH"]).all()


def test_risk_parity_zero_weights_outside_active_signals():
    from src.strategies.overlays.risk_parity import RiskParity

    class _LongOnlyFirst(Strategy):
        name = "_long_first"
        def signals(self, close):
            sig = pd.DataFrame(False, index=close.index, columns=close.columns)
            sig.iloc[:, 0] = True
            return sig

    rng = np.random.default_rng(2)
    n = 200
    idx = pd.date_range("2020", periods=n, freq="B")
    close = pd.DataFrame(
        {f"A{i}": 100 * np.exp(np.cumsum(rng.normal(0, 0.01, n))) for i in range(3)}, index=idx
    )
    w = RiskParity(_LongOnlyFirst(), lookback=20).weights(close)
    tail = w.iloc[100:]
    assert (tail["A1"] == 0).all()
    assert (tail["A2"] == 0).all()
    assert (tail["A0"] == 1.0).all()


def test_vol_target_rejects_bad_params():
    import pytest
    with pytest.raises(ValueError):
        VolTarget(_AlwaysLong(), target_vol=-0.1)
    with pytest.raises(ValueError):
        VolTarget(_AlwaysLong(), lookback=1)
    with pytest.raises(ValueError):
        VolTarget(_AlwaysLong(), max_leverage=0)
