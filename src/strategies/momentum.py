"""Time-series momentum (TSMOM). Per-symbol on wide close DataFrame."""
from __future__ import annotations

import pandas as pd

from .base import Strategy


class TimeSeriesMomentum(Strategy):
    name = "tsmom"

    def __init__(self, lookback: int = 252, skip: int = 21, threshold: float = 0.0):
        if lookback <= skip:
            raise ValueError("lookback must be > skip")
        self.lookback = lookback
        self.skip = skip
        self.threshold = threshold

    def signals(self, close: pd.DataFrame) -> pd.DataFrame:
        past = close.shift(self.skip)
        ref = close.shift(self.lookback)
        ret = past / ref - 1.0
        return (ret > self.threshold).fillna(False)
