"""Mortgage and structured-credit strategies (One Quant Book 9, chapter 20).

Synthetic: firm.mbsrv's pass-through (borrowers at 6.5%, coupon 6.0%, 29 years left) on Hull-White paths around a
flat 4% curve, priced by a market prepayment model (Book 6's turnover, S-curve and burnout 0.25) at an OAS of 50 bp;
a trader's view that the pool is burning out faster (burnout 1.0); the IO bought on the view and hedged with ten-year
Treasuries, when the market is right, when the view is right, when borrowers are slower, and when borrowers never burn
out; each coupon's OAS under the view; and index tranches in the large-pool Gaussian copula at three correlations,
with protection on the 7-10% tranche sold at the market's correlation of 0.30. NumPy.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "mbsrv"))
from firm_mbsrv import (  # noqa: E402
    MbsConfig,
    PrepayModel,
    _paths,
    coupon_stack,
    expected_tranche_loss,
    io_trade,
    tranche_rv,
)

CFG = MbsConfig()
MARKET = PrepayModel()
TRUTHS = {"market": MARKET, "view": PrepayModel(burnout=1.0), "slow": PrepayModel(refi_top=0.33),
          "no_burnout": PrepayModel(burnout=0.0)}
SHIFTS = tuple(range(-150, 151, 25))
WACS = (0.045, 0.05, 0.055, 0.06, 0.065, 0.07, 0.075, 0.08)
TRANCHES = ((0.0, 0.03), (0.03, 0.07), (0.07, 0.10), (0.10, 0.15), (0.15, 0.30))


@functools.lru_cache(maxsize=1)
def io_scenarios() -> dict:
    """Hedged gain (% of the IO's price) of buying the IO at the market's value, by parallel shift (bp), per truth."""
    out = {n: io_trade(CFG, MARKET, m, 1.0, [s * 1e-4 for s in SHIFTS]) for n, m in TRUTHS.items()}
    return {"price": out["market"]["price"], "hedge": out["market"]["hedge"],
            "gain": {n: [float(g) for g in r["gain"]] for n, r in out.items()}}


def io_summary() -> dict:
    s = io_scenarios()
    i0 = SHIFTS.index(0)
    return {"price": s["price"], "hedge": s["hedge"]} | {n: g[i0] for n, g in s["gain"].items()} | {
        n + "_dn100": g[SHIFTS.index(-100)] for n, g in s["gain"].items()}


@functools.lru_cache(maxsize=1)
def stack() -> list[dict]:
    """Each coupon's price under the market model and its OAS under the view and under no burnout (bp)."""
    view, nob = coupon_stack(CFG, MARKET, TRUTHS["view"], WACS), coupon_stack(CFG, MARKET, TRUTHS["no_burnout"], WACS)
    return [{"coupon": round(100 * (v["wac"] - 0.005), 1), "price": v["price"], "duration": v["duration"],
             "oas_view": 1e4 * v["oas_view"], "oas_nob": 1e4 * n["oas_view"]} for v, n in zip(view, nob, strict=True)]


def tranches(p: float = 0.06) -> list[dict]:
    """Expected loss (% of the tranche, five years) at correlations 0.15, 0.30 and 0.45."""
    return [{"tranche": (a, d)} | {rho: 100 * expected_tranche_loss(a, d, p, rho) for rho in (0.15, 0.30, 0.45)}
            for a, d in TRANCHES]


def mezz() -> dict:
    """Selling protection on the 7-10% tranche at the market's expected loss (correlation 0.30), by true correlation."""
    return {rho: tranche_rv(0.06, 0.30, rho, 0.07, 0.10) for rho in (0.15, 0.30, 0.45)}


def new_mortgage_rate() -> float:
    """The mortgage rate at the start: the ten-year par rate plus the model's mortgage spread."""
    _, p10 = _paths(CFG)
    return float(p10[:, 0].mean() + MARKET.mortgage_spread)


def vol_case(sigma: float = 0.012) -> dict:
    """The IO trade at unchanged rates with another rate volatility, for the market and every truth."""
    cfg = MbsConfig(sigma=sigma)
    out = {n: io_trade(cfg, MARKET, TRUTHS[n]) for n in ("view", "no_burnout")}
    return {"price": out["view"]["price"]} | {n: float(r["gain"][0]) for n, r in out.items()}
