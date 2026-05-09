"""Inverse-volatility (a.k.a. naive risk parity) overlay.

Replaces the equal-weight default that the runner applies to multi-asset
bool signals with weights ∝ 1/vol_i, normalized over only the assets
that the base strategy says are active on each row.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.strategies.base import Strategy


class RiskParity(Strategy):
    name = "risk_parity"

    def __init__(self, base: Strategy, lookback: int = 60):
        if lookback < 5:
            raise ValueError("lookback must be >= 5")
        self.base = base
        self.lookback = lookback

    def weights(self, close: pd.DataFrame) -> pd.DataFrame:
        sig = self.base.signals(close)
        if sig is None:
            base_w = self.base.weights(close)
            if base_w is None:
                raise ValueError(
                    f"{type(self.base).__name__} produced neither signals nor weights"
                )
            sig = base_w != 0

        active = sig.astype(bool)
        returns = close.pct_change()
        vol = returns.rolling(self.lookback).std()
        inv_vol = (1.0 / vol.replace(0.0, np.nan)).where(active, 0.0)
        row_sum = inv_vol.sum(axis=1)
        weights = inv_vol.div(row_sum.replace(0.0, np.nan), axis=0)
        return weights.fillna(0.0)
