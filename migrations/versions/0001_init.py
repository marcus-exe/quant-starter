"""init schema + timescale hypertable

Revision ID: 0001_init
Revises:
Create Date: 2026-05-08

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")

    op.create_table(
        "bars",
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("interval", sa.String(8), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("open", sa.Numeric(18, 6), nullable=False),
        sa.Column("high", sa.Numeric(18, 6), nullable=False),
        sa.Column("low", sa.Numeric(18, 6), nullable=False),
        sa.Column("close", sa.Numeric(18, 6), nullable=False),
        sa.Column("volume", sa.Numeric(24, 4), nullable=False, server_default="0"),
        sa.PrimaryKeyConstraint("symbol", "interval", "ts"),
    )
    op.execute(
        "SELECT create_hypertable('bars', 'ts', chunk_time_interval => INTERVAL '30 days');"
    )
    op.create_index("ix_bars_symbol_interval_ts", "bars", ["symbol", "interval", "ts"])

    op.create_table(
        "strategy_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("strategy", sa.String(64), nullable=False),
        sa.Column("config_hash", sa.String(64), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("params", postgresql.JSONB, nullable=False, server_default="{}"),
        sa.Column("metrics", postgresql.JSONB, nullable=False, server_default="{}"),
    )
    op.create_index("ix_strategy_runs_strategy", "strategy_runs", ["strategy"])

    op.create_table(
        "trades",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("strategy_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("side", sa.String(4), nullable=False),
        sa.Column("qty", sa.Numeric(24, 8), nullable=False),
        sa.Column("price", sa.Numeric(18, 6), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("fee", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("pnl", sa.Numeric(18, 6), nullable=False, server_default="0"),
        sa.Column("meta", sa.JSON, nullable=False, server_default="{}"),
    )
    op.create_index("ix_trades_run_id", "trades", ["run_id"])
    op.create_index("ix_trades_symbol", "trades", ["symbol"])
    op.create_index("ix_trades_ts", "trades", ["ts"])

    op.create_table(
        "positions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column(
            "run_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("strategy_runs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("qty", sa.Numeric(24, 8), nullable=False),
        sa.Column("avg_price", sa.Numeric(18, 6), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("pnl", sa.Numeric(18, 6), nullable=False, server_default="0"),
    )
    op.create_index("ix_positions_run_id", "positions", ["run_id"])
    op.create_index("ix_positions_symbol", "positions", ["symbol"])


def downgrade() -> None:
    op.drop_table("positions")
    op.drop_table("trades")
    op.drop_table("strategy_runs")
    op.drop_table("bars")
