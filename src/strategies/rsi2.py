"""Connors RSI(2) mean-reversion. Long when RSI(2) < entry, exit when > exit."""
from __future__ import annotations

import pandas as pd

from .base import Strategy


def _rsi(close: pd.DataFrame, period: int) -> pd.DataFrame:
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, pd.NA)
    return 100.0 - 100.0 / (1.0 + rs)


class Rsi2(Strategy):
    name = "rsi2"

    def __init__(self, period: int = 2, entry: float = 5.0, exit: float = 70.0):
        if period < 1:
            raise ValueError("period must be >= 1")
        if entry >= exit:
            raise ValueError("entry must be < exit")
        self.period = period
        self.entry = entry
        self.exit = exit

    def signals(self, close: pd.DataFrame) -> pd.DataFrame:
        import numpy as np

        rsi = _rsi(close, self.period)
        result = {}
        for col in close.columns:
            vals = rsi[col].to_numpy()
            out = np.zeros(len(vals), dtype=bool)
            held = False
            for i, v in enumerate(vals):
                if pd.isna(v):
                    out[i] = held
                    continue
                if not held and v < self.entry:
                    held = True
                elif held and v > self.exit:
                    held = False
                out[i] = held
            result[col] = out
        return pd.DataFrame(result, index=close.index)
