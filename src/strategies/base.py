"""Strategy ABC.

Inputs: wide close DataFrame (index=ts, columns=symbols).
Outputs: bool DataFrame same shape — True = long, False = flat — per (ts, symbol).

Single-asset = single-column DataFrame.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    name: str

    @abstractmethod
    def signals(self, close: pd.DataFrame) -> pd.DataFrame:
        ...
