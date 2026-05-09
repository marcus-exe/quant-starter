"""Pull OHLCV bars from yfinance."""
from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf
from loguru import logger


def fetch_ohlcv(
    symbol: str,
    start: str | date,
    end: str | date | None = None,
    interval: str = "1d",
) -> pd.DataFrame:
    logger.info(f"fetch {symbol} {start}->{end} interval={interval}")
    df = yf.download(
        symbol,
        start=start,
        end=end,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )
    if df.empty:
        raise ValueError(f"no data for {symbol}")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.columns = [c.lower() for c in df.columns]
    df.index.name = "date"
    return df
