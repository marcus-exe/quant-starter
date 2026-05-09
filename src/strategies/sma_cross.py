"""Classic 50/200 SMA crossover."""
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

    def signals(self, prices: pd.DataFrame) -> pd.Series:
        close = prices["close"]
        fast_ma = close.rolling(self.fast).mean()
        slow_ma = close.rolling(self.slow).mean()
        return (fast_ma > slow_ma).fillna(False)
