"""Execution-quality statistics on simulated retail and institutional flow (Chapter 10).

All prices in cents. For a trade of side e (+1 buy), price p, mid m at execution and mid m_tau
a horizon tau later:
    effective half-spread  e (p - m)
    realised half-spread   e (p - m_tau)       what the liquidity provider keeps
    price impact           e (m_tau - m)       what the order knew
and effective = realised + impact, trade by trade.
"""
from dataclasses import dataclass

import numpy as np

HORIZONS_S = (0.1, 1.0, 10.0, 60.0, 300.0)


@dataclass(frozen=True)
class Flow:
    name: str
    informed: float          # probability that an order predicts the move
    drift_cents: float       # size of the predicted move, reached gradually over ~60 s
    improvement: float       # price improvement given, as a fraction of the quoted half-spread


RETAIL = Flow("retail", 0.05, 3.0, 0.20)
EXCHANGE = Flow("exchange", 0.35, 3.0, 0.0)


def simulate(flow: Flow, n: int, seed: int, half_spread: float = 1.0, noise_per_sqrt_s: float = 0.35):
    rng = np.random.default_rng(seed)
    side = rng.choice([-1, 1], size=n)
    price_vs_mid = side * half_spread * (1.0 - flow.improvement)          # p - m
    informed = rng.random(n) < flow.informed
    moves = {}
    for tau in HORIZONS_S:
        learned = flow.drift_cents * (1.0 - np.exp(-tau / 20.0))
        moves[tau] = side * informed * learned + rng.normal(0.0, noise_per_sqrt_s * np.sqrt(tau), n)
    return side, price_vs_mid, moves


def stats(side, price_vs_mid, move) -> dict[str, float]:
    effective = side * price_vs_mid
    impact = side * move
    realised = effective - impact
    return {"effective": float(effective.mean()), "realised": float(realised.mean()),
            "impact": float(impact.mean())}


def price_improvement_per_share(half_spread: float, flow: Flow) -> float:
    return half_spread * flow.improvement


def max_payment(half_spread: float, flow: Flow, cost: float) -> float:
    """What a wholesaler can pay per share and break even: spread kept less expected impact and costs."""
    expected_impact = flow.informed * flow.drift_cents
    return half_spread * (1.0 - flow.improvement) - expected_impact - cost
