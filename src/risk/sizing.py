"""Position sizing utilities."""
from __future__ import annotations


def fixed_fraction(equity: float, fraction: float, price: float) -> int:
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    return int((equity * fraction) // price)


def kelly(win_prob: float, win_loss_ratio: float, cap: float = 0.25) -> float:
    """Kelly fraction with cap. b = win/loss ratio."""
    if not 0 < win_prob < 1:
        raise ValueError("win_prob in (0,1)")
    f = win_prob - (1 - win_prob) / win_loss_ratio
    return max(0.0, min(f, cap))
