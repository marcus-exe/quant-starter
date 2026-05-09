"""Strategy ABC.

Subclasses override exactly one of:

- ``signals(close) -> bool DataFrame`` — long-only on/off per (ts, symbol).
  Wired to ``vbt.Portfolio.from_signals`` (equal-weight on multi-asset).
- ``weights(close) -> float DataFrame`` — continuous target weights in
  ``[-1, +1]`` per (ts, symbol). Negative = short, NaN/0 = flat.
  Wired to ``vbt.Portfolio.from_orders`` with ``size_type=targetpercent``.

Inputs: wide close DataFrame (index=ts, columns=symbols).
Single-asset = single-column DataFrame.
"""
from __future__ import annotations

import pandas as pd


class Strategy:
    name: str

    def signals(self, close: pd.DataFrame) -> pd.DataFrame | None:
        """Override to emit bool long-only signals. Default returns None."""
        return None

    def weights(self, close: pd.DataFrame) -> pd.DataFrame | None:
        """Override to emit continuous weights. Default returns None."""
        return None
