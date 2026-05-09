"""OHLCV persistence: TimescaleDB primary, Parquet export optional."""
from __future__ import annotations

from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.db.engine import engine, get_session
from src.db.models import Bar

DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"


def _to_records(df: pd.DataFrame, symbol: str, interval: str) -> list[dict]:
    out = df.reset_index().rename(columns={"date": "ts", "Date": "ts", "Datetime": "ts"})
    out["ts"] = pd.to_datetime(out["ts"], utc=True)
    out["symbol"] = symbol
    out["interval"] = interval
    cols = ["symbol", "interval", "ts", "open", "high", "low", "close", "volume"]
    out = out[cols]
    return out.to_dict(orient="records")


def save(df: pd.DataFrame, symbol: str, interval: str = "1d") -> int:
    """Upsert bars into Timescale. Returns row count written."""
    records = _to_records(df, symbol, interval)
    if not records:
        return 0
    stmt = pg_insert(Bar).values(records)
    stmt = stmt.on_conflict_do_update(
        index_elements=["symbol", "interval", "ts"],
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "volume": stmt.excluded.volume,
        },
    )
    with get_session() as s:
        s.execute(stmt)
    return len(records)


def load(
    symbol: str,
    interval: str = "1d",
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
) -> pd.DataFrame:
    stmt = select(Bar).where(Bar.symbol == symbol, Bar.interval == interval)
    if start is not None:
        stmt = stmt.where(Bar.ts >= pd.Timestamp(start, tz="UTC"))
    if end is not None:
        stmt = stmt.where(Bar.ts <= pd.Timestamp(end, tz="UTC"))
    stmt = stmt.order_by(Bar.ts)
    df = pd.read_sql(stmt, engine, parse_dates=["ts"])
    if df.empty:
        return df
    df = df.drop(columns=["symbol", "interval"]).set_index("ts")
    return df


def get_or_fetch(
    symbol: str,
    start: str | pd.Timestamp,
    end: str | pd.Timestamp | None = None,
    interval: str = "1d",
) -> pd.DataFrame:
    """DB-first cache. Hit DB; on miss, fetch from vendor, persist, reload."""
    df = load(symbol, interval, start=start, end=end)
    if not df.empty:
        return df
    from src.data.fetch import fetch_ohlcv

    raw = fetch_ohlcv(symbol, start, end, interval)
    save(raw, symbol, interval)
    return load(symbol, interval, start=start, end=end)


def export_parquet(symbol: str, interval: str = "1d") -> Path:
    """Dump symbol/interval slice to Parquet under data/raw/."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{symbol}_{interval}.parquet"
    load(symbol, interval).to_parquet(path)
    return path
