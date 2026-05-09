"""Paper trading loop. Run during market hours.

Usage: python scripts/live_paper.py --config configs/sma_cross.yaml
"""
from __future__ import annotations

import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

import click
import yaml
from alpaca.trading.enums import OrderSide
from dotenv import load_dotenv
from loguru import logger

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.fetch import fetch_ohlcv
from src.execution.alpaca_client import client, submit_market
from src.risk.sizing import fixed_fraction
from src.strategies.sma_cross import SmaCross

STRATEGIES = {"sma_cross": SmaCross}
POLL_SEC = 300


@click.command()
@click.option("--config", "-c", required=True, type=click.Path(exists=True))
@click.option("--fraction", default=0.1, help="equity fraction per entry")
def main(config: str, fraction: float) -> None:
    load_dotenv()
    cfg = yaml.safe_load(Path(config).read_text())
    strat_cls = STRATEGIES[cfg["strategy"]]
    strategy = strat_cls(**cfg["params"])
    symbol = cfg["universe"]["symbol"]

    api = client()
    logger.info(f"paper trading {symbol} via {cfg['strategy']}")

    last_signal: bool | None = None
    while True:
        end = datetime.utcnow().date()
        start = end - timedelta(days=max(cfg["params"].values()) * 2)
        prices = fetch_ohlcv(symbol, start, end)
        sig = bool(strategy.signals(prices).iloc[-1])

        if last_signal is None:
            last_signal = sig
            logger.info(f"initial signal={sig}")
        elif sig != last_signal:
            account = api.get_account()
            equity = float(account.equity)
            price = float(prices["close"].iloc[-1])

            if sig:
                qty = fixed_fraction(equity, fraction, price)
                if qty > 0:
                    oid = submit_market(symbol, qty, OrderSide.BUY, api)
                    logger.info(f"BUY {qty} {symbol} @ ~{price} order={oid}")
            else:
                positions = {p.symbol: float(p.qty) for p in api.get_all_positions()}
                qty = positions.get(symbol, 0)
                if qty > 0:
                    oid = submit_market(symbol, qty, OrderSide.SELL, api)
                    logger.info(f"SELL {qty} {symbol} @ ~{price} order={oid}")
            last_signal = sig

        time.sleep(POLL_SEC)


if __name__ == "__main__":
    main()
