"""Depositary receipts and dual listings (One Quant Book 11, chapter 14).

A home listing open for the first two hours of the receipt's session, a receipt of two shares at 1.25 dollars per
unit of home currency, a proxy for the home market that trades all session. The receipt's fair value from the home
mid when both are open, from the home close with or without the proxy's move when the home market is shut; the
quoting error by minute of the session; the overlap's price gaps; the conversion threshold.
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "drarb"))
import firm_drarb as fd  # noqa: E402

SEEDS = (1, 2, 3)


@functools.cache
def pair(seed: int, si: float = 0.012) -> fd.Pair:
    return fd.Pair(seed=seed, si=si)


def _rms(x) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def errors(si: float = 0.012) -> dict:
    """RMS quoting error (bp) in open and closed minutes and at the session's last minute, three pairs pooled."""
    out = {}
    for m in ("home", "proxy"):
        o, c, e = [], [], []
        for s in SEEDS:
            p = pair(s, si)
            err = p.error_bp(m)
            o.append(err[p.open])
            c.append(err[~p.open])
            e.append(err[np.arange(p.m) % fd.SESSION == fd.SESSION - 1])
        out[m] = {"open": _rms(np.concatenate(o)), "closed": _rms(np.concatenate(c)), "end": _rms(np.concatenate(e))}
    return out


def by_minute(step: int = 15) -> dict:
    """RMS error by minute of the session, in buckets of `step` minutes (figure)."""
    rows = {}
    for m in ("home", "proxy"):
        errs = np.concatenate([pair(s).error_bp(m).reshape(-1, fd.SESSION) for s in SEEDS])
        rows[m] = [_rms(errs[:, i:i + step]) for i in range(0, fd.SESSION, step)]
    return rows


def overlap_gaps(cost_bp: float = 10.0) -> dict:
    """The receipt's own mid against the home mid converted, while both are open: standard deviation and the share of
    minutes when the gap exceeds the round-trip cost of trading both legs and the currency."""
    g = np.concatenate([(1e4 * (pair(s).dr_mid - pair(s).quote("home")) / pair(s).true)[pair(s).open] for s in SEEDS])
    return {"sd": float(g.std()), "over": float(np.mean(np.abs(g) > cost_bp))}


def threshold(dr_price: float = 25.0) -> float:
    return fd.threshold_bp(dr_price, 0.05, 6.0, 2, 0.05)
