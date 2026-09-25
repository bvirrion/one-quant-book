"""Discretionary macro (One Quant Book 9, chapter 17).

Synthetic: firm.macrobook's 20,000 six-month paths of a rate whose true drift is drawn around a manager's view that it
will fall 50 bp (dispersion 50 bp, normal volatility 90 bp a year); the view expressed as futures without a stop,
futures with a 25 or 50 bp stop, an at-the-money and a 25 bp out-of-the-money receiver option, and a 0/-50 bp option
spread, each per unit of risk budget; how often a correct view loses, and how often a stop cuts it short. NumPy.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "macrobook"))
from firm_macrobook import ViewConfig, bachelier_receiver, expressions, rate_paths, stopped_correct  # noqa: E402


@functools.lru_cache(maxsize=2)
def paths(view_sd: float = 50.0):
    cfg = ViewConfig(view_sd=view_sd)
    return cfg, rate_paths(cfg)


def table(view_sd: float = 50.0):
    """Per expression: mean and sd per unit of risk budget, chance of profit, chance of losing when the view is right,
    and the 5th percentile."""
    cfg, p = paths(view_sd)
    right = p[:, -1] < 0
    out = {}
    for k, v in expressions(p, cfg).items():
        out[k] = {"mean": float(v.mean()), "sd": float(v.std()), "p_profit": float((v > 0).mean()),
                  "lose_when_right": float((v[right] <= 0).mean()), "p05": float(np.percentile(v, 5))}
    return out | {"share_right": float(right.mean())}


def stops(distances=(10, 25, 50, 75, 100)):
    cfg, p = paths()
    return {d: stopped_correct(p, cfg, float(d)) for d in distances}


def premiums():
    cfg = ViewConfig()
    vol, tau = cfg.vol_bp * cfg.vol_premium, cfg.days / 252
    return {"atm": bachelier_receiver(0.0, vol, tau), "otm": bachelier_receiver(-cfg.otm_bp, vol, tau),
            "spread": bachelier_receiver(0.0, vol, tau) - bachelier_receiver(-cfg.spread_bp, vol, tau)}
