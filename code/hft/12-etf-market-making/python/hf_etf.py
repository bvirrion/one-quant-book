"""ETF market making (One Quant Book 11, chapter 12).

A synthetic bond ETF of 100 bonds that print a trade every two hours on average (every twenty in a five-day freeze,
days 40-44 of 60, when the factor falls 5% with four times the volatility and bond spreads rise sixfold). A market
maker quotes it from the stale NAV or from a pricing basket moved by a liquid proxy, hedges or not in the proxy,
holds or redeems in kind at the close. Three simulated markets.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "etfmm"))
import firm_etfmm as fe  # noqa: E402

SEEDS = (3, 4, 5)
CONFIGS = {"NAV, unhedged": ("nav", "none", "hold"), "NAV, hedged": ("nav", "future", "hold"),
           "basket, unhedged": ("basket", "none", "hold"), "basket, hedged": ("basket", "future", "hold"),
           "basket, hedged, redeem": ("basket", "future", "redeem")}


@functools.cache
def market(seed: int) -> fe.Market:
    return fe.Market(seed=seed)


@functools.cache
def run(name: str, seed: int) -> dict:
    return fe.run_mm(market(seed), *CONFIGS[name])


def _freeze(mk):
    return np.isin(np.arange(mk.days), range(*mk.freeze))


def errors() -> dict:
    """Mean absolute error of the NAV and of the pricing basket against the true value (basis points), and the mean
    age of the bonds' last prints (minutes), in normal minutes and in the freeze; three markets pooled."""
    out = {}
    for part in ("normal", "freeze"):
        nav, bas, age = [], [], []
        for s in SEEDS:
            mk = market(s)
            sel = mk.stress if part == "freeze" else ~mk.stress
            nav.append(np.abs(mk.nav - mk.true)[sel] / mk.true[sel])
            bas.append(np.abs(mk.basket - mk.true)[sel] / mk.true[sel])
            age.append(mk.age[sel])
        out[part] = {"nav_bp": 1e4 * float(np.mean(np.concatenate(nav))),
                     "basket_bp": 1e4 * float(np.mean(np.concatenate(bas))),
                     "age_min": float(np.mean(np.concatenate(age)))}
    return out


def table() -> dict:
    """Per configuration: mean and standard deviation of the P&L of a normal day (the forty days before the freeze),
    the freeze's total, and its parts."""
    out = {}
    for name in CONFIGS:
        normal, sd, frz, parts = [], [], [], {k: [] for k in ("spread", "arb", "hedge", "flatten")}
        for s in SEEDS:
            r, f = run(name, s), _freeze(market(s))
            pre = np.arange(market(s).days) < market(s).freeze[0]
            normal.append(r["total"][pre].mean())
            sd.append(r["total"][pre].std())
            frz.append(r["total"][f].sum())
            for k in parts:
                parts[k].append(r[k][f].sum())
        out[name] = {"normal": float(np.mean(normal)), "sd": float(np.mean(sd)), "freeze": float(np.mean(frz)),
                     **{"freeze_" + k: float(np.mean(v)) for k, v in parts.items()}}
    return out


def decomposition(seed: int = SEEDS[0], name: str = "basket, hedged") -> dict:
    """At each close: the premium the market maker quotes over the NAV, the NAV's staleness (NAV over true) and the
    quote's own gap to the true value (pressure), in basis points; and the worst day."""
    mk, r = market(seed), run(name, seed)
    ends = np.arange(fe.MINUTES - 1, mk.m, fe.MINUTES)
    prem = 1e4 * (r["mid"][ends] - mk.nav[ends]) / mk.nav[ends]
    stale = 1e4 * (mk.nav[ends] - mk.true[ends]) / mk.true[ends]
    press = 1e4 * (r["mid"][ends] - mk.true[ends]) / mk.true[ends]
    d = int(np.argmin(prem))
    return {"day": d, "premium": float(prem[d]), "stale": float(stale[d]), "pressure": float(press[d]),
            "prem": prem, "stale_path": stale, "press": press,
            "freeze_pressure": float(press[_freeze(mk)].mean()), "normal_premium_sd": float(prem[~_freeze(mk)].std())}


def unit_fee_bp(fee: float = 1250.0, shares: int = 50000, price: float = 291.58) -> float:
    """A fixed creation fee in basis points of a creation unit's value."""
    return 1e4 * fee / (shares * price)


def sparser(freeze_print: float, seed: int = SEEDS[0]) -> dict:
    """The first market with bonds printing `freeze_print` times less often in the freeze (exercise 7)."""
    mk = fe.Market(seed=seed, freeze_print=freeze_print)
    ends = np.arange(fe.MINUTES - 1, mk.m, fe.MINUTES)
    f = _freeze(mk)
    return {"max_stale": float(np.max(1e4 * (mk.nav[ends] - mk.true[ends]) / mk.true[ends])),
            "basket_bp": 1e4 * float(np.mean(np.abs(mk.basket - mk.true)[mk.stress] / mk.true[mk.stress])),
            "basket": float(fe.run_mm(mk, "basket", "future", "hold")["total"][f].sum()),
            "nav": float(fe.run_mm(mk, "nav", "future", "hold")["total"][f].sum())}
