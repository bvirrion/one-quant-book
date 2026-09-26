"""FX market making (One Quant Book 11, chapter 21).

A consolidated fair price from three venues; three client tiers streamed at 0.3, 0.5 and 1.0 basis point half-spreads
with informed shares of 30%, 10% and none (an informed request follows a 0.6 bp move the stream has not shown);
last look with a 5 ms hold, none, asymmetric or symmetric at 0.1 bp; then a day of 20,000 client trades of $1 million,
internalised or hedged on the primary venue at 0.25 bp, with a skew that brings offsetting flow.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "fxlp"))
import firm_fxlp as fx  # noqa: E402

TIERS = {"tier 1": (0.3, 0.5, 0.30, 0.6), "tier 2": (0.5, 0.3, 0.10, 0.6), "tier 3": (1.0, 0.2, 0.0, 0.6)}
SKEWS = (0.0, 0.0002, 0.0003, 0.0004, 0.00045, 0.0005, 0.001, 0.002, 0.005)


def venues() -> dict:
    return fx.venue_errors()


@functools.cache
def last_look() -> dict:
    return {p: fx.stream(TIERS, policy=p) for p in ("none", "asymmetric", "symmetric")}


@functools.cache
def hedging() -> dict:
    out = {}
    for s in SKEWS:
        best, res = fx.best_hedge_share(skew=s)
        out[s] = {"best": best, "objective": res[best]["objective"], "internalise_all": res[0.0]["objective"],
                  "hedge_all": res[1.0]["objective"], "half_life": math.log(2) / (2 * s) if s else math.inf,
                  "mean_abs_inv": res[0.0]["mean_abs_inventory"]}
    return out


def cross() -> tuple[float, float]:
    return fx.synthetic_cross(1.0850, 1.0851, 150.20, 150.21)
