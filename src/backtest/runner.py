"""vectorbt backtest wrapper."""
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
    prices: pd.DataFrame,
    strategy: Strategy,
    init_cash: float = 100_000,
    fees: float = 0.0005,
    slippage: float = 0.0005,
) -> BacktestResult:
    sig = strategy.signals(prices)
    entries = sig & ~sig.shift(1, fill_value=False)
    exits = ~sig & sig.shift(1, fill_value=False)

    pf = vbt.Portfolio.from_signals(
        prices["close"],
        entries=entries,
        exits=exits,
        init_cash=init_cash,
        fees=fees,
        slippage=slippage,
        freq="1D",
    )

    return BacktestResult(
        total_return=float(pf.total_return()),
        sharpe=float(pf.sharpe_ratio()),
        max_drawdown=float(pf.max_drawdown()),
        n_trades=int(pf.trades.count()),
        portfolio=pf,
    )
