"""Vol-targeting overlay.

Wraps any base ``Strategy``. Converts the base's bool signals (or weights)
into target weights scaled so the realized portfolio vol approximates a
configured annual target. Capped by ``max_leverage`` to avoid runaway
exposure when realized vol is near zero.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.risk.vol import realized_vol
from src.strategies.base import Strategy


class VolTarget(Strategy):
    name = "vol_target"

    def __init__(
        self,
        base: Strategy,
        target_vol: float = 0.10,
        lookback: int = 20,
        max_leverage: float = 2.0,
    ):
        if target_vol <= 0:
            raise ValueError("target_vol must be > 0")
        if lookback < 2:
            raise ValueError("lookback must be >= 2")
        if max_leverage <= 0:
            raise ValueError("max_leverage must be > 0")
        self.base = base
        self.target_vol = target_vol
        self.lookback = lookback
        self.max_leverage = max_leverage

    def _base_weights(self, close: pd.DataFrame) -> pd.DataFrame:
        w = self.base.weights(close)
        if w is not None:
            return w.astype(float)
        sig = self.base.signals(close)
        if sig is None:
            raise ValueError(f"{type(self.base).__name__} produced neither signals nor weights")
        n_assets = sig.shape[1]
        return sig.astype(float) / n_assets

    def weights(self, close: pd.DataFrame) -> pd.DataFrame:
        base_w = self._base_weights(close)
        returns = close.pct_change().fillna(0.0)
        port_ret = (base_w.shift(1) * returns).sum(axis=1)
        port_vol = realized_vol(port_ret, self.lookback)
        scale = (self.target_vol / port_vol.replace(0.0, np.nan)).clip(upper=self.max_leverage)
        scale = scale.fillna(0.0)
        return base_w.mul(scale, axis=0)
