"""Options: cross-venue and volatility arbitrage at speed (One Quant Book 11, chapter 20).

Parity scans across one, three and six venues quoting the same chain (nine strikes, three months, fair values from
firm.parity), a cent a leg in fees, and how many opportunities survive one refresh of the quotes; a box and a jelly
roll; the dividend play's profit against the share of holders who fail to exercise (firm.optmm.best_play).
"""
from __future__ import annotations

import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "optarb"))
import firm_optarb as oa  # noqa: E402

FAILS = (0.01, 0.015, 0.02, 0.03, 0.05, 0.1, 0.2, 0.3, 0.5)


@functools.cache
def scans() -> dict:
    return {(nv, rho): oa.scan(oa.Listings(n_venues=nv, seed=2), lag_rho=rho, rounds=1000)
            for nv in (1, 3, 6) for rho in (0.0, 0.5, 0.9)}


def dividend() -> dict:
    return oa.dividend_curve(FAILS)


def examples() -> dict:
    a = oa.Listings()
    b = oa.Listings(years=0.5)
    return {"box_rate": oa.box_rate(95, 105, 9.90, 0.25), "box_edge": oa.box_edge(9.89, 9.87, 95, 105, 0.25, 0.04),
            "jelly": oa.jelly_roll(a.fair[(100, "C")], a.fair[(100, "P")], b.fair[(100, "C")], b.fair[(100, "P")],
                                   100, 0.25, 0.5, 0.04),
            "threshold": oa.exercise_threshold(), "forward": a.forward}
