"""Bollinger band fade. Long when close < lower band, exit at middle."""
from __future__ import annotations

import pandas as pd

from .base import Strategy


class BollingerFade(Strategy):
    name = "bollinger_fade"

    def __init__(self, period: int = 20, n_std: float = 2.0):
        if period < 2:
            raise ValueError("period must be >= 2")
        if n_std <= 0:
            raise ValueError("n_std must be > 0")
        self.period = period
        self.n_std = n_std

    def signals(self, close: pd.DataFrame) -> pd.DataFrame:
        import numpy as np

        mid = close.rolling(self.period).mean()
        std = close.rolling(self.period).std()
        lower = mid - self.n_std * std

        below_lower = (close < lower).fillna(False)
        above_mid = (close > mid).fillna(False)

        result = {}
        for col in close.columns:
            lo = below_lower[col].to_numpy()
            hi = above_mid[col].to_numpy()
            out = np.zeros(len(close), dtype=bool)
            held = False
            for i in range(len(close)):
                if not held and lo[i]:
                    held = True
                elif held and hi[i]:
                    held = False
                out[i] = held
            result[col] = out
        return pd.DataFrame(result, index=close.index)
