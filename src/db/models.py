"""ORM models. Bars is a Timescale hypertable created in migration 0001."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.engine import Base


class Bar(Base):
    __tablename__ = "bars"
    __table_args__ = (PrimaryKeyConstraint("symbol", "interval", "ts"),)

    symbol: Mapped[str] = mapped_column(String(32), nullable=False)
    interval: Mapped[str] = mapped_column(String(8), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    open: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    high: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    low: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    close: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    volume: Mapped[float] = mapped_column(Numeric(24, 4), nullable=False, default=0)


class StrategyRun(Base):
    __tablename__ = "strategy_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    strategy: Mapped[str] = mapped_column(String(64), nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    params: Mapped[dict] = mapped_column(JSONB, default=dict)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict)

    trades: Mapped[list["Trade"]] = relationship(back_populates="run", cascade="all, delete-orphan")
    positions: Mapped[list["Position"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("strategy_runs.id", ondelete="CASCADE"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    side: Mapped[str] = mapped_column(String(4), nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    fee: Mapped[float] = mapped_column(Numeric(18, 6), default=0)
    pnl: Mapped[float] = mapped_column(Numeric(18, 6), default=0)
    meta: Mapped[dict] = mapped_column(JSON, default=dict)

    run: Mapped[StrategyRun] = relationship(back_populates="trades")


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("strategy_runs.id", ondelete="CASCADE"), index=True
    )
    symbol: Mapped[str] = mapped_column(String(32), index=True, nullable=False)
    qty: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    avg_price: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    pnl: Mapped[float] = mapped_column(Numeric(18, 6), default=0)

    run: Mapped[StrategyRun] = relationship(back_populates="positions")
