"""Strategy ABC. Returns long/flat signal series aligned to price index."""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    name: str

    @abstractmethod
    def signals(self, prices: pd.DataFrame) -> pd.Series:
        """Return boolean Series: True = long, False = flat."""
