"""Pricing a risk bid for a block of stock (Chapter 2).

The dealer buys Q shares now at a discount and sells them at a constant rate,
a fraction `participation` of the daily volume V, so the unwind lasts
T = Q / (participation * V) days. Two costs:

  impact  = kappa * sigma * sqrt(Q / V)          (square-root law, average cost)
  risk    = z * sigma * sqrt(T / 3)              (z-quantile of the unwind P&L)

Both are fractions of the block's value; sigma is the daily volatility.
"""
import math
from dataclasses import dataclass

import numpy as np

Z95 = 1.6449


@dataclass(frozen=True)
class Block:
    shares: float
    adv: float                 # average daily volume, shares
    sigma: float               # daily volatility, fraction
    participation: float = 0.10
    kappa: float = 0.70        # impact coefficient (model parameter)


def unwind_days(b: Block) -> float:
    return b.shares / (b.participation * b.adv)


def impact_cost(b: Block) -> float:
    return b.kappa * b.sigma * math.sqrt(b.shares / b.adv)


def risk_std(b: Block) -> float:
    """Std of the unwind P&L as a fraction of value: sigma * sqrt(T / 3)."""
    return b.sigma * math.sqrt(unwind_days(b) / 3.0)


def breakeven_discount(b: Block, z: float = Z95) -> float:
    """Discount at which the dealer loses money with probability 1 - Phi(z)."""
    return impact_cost(b) + z * risk_std(b)


def simulate_unwind(b: Block, discount: float, n_paths: int, seed: int, steps: int = 200):
    """P&L per unit of block value over n_paths, selling linearly over T days."""
    rng = np.random.default_rng(seed)
    dt = unwind_days(b) / steps
    dw = rng.normal(0.0, b.sigma * math.sqrt(dt), size=(n_paths, steps))
    price = np.cumsum(dw, axis=1)                 # return of the stock since purchase
    avg_sale = price.mean(axis=1)                 # equal slices: average sale return
    return discount - impact_cost(b) + avg_sale
