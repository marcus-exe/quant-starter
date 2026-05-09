"""vectorbt backtest wrapper. Two paths:

- ``signals()`` bool DataFrame → ``Portfolio.from_signals`` (long-only).
- ``weights()`` float DataFrame → ``Portfolio.from_orders`` (long/short, scaled).

The path is chosen per ``Strategy`` instance: ``weights()`` wins if non-None.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
import vectorbt as vbt

from src.strategies.base import Strategy


@dataclass
class BacktestResult:
    total_return: float
    sharpe: float
    max_drawdown: float
    n_trades: int
    portfolio: vbt.Portfolio

    def summary(self) -> str:
        return (
            f"return={self.total_return:.2%} "
            f"sharpe={self.sharpe:.2f} "
            f"mdd={self.max_drawdown:.2%} "
            f"trades={self.n_trades}"
        )


def _scalar(v) -> float:
    return float(v.iloc[0]) if hasattr(v, "iloc") else float(v)


def _n_trades(pf: vbt.Portfolio) -> int:
    n = pf.trades.count()
    if hasattr(n, "sum"):
        n = int(n.sum())
    return int(n)


def _from_signals(close: pd.DataFrame, sig: pd.DataFrame, **kwargs) -> vbt.Portfolio:
    entries = sig & ~sig.shift(1, fill_value=False)
    exits = ~sig & sig.shift(1, fill_value=False)
    n_assets = close.shape[1]
    extra = {}
    if n_assets > 1:
        extra = dict(cash_sharing=True, group_by=True, size=1.0 / n_assets, size_type="percent")
    return vbt.Portfolio.from_signals(close=close, entries=entries, exits=exits, **kwargs, **extra)


def _from_weights(close: pd.DataFrame, w: pd.DataFrame, **kwargs) -> vbt.Portfolio:
    """Translate target weights into rebalance orders.

    Only ``w`` rows where weights change vs prior bar produce orders;
    otherwise the position drifts. ``cash_sharing=True`` is required when
    weights span multiple assets so the group budget is honored.
    """
    w = w.reindex(index=close.index, columns=close.columns).fillna(0.0)
    prev = w.shift(1).fillna(0.0)
    changed = (w != prev).any(axis=1).to_numpy()
    arr = w.to_numpy().copy()
    arr[~changed, :] = np.nan
    target = pd.DataFrame(arr, index=close.index, columns=close.columns)
    return vbt.Portfolio.from_orders(
        close=close,
        size=target,
        size_type="targetpercent",
        cash_sharing=True,
        group_by=True,
        **kwargs,
    )


def run(
    close: pd.DataFrame,
    strategy: Strategy,
    init_cash: float = 100_000,
    fees: float = 0.0005,
    slippage: float = 0.0005,
) -> BacktestResult:
    common = dict(init_cash=init_cash, fees=fees, slippage=slippage, freq="1D")

    w = strategy.weights(close)
    if w is not None:
        pf = _from_weights(close, w, **common)
    else:
        sig = strategy.signals(close)
        if sig is None:
            raise ValueError(
                f"{type(strategy).__name__} returned None for both signals() and weights()"
            )
        pf = _from_signals(close, sig, **common)

    return BacktestResult(
        total_return=_scalar(pf.total_return()),
        sharpe=_scalar(pf.sharpe_ratio()),
        max_drawdown=_scalar(pf.max_drawdown()),
        n_trades=_n_trades(pf),
        portfolio=pf,
    )
