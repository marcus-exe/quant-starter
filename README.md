# Finances — Quant Trading Starter

Personal quant research + paper trading sandbox.

## Stack

- Python 3.11+, `vectorbt` backtests
- TimescaleDB (Postgres + time-series ext) — primary store
- MinIO (S3-compat) — Parquet/tick archival
- pgAdmin — DB browser
- Jupyter Lab — research
- yfinance / Polygon — data
- Alpaca — paper/live exec

## Layout

```
src/
  data/         # fetch + DB store layer
  db/           # SQLAlchemy engine + models
  strategies/   # strategy implementations
  backtest/     # vectorbt runner
  execution/    # Alpaca client
  risk/         # position sizing
migrations/     # Alembic
scripts/        # CLI entrypoints
configs/        # per-strategy YAML
notebooks/      # research / EDA
tests/          # pytest
data/           # parquet exports (gitignored)
```

## Setup

```bash
cp .env.example .env             # add API keys
docker compose up -d db pgadmin minio jupyter
uv python pin 3.11               # vectorbt/numba break on 3.13
uv sync                          # install python deps locally
uv run alembic upgrade head      # create schema + hypertable
```

Services:
- DB: `localhost:5432` (user/pass `quant`/`quant`)
- pgAdmin: http://localhost:5050 (admin@local / admin)
- MinIO: http://localhost:9001 (minio / minio12345)
- Jupyter: http://localhost:8888 (token `quant`)

## Run

Backtest:
```bash
uv run python scripts/backtest.py --config configs/sma_cross.yaml
```

Paper trade:
```bash
uv run python scripts/live_paper.py --config configs/sma_cross.yaml
```

Run inside container instead:
```bash
docker compose --profile app run --rm app uv run python scripts/backtest.py --config configs/sma_cross.yaml
```

## Data + Runs

OHLCV bars cached in Timescale (`bars` hypertable). First backtest hits yfinance, persists, subsequent runs read from DB only.

Each backtest writes a row to `strategy_runs` with `params`, `metrics`, `config_hash`, timestamps.

Query bars:
```bash
uv run python -c "from src.data.store import load; print(load('SPY').tail())"
```

Query runs:
```bash
uv run python -c "
from src.db.engine import get_session
from src.db.models import StrategyRun
with get_session() as s:
    for r in s.query(StrategyRun).order_by(StrategyRun.started_at.desc()).limit(5):
        print(r.id, r.strategy, r.metrics)
"
```

Force refresh from vendor (delete cached bars first):
```sql
DELETE FROM bars WHERE symbol = 'SPY' AND interval = '1d';
```

## Migrations

```bash
uv run alembic revision --autogenerate -m "msg"
uv run alembic upgrade head
uv run alembic downgrade -1
```

## First Strategy

`sma_cross` — 50/200 SMA crossover on SPY. Scaffold smoke test, not investment advice.

## Roadmap

1. Paper trade SMA cross via Alpaca
2. Add momentum + mean-reversion strategies
3. Walk-forward validation
4. Risk parity portfolio across strats
5. Live tiny capital
