"""Turn-of-month seasonality. Long last N + first M trading days of each month."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .base import Strategy


class TurnOfMonth(Strategy):
    name = "turn_of_month"

    def __init__(self, days_end: int = 4, days_start: int = 3):
        if days_end < 0 or days_start < 0:
            raise ValueError("days_end and days_start must be >= 0")
        if days_end + days_start == 0:
            raise ValueError("at least one window must be > 0")
        self.days_end = days_end
        self.days_start = days_start

    def signals(self, close: pd.DataFrame) -> pd.DataFrame:
        idx = close.index
        period = pd.PeriodIndex(idx, freq="M")
        rank_in_month = pd.Series(idx, index=idx).groupby(period).cumcount()
        size_per_month = rank_in_month.groupby(period).transform("max") + 1
        last_n = (size_per_month - rank_in_month) <= self.days_end
        first_m = rank_in_month < self.days_start
        active = (last_n | first_m).to_numpy()
        return pd.DataFrame(
            np.broadcast_to(active[:, None], (len(idx), len(close.columns))).copy(),
            index=idx,
            columns=close.columns,
        )
