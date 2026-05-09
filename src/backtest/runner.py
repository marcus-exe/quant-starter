"""vectorbt backtest wrapper. Single + multi-asset via wide close DataFrame."""
from __future__ import annotations

from dataclasses import dataclass

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


def run(
    close: pd.DataFrame,
    strategy: Strategy,
    init_cash: float = 100_000,
    fees: float = 0.0005,
    slippage: float = 0.0005,
) -> BacktestResult:
    """`close` is a wide DataFrame (cols=symbols). 1 col = single asset.

    Multi-asset = grouped portfolio, equal-weight per active signal,
    cash shared across the group.
    """
    sig = strategy.signals(close)
    entries = sig & ~sig.shift(1, fill_value=False)
    exits = ~sig & sig.shift(1, fill_value=False)

    n_assets = close.shape[1]
    multi = n_assets > 1

    kwargs = dict(
        close=close,
        entries=entries,
        exits=exits,
        init_cash=init_cash,
        fees=fees,
        slippage=slippage,
        freq="1D",
    )
    if multi:
        kwargs.update(
            cash_sharing=True,
            group_by=True,
            size=1.0 / n_assets,
            size_type="percent",
        )

    pf = vbt.Portfolio.from_signals(**kwargs)

    def _scalar(v) -> float:
        return float(v.iloc[0]) if hasattr(v, "iloc") else float(v)

    n_trades = pf.trades.count()
    if hasattr(n_trades, "sum"):
        n_trades = int(n_trades.sum())

    return BacktestResult(
        total_return=_scalar(pf.total_return()),
        sharpe=_scalar(pf.sharpe_ratio()),
        max_drawdown=_scalar(pf.max_drawdown()),
        n_trades=int(n_trades),
        portfolio=pf,
    )
