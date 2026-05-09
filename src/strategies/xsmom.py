"""Cross-sectional momentum (XSMOM).

Each bar: rank universe by past `lookback` return (skipping last `skip` bars).
Long top `top_n` symbols, flat the rest. Rebalances daily on rank change.
"""
from __future__ import annotations

import pandas as pd

from .base import Strategy


class CrossSectionalMomentum(Strategy):
    name = "xsmom"

    def __init__(self, lookback: int = 252, skip: int = 21, top_n: int = 3):
        if lookback <= skip:
            raise ValueError("lookback must be > skip")
        if top_n < 1:
            raise ValueError("top_n must be >= 1")
        self.lookback = lookback
        self.skip = skip
        self.top_n = top_n

    def signals(self, close: pd.DataFrame) -> pd.DataFrame:
        past = close.shift(self.skip)
        ref = close.shift(self.lookback)
        ret = past / ref - 1.0
        ranks = ret.rank(axis=1, ascending=False, method="first")
        return (ranks <= self.top_n).fillna(False)
