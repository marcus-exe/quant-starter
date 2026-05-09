"""CLI: python scripts/backtest.py --config configs/sma_cross.yaml"""
from __future__ import annotations

import hashlib
import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import click
import yaml
from loguru import logger

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.runner import run
from src.data.store import get_or_fetch
from src.db.engine import get_session
from src.db.models import StrategyRun
from src.strategies.sma_cross import SmaCross

STRATEGIES = {"sma_cross": SmaCross}


def _config_hash(cfg: dict) -> str:
    return hashlib.sha256(json.dumps(cfg, sort_keys=True, default=str).encode()).hexdigest()[:16]


@click.command()
@click.option("--config", "-c", required=True, type=click.Path(exists=True))
def main(config: str) -> None:
    cfg = yaml.safe_load(Path(config).read_text())

    strat_cls = STRATEGIES[cfg["strategy"]]
    strategy = strat_cls(**cfg["params"])

    u = cfg["universe"]
    prices = get_or_fetch(u["symbol"], u["start"], u.get("end"), u.get("interval", "1d"))

    started = datetime.now(timezone.utc)
    result = run(prices, strategy, **cfg["backtest"])
    finished = datetime.now(timezone.utc)

    run_id = uuid.uuid4()
    metrics = {
        "total_return": result.total_return,
        "sharpe": result.sharpe,
        "max_drawdown": result.max_drawdown,
        "n_trades": result.n_trades,
        "symbol": u["symbol"],
    }
    with get_session() as s:
        s.add(
            StrategyRun(
                id=run_id,
                strategy=cfg["strategy"],
                config_hash=_config_hash(cfg),
                started_at=started,
                finished_at=finished,
                params={**cfg["params"], **cfg["backtest"], "universe": u},
                metrics=metrics,
            )
        )

    logger.info(f"{cfg['strategy']} on {u['symbol']}: {result.summary()}")
    logger.info(f"run_id={run_id}")


if __name__ == "__main__":
    main()
