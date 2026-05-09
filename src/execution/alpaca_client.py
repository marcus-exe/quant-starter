"""Thin Alpaca wrapper for paper trading."""
from __future__ import annotations

import os
from dataclasses import dataclass

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest


@dataclass
class AlpacaConfig:
    api_key: str
    secret_key: str
    paper: bool = True

    @classmethod
    def from_env(cls) -> AlpacaConfig:
        return cls(
            api_key=os.environ["ALPACA_API_KEY"],
            secret_key=os.environ["ALPACA_SECRET_KEY"],
            paper="paper" in os.environ.get("ALPACA_BASE_URL", "paper"),
        )


def client(cfg: AlpacaConfig | None = None) -> TradingClient:
    cfg = cfg or AlpacaConfig.from_env()
    return TradingClient(cfg.api_key, cfg.secret_key, paper=cfg.paper)


def submit_market(symbol: str, qty: float, side: OrderSide, c: TradingClient) -> str:
    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=side,
        time_in_force=TimeInForce.DAY,
    )
    resp = c.submit_order(order)
    return str(resp.id)
