"""The bond-futures basis trade (One Quant Book 9, chapter 11).

Synthetic: firm.basistrade's five years of a long-basis book (long cash Treasuries in repo, short futures) earning
20 bp a year on its face, with a 3-cent mean-reverting basis deviation; at year 2.5 a ten-day funding stress moves
the basis 60 cents per 100 against the book, lifts the haircut and futures margin from 1% to 3% each and the repo
rate by 1%, and the basis comes back over two months. Books at several leverages, cut by margin calls and re-levered
at quarterly rolls. Real: leveraged funds' net positions in CBOT Treasury futures (CFTC Traders in Financial
Futures, 2010-2026), as derived statistics. NumPy.
"""
from __future__ import annotations

import csv
import functools
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "basistrade"))
from firm_basistrade import YEAR, BasisConfig, run_book, simulate_basis  # noqa: E402

DATA = ROOT.parent / "data" / "strategies-2"
LEVERAGES = (10, 20, 30, 50)


@functools.lru_cache(maxsize=1)
def books():
    cfg = BasisConfig()
    sim = simulate_basis(cfg)
    return cfg, sim, {L: run_book(sim, cfg, L) for L in LEVERAGES}


def table():
    """By leverage: annual return before the stress, the trough in the stress and the loss left after the recovery
    (both against the capital the day before), the forced-sale days, and five-year annual return."""
    cfg, sim, b = books()
    a, e = sim["stress"]
    out = {}
    for L, r in b.items():
        c = r["capital"]
        pre = c[a - 1]
        out[L] = {"before": float(pre ** (YEAR / (a - 1)) - 1),
                  "trough": float(c[a:e + cfg.recover_days].min() / pre - 1),
                  "after": float(c[e + cfg.recover_days] / pre - 1), "forced": r["forced"],
                  "five_years": float(c[-1] ** (YEAR / cfg.days) - 1), "face_after": float(r["face"][e])}
    return out


def parts(L: int = 50):
    """The stress window's P&L by source, as a share of the capital the day before."""
    cfg, sim, b = books()
    a, e = sim["stress"]
    r, pre = b[L], b[L]["capital"][a - 1]
    w = slice(a - 1, e + cfg.recover_days)
    return {k: float(r[k][w].sum() / pre) for k in ("carry", "marks", "funding", "costs")}


def paths(step: int = 2):
    cfg, sim, b = books()
    idx = np.arange(0, cfg.days + 1, step)
    return {"day": idx, **{L: b[L]["capital"][idx] for L in (10, 20, 50)}}


def real():
    with open(DATA / "tff_summary.csv") as fh:
        return {r["stat"]: r["value"] for r in csv.DictReader(fh)}


def same_terms(L: int = 50):
    """Exercise 7: the stress with collateral terms unchanged (1% and 1%): forced-sale days, trough and after."""
    cfg = BasisConfig(haircut_stress=0.01, margin_stress=0.01)
    sim = simulate_basis(cfg)
    r = run_book(sim, cfg, L)
    a, e = sim["stress"]
    c, pre = r["capital"], r["capital"][a - 1]
    return {"forced": r["forced"], "trough": float(c[a:e + cfg.recover_days].min() / pre - 1),
            "after": float(c[e + cfg.recover_days] / pre - 1), "face_before": float(r["face"][a - 1])}


def forced_before_stress(L: int = 50):
    cfg, sim, b = books()
    a = sim["stress"][0]
    f, face = b[L]["face"], b[L]["face"]
    return {"cuts_before": int((np.diff(f[:a]) < -1e-12).sum()), "face_before": float(face[a - 1]),
            "face_after": float(face[sim["stress"][1]])}
