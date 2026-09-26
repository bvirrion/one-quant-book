"""Automated options market making (One Quant Book 11, chapter 19).

A chain of 170 series (17 strikes from 80 to 120, five expiries from 7 to 90 days, calls and puts) on a stock at 100,
quoted from a skewed surface at half a volatility point either side of theo, ten contracts a series. An informed sweep
after a 1% move in the stock, one series every 5 microseconds, against the exchange's count-based protection; an
ordinary day of multi-leg customer orders against the same protection; a volatility sweep after a 2-point rise in
implied volatility against the market maker's own per-expiry vega limits.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "optquoter"))
import firm_optquoter as oq  # noqa: E402

THRESHOLDS = (2, 3, 5, 10, 13, 15, 20, 40, 10**9)
CHAIN = oq.Chain()
SURF = oq.surface()


@functools.cache
def quotes() -> list[dict]:
    return oq.mass_quote(CHAIN, 100.0, SURF)


def widths() -> dict:
    q = quotes()
    atm = [x for x in q if x["opt"].strike == 100.0]
    call = next(x for x in atm if x["opt"].right == "C" and round(x["opt"].expiry * 365) == 30)
    return {"n": len(q), "atm_30d_call": call,
            "min_width": min(x["ask"] - x["bid"] for x in q), "max_width": max(x["ask"] - x["bid"] for x in q)}


@functools.cache
def protection_table(jump: float = 0.01) -> dict:
    out = {}
    for n in THRESHOLDS:
        s = oq.sweep(quotes(), jump, CHAIN, SURF, oq.Protection(n))
        d = oq.normal_day(len(quotes()), oq.Protection(n))
        out[n] = {"sweep_fills": s["fills"], "sweep_loss": s["loss"], "delta": s["delta_shares"],
                  "day_fills": d["fills"], "day_lost": d["lost"], "day_pulls": d["pulls"], "edge_lost": d["edge_lost"],
                  "edge_kept": d["edge_kept"], "max_loss": s["max_loss"], "targets": s["targets"]}
    return out


def vol_sweep() -> dict:
    out = {}
    for vl in (None, 2000.0, 1000.0, 500.0):
        for react in (50.0, 5.0):
            r = oq.sweep(quotes(), 0.0, CHAIN, SURF, oq.Protection(10**9), dvol=0.02, vega_limit=vl, react_us=react)
            out[(vl, react)] = {"fills": r["fills"], "loss": r["loss"], "vega": r["vega_dollars"],
                                "by_expiry": r["vega_by_expiry"]}
    return out


def refit(noise_vol: float = 0.002, seed: int = 4) -> dict:
    rng = np.random.default_rng(seed)
    ks = np.array(CHAIN.strikes)
    tau = 30 / 365
    true = np.array([SURF.vol(k, tau, 100.0) for k in ks])
    params, rms = oq.refit_slice(ks, 100.0, tau, true + rng.normal(0.0, noise_vol, len(ks)))
    fit = np.sqrt(np.maximum(oq.fsvi.svi(np.log(ks / 100.0), *params), 0.0) / tau)
    return {"rms_to_quotes": rms, "rms_to_true": float(np.sqrt(np.mean((fit - true) ** 2))), "params": params}


def bigger_move(jump: float = 0.02, n: int = 13) -> dict:
    """Exercise 7."""
    a = oq.sweep(quotes(), jump, CHAIN, SURF, oq.Protection(n))
    b = oq.sweep(quotes(), jump, CHAIN, SURF, oq.Protection(10**9))
    return {"protected": a["loss"], "unprotected": b["loss"], "targets": b["targets"]}
