"""Volatility helpers: realized vol estimation + inverse-vol weights."""
from __future__ import annotations

import numpy as np
import pandas as pd


def realized_vol(returns: pd.DataFrame | pd.Series, lookback: int, annualize: int = 252) -> pd.Series | pd.DataFrame:
    """Rolling realized vol, annualized by sqrt(annualize)."""
    return returns.rolling(lookback).std() * np.sqrt(annualize)


def inverse_vol_weights(returns: pd.DataFrame, lookback: int) -> pd.DataFrame:
    """Per-row weights ∝ 1/vol_i, normalized to sum to 1.

    Rows where any vol is NaN return zeros (insufficient history).
    """
    vol = returns.rolling(lookback).std()
    inv = 1.0 / vol.replace(0.0, np.nan)
    row_sum = inv.sum(axis=1)
    weights = inv.div(row_sum, axis=0)
    valid = vol.notna().all(axis=1)
    return weights.where(valid, 0.0).fillna(0.0)
