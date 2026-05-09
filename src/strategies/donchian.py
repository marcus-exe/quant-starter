"""Donchian breakout (Turtle-style). Enter on N-day high, exit on M-day low."""
from __future__ import annotations

import pandas as pd

from .base import Strategy


class Donchian(Strategy):
    name = "donchian"

    def __init__(self, entry_lookback: int = 20, exit_lookback: int = 10):
        if entry_lookback < 2:
            raise ValueError("entry_lookback must be >= 2")
        if exit_lookback < 1:
            raise ValueError("exit_lookback must be >= 1")
        if exit_lookback >= entry_lookback:
            raise ValueError("exit_lookback must be < entry_lookback")
        self.entry_lookback = entry_lookback
        self.exit_lookback = exit_lookback

    def signals(self, close: pd.DataFrame) -> pd.DataFrame:
        import numpy as np

        prior_high = close.shift(1).rolling(self.entry_lookback).max()
        prior_low = close.shift(1).rolling(self.exit_lookback).min()

        breakout_up = (close > prior_high).fillna(False)
        breakout_dn = (close < prior_low).fillna(False)

        result = {}
        for col in close.columns:
            up = breakout_up[col].to_numpy()
            dn = breakout_dn[col].to_numpy()
            out = np.zeros(len(close), dtype=bool)
            held = False
            for i in range(len(close)):
                if not held and up[i]:
                    held = True
                elif held and dn[i]:
                    held = False
                out[i] = held
            result[col] = out
        return pd.DataFrame(result, index=close.index)
