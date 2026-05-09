"""Cointegration-based pairs trading on 2 symbols.

Rolling OLS hedge ratio β; spread = a - β·b. Z-score on rolling mean/std.
Long spread (long a, short β·b) when z < -entry; short spread when z > +entry.
Flat when |z| < exit. Emits continuous weights — runs through the
``from_orders`` path of the backtest runner.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Strategy


def _rolling_beta(a: pd.Series, b: pd.Series, window: int) -> pd.Series:
    cov = a.rolling(window).cov(b)
    var = b.rolling(window).var()
    return (cov / var.replace(0.0, np.nan)).astype(float)


class Pairs(Strategy):
    name = "pairs"

    def __init__(
        self,
        window: int = 60,
        entry_z: float = 2.0,
        exit_z: float = 0.5,
        leg_size: float = 0.5,
    ):
        if window < 10:
            raise ValueError("window must be >= 10")
        if entry_z <= 0 or exit_z < 0:
            raise ValueError("entry_z>0 and exit_z>=0 required")
        if exit_z >= entry_z:
            raise ValueError("exit_z must be < entry_z")
        if not 0 < leg_size <= 1:
            raise ValueError("leg_size must be in (0, 1]")
        self.window = window
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.leg_size = leg_size

    def weights(self, close: pd.DataFrame) -> pd.DataFrame:
        if close.shape[1] != 2:
            raise ValueError(f"Pairs expects exactly 2 columns, got {close.shape[1]}")
        a_col, b_col = close.columns
        a = close[a_col].astype(float)
        b = close[b_col].astype(float)

        beta = _rolling_beta(a, b, self.window)
        spread = a - beta * b
        mean = spread.rolling(self.window).mean()
        std = spread.rolling(self.window).std()
        z = ((spread - mean) / std.replace(0.0, np.nan)).astype(float)

        z_arr = z.to_numpy()
        beta_arr = beta.to_numpy()

        n = len(close)
        w_a = np.zeros(n)
        w_b = np.zeros(n)
        position = 0  # +1 = long spread, -1 = short spread, 0 = flat

        for i in range(n):
            zi = z_arr[i]
            bi = beta_arr[i]
            if np.isnan(zi) or np.isnan(bi):
                w_a[i] = 0.0
                w_b[i] = 0.0
                continue

            if position == 0:
                if zi < -self.entry_z:
                    position = +1
                elif zi > +self.entry_z:
                    position = -1
            elif position == +1 and zi >= -self.exit_z:
                position = 0
            elif position == -1 and zi <= +self.exit_z:
                position = 0

            if position == +1:
                w_a[i] = +self.leg_size
                w_b[i] = -self.leg_size * bi
            elif position == -1:
                w_a[i] = -self.leg_size
                w_b[i] = +self.leg_size * bi

        return pd.DataFrame({a_col: w_a, b_col: w_b}, index=close.index)
