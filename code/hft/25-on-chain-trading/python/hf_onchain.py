"""On-chain trading (One Quant Book 11, chapter 25).

A constant-product pool worth $20 million in a token at $3,000 (4% daily volatility), 12-second blocks for a week,
$2,000 of noise swaps a block, arbitrage against the centralised price whenever it beats $5 of gas; searchers bidding
for each opportunity in a first-price auction to the builder; the liquidity provider hedged on the centralised
exchange; a lending liquidation; and one sandwich, for the legal discussion.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
for dep in ("searcher", "sandwich"):
    sys.path.insert(0, str(ROOT / "firm" / dep))
import firm_sandwich as sw  # noqa: E402
import firm_searcher as fs  # noqa: E402

SEEDS = (1, 2, 3)
FEES = (0.0005, 0.001, 0.003, 0.01)
NS = (1, 2, 3, 5, 10, 20)


@functools.cache
def chain(seed: int = 1) -> fs.Chain:
    return fs.Chain(seed=seed, blocks=7200 * 7)


@functools.cache
def pool_week() -> dict:
    return {s: fs.run_pool(chain(s)) for s in SEEDS}


@functools.cache
def by_fee() -> dict:
    return {f: fs.run_pool(chain(1), fee=f) for f in FEES}


def auctions(spread: float = 0.2) -> dict:
    return {n: fs.auction(100.0, n, spread) for n in NS}


def lvr_theory() -> float:
    return fs.lvr_rate(0.04, 20e6) * 7


def sandwich_example():
    """A $100,000 buy of the token in a $20 million pool (reserves in integer cents and thousandths of a token), a 1%
    slippage tolerance, $10 of gas, 90% of the gross paid to the builder. Amounts returned in cents and milli-tokens."""
    ra, rb = 1_000_000_000, 3_333_333
    return sw.sandwich(ra, rb, 10_000_000, 100, 1_000, 9000)


def double_vol() -> dict:
    """Exercise 7: the same week at 8% daily volatility."""
    r = fs.run_pool(fs.Chain(seed=1, blocks=7200 * 7, sigma_day=0.08))
    return {**r, "theory": fs.lvr_rate(0.08, 20e6) * 7}


def gross_opportunity() -> float:
    r = pool_week()[1]
    return r["arb_profit"] + 5.0 * r["arbs"]
