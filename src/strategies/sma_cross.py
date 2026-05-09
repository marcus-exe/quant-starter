"""SMA crossover. Operates per symbol on wide close DataFrame."""
from __future__ import annotations

import pandas as pd

from .base import Strategy


class SmaCross(Strategy):
    name = "sma_cross"

    def __init__(self, fast: int = 50, slow: int = 200):
        if fast >= slow:
            raise ValueError("fast must be < slow")
        self.fast = fast
        self.slow = slow

    def signals(self, close: pd.DataFrame) -> pd.DataFrame:
        fast_ma = close.rolling(self.fast).mean()
        slow_ma = close.rolling(self.slow).mean()
        return (fast_ma > slow_ma).fillna(False)
