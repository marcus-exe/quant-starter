"""VIX term-structure carry. Long the target (e.g. SVXY) when VIX < VIX3M.

Contango = front month cheaper than back month → SVXY collects positive roll.
Backwardation = expensive front → step aside (vol crush risk, e.g. Feb 2018).

Fetches the two VIX series internally so a single-asset config (SVXY only)
is enough — caller doesn't need to wire the proxies into the universe.
"""
from __future__ import annotations

import pandas as pd

from src.data.store import get_or_fetch

from .base import Strategy


class VixCarry(Strategy):
    name = "vix_carry"

    def __init__(
        self,
        target: str = "SVXY",
        short_proxy: str = "^VIX",
        long_proxy: str = "^VIX3M",
        smooth: int = 5,
    ):
        if smooth < 1:
            raise ValueError("smooth must be >= 1")
        self.target = target
        self.short_proxy = short_proxy
        self.long_proxy = long_proxy
        self.smooth = smooth

    def _term_ratio(self, index: pd.DatetimeIndex) -> pd.Series:
        start = index.min().date().isoformat()
        end = index.max().date().isoformat()
        vix = get_or_fetch(self.short_proxy, start, end)["close"].astype(float)
        vix3m = get_or_fetch(self.long_proxy, start, end)["close"].astype(float)
        ratio = (vix / vix3m).rolling(self.smooth).mean()
        return ratio.reindex(index, method="ffill")

    def signals(self, close: pd.DataFrame) -> pd.DataFrame:
        if self.target not in close.columns:
            raise ValueError(f"target {self.target!r} missing from close columns")
        ratio = self._term_ratio(close.index)
        contango = (ratio < 1.0).fillna(False)
        out = pd.DataFrame(False, index=close.index, columns=close.columns)
        out[self.target] = contango.to_numpy()
        return out
