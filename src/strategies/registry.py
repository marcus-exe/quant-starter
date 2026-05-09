"""Single source of truth: strategy + overlay name → class."""
from __future__ import annotations

from src.strategies.base import Strategy
from src.strategies.bollinger import BollingerFade
from src.strategies.donchian import Donchian
from src.strategies.momentum import TimeSeriesMomentum
from src.strategies.pairs import Pairs
from src.strategies.rsi2 import Rsi2
from src.strategies.seasonality import TurnOfMonth
from src.strategies.sma_cross import SmaCross
from src.strategies.overlays.risk_parity import RiskParity
from src.strategies.overlays.vol_target import VolTarget
from src.strategies.vix_carry import VixCarry
from src.strategies.xsmom import CrossSectionalMomentum

STRATEGIES: dict[str, type[Strategy]] = {
    "sma_cross": SmaCross,
    "tsmom": TimeSeriesMomentum,
    "xsmom": CrossSectionalMomentum,
    "rsi2": Rsi2,
    "bollinger_fade": BollingerFade,
    "donchian": Donchian,
    "turn_of_month": TurnOfMonth,
    "vix_carry": VixCarry,
    "pairs": Pairs,
}

OVERLAYS: dict[str, type[Strategy]] = {
    "vol_target": VolTarget,
    "risk_parity": RiskParity,
}
