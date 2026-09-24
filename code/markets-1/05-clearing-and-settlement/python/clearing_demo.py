"""Netting, margin and the default waterfall (Chapter 5). Parameters illustrative."""
import math
from collections import defaultdict
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Trade:
    buyer: str
    seller: str
    symbol: str
    quantity: int
    price: float


def net_obligations(trades: list[Trade]):
    """Per member: net shares to receive (+) or deliver (-) per symbol, and net cash (+ receives)."""
    shares: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    cash: dict[str, float] = defaultdict(float)
    for t in trades:
        shares[t.buyer][t.symbol] += t.quantity
        shares[t.seller][t.symbol] -= t.quantity
        cash[t.buyer] -= t.quantity * t.price
        cash[t.seller] += t.quantity * t.price
    return {m: dict(s) for m, s in shares.items()}, dict(cash)


def netting_efficiency(trades: list[Trade]) -> float:
    """1 - (value that settles after multilateral netting) / (gross value traded)."""
    gross = sum(t.quantity * t.price for t in trades)
    _, cash = net_obligations(trades)
    net = sum(c for c in cash.values() if c > 0)
    return 1.0 - net / gross


def initial_margin(position_value: float, sigma_daily: float, days: float, z: float = 2.326) -> float:
    """A value-at-risk margin: z standard deviations over the margin period of risk."""
    return abs(position_value) * z * sigma_daily * math.sqrt(days)


@dataclass(frozen=True)
class Waterfall:
    defaulter_margin: float
    defaulter_fund: float
    ccp_capital: float
    survivors_fund: float
    assessments: float

    def layers(self):
        return (("defaulter's margin", self.defaulter_margin),
                ("defaulter's fund contribution", self.defaulter_fund),
                ("clearing house's own capital", self.ccp_capital),
                ("survivors' fund contributions", self.survivors_fund),
                ("assessments on survivors", self.assessments))

    def allocate(self, loss: float) -> dict[str, float]:
        out, left = {}, loss
        for name, size in self.layers():
            used = min(left, size)
            out[name] = used
            left -= used
        out["uncovered"] = left
        return out


def random_trades(n: int, members: int, seed: int, symbols: int = 5) -> list[Trade]:
    rng = np.random.default_rng(seed)
    names = [chr(65 + i) for i in range(members)]
    out = []
    for _ in range(n):
        b, s = rng.choice(members, size=2, replace=False)
        k = int(rng.integers(symbols))
        out.append(Trade(names[b], names[s], f"S{k}", int(rng.integers(1, 20)) * 100, 20.0 + 10 * k))
    return out
