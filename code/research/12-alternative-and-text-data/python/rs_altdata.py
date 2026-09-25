"""Alternative and text data (One Quant Book 7, chapter 12).

A vendor trial on a synthetic card-spending panel. The market is firm.synthmkt (seed 1); 400 names listed for all ten
years are the retailers; each quarter's true earnings surprise s is announced a random number of days after the
quarter. The vendor's panel measures each retailer's quarter with a spending-growth figure delivered ten trading days
after the quarter ends. Its five-year history (years 6 to 10 of the market) has a planted story: the vendor launched
live at the start of its third year, when it changed card provider; the first two years were reconstructed at launch
from the new provider's panel, reweighted to match the retailers' reported results (so they fit the outcome), and
cover all 400 names; the live years cover fewer names, with a level shift and more noise. The firm already owns a
signal that carries part of the same information. The harness (firm.vendoreval) measures what the trial can see.

Text: a synthetic corpus of 2,000 documents with a planted tone, scored with a general-purpose negative word list
(which counts words such as liability, tax and cost, frequent in financial text and unrelated to its tone) and with a
finance-specific list. NumPy only.
"""
from __future__ import annotations

import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[3] / "firm"
for c in ("vendoreval", "synthmkt"):
    sys.path.insert(0, str(ROOT / c))
from firm_synthmkt import simulate  # noqa: E402
from firm_vendoreval import (  # noqa: E402
    backfill_share,
    breakeven,
    coverage,
    cusum_break,
    fit_by_group,
    ic_by_group,
    incremental_ic,
    long_short,
    rank_ic,
    residualise,
    tone,
)

Q, YEAR, LAG = 63, 252, 10                    # quarter, year (days); delivery lag after the quarter's end
START, LIVE = 5 * YEAR, 7 * YEAR              # history starts in year 6; live (new provider) from year 8
CAPITAL, COST, HALF_LIFE, YEARS = 20e6, 0.004, 2.0, 3


@functools.lru_cache(maxsize=1)
def trial():
    """One row per (retailer, quarter) in the vendor's history with an announcement after the delivery: the panel
    value, the true surprise, the firm's existing signal, the return from delivery to announcement (market-adjusted),
    the quarter, the history year (1-5), the delivery day, and whether the row was backfilled."""
    P = simulate()
    full = np.flatnonzero(P.listed.all(axis=0))[:400]
    rng = np.random.default_rng(12)
    live_names = set(rng.choice(full, 320, replace=False).tolist())
    adj = P.ret - P.beta[None, :] * P.mkt[:, None]
    rows = []
    for t, p, s in P.earnings:
        f = t - t % Q
        if p not in set(full.tolist()) or f < START or t - f <= LAG:
            continue
        live = f >= LIVE
        if live and p not in live_names:
            continue
        if live:
            m = 0.12 + 0.35 * s + rng.normal(0.0, 1.0)             # new provider: shifted, noisier
        else:
            m = 0.90 * s + rng.normal(0.0, 0.55)                   # reconstructed to fit the reported results
        k = f + LAG
        rows.append((m, s, 0.45 * s + rng.normal(0.0, 1.0), np.sum(adj[k + 1:t + 1, p]), f, (f - START) // YEAR + 1,
                     k, t, 0 if live else 1))
    a = np.array(rows)
    return {"m": a[:, 0], "s": a[:, 1], "old": a[:, 2], "y": a[:, 3], "quarter": a[:, 4].astype(int),
            "year": a[:, 5].astype(int), "delivered": np.where(a[:, 8] == 1, LIVE, a[:, 6]).astype(int),
            "announce": a[:, 7].astype(int), "backfilled": a[:, 8].astype(bool)}


def trial_report():
    d = trial()
    cov = coverage(d["quarter"])
    fit = fit_by_group(d["s"], d["m"], d["year"])
    order = np.argsort(d["quarter"], kind="stable")
    resid = (d["m"] - np.polyfit(d["s"], d["m"], 1)[0] * d["s"])[order]
    k, stat = cusum_break(resid)
    live = ~d["backfilled"]
    inc = incremental_ic(d["m"][live], d["old"][live], d["y"][live], d["quarter"][live])
    ls_new = long_short(d["m"][live], d["y"][live], d["quarter"][live])
    ls_back = long_short(d["m"][~live], d["y"][~live], d["quarter"][~live])
    ls_inc = long_short(residualise(d["m"][live], d["old"][live], d["quarter"][live]), d["y"][live], d["quarter"][live])
    return {"rows": len(d["m"]), "coverage_backfill": np.mean([v for q, v in cov.items() if q < LIVE]),
            "coverage_live": np.mean([v for q, v in cov.items() if q >= LIVE]),
            "backfill_share": backfill_share(d["quarter"], d["delivered"], Q),
            "fit": fit, "break_quarter_year": float((d["quarter"][order][k] - START) / YEAR + 1), "break_stat": stat,
            "ic_year": ic_by_group(d["m"], d["y"], d["year"]),
            "ic_backfill": rank_ic(d["m"][~live], d["y"][~live]), "ic_live": rank_ic(d["m"][live], d["y"][live]),
            "ic_old_live": rank_ic(d["old"][live], d["y"][live]), "inc": inc,
            "ls_new": ls_new, "ls_inc": ls_inc, "ls_back": ls_back}


def live_fit():
    d = trial()
    live = ~d["backfilled"]
    b, a = np.polyfit(d["s"][live], d["m"][live], 1)
    return float(b), float(a)


def ic_break():
    """Exercise 7: the IC of each quarter, and the CUSUM break of that series (quarter index, year, statistic)."""
    d = trial()
    ics = ic_by_group(d["m"], d["y"], d["quarter"])
    q = np.array(sorted(ics))
    x = np.array([ics[k] for k in q])
    k, stat = cusum_break(x)
    return x, int(k), float((q[k] - START) / YEAR + 1), float(stat)


def breakeven_curve(half_lives=(0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0)):
    """Break-even annual fee against the edge's half-life, for the spread of the backfilled years (the vendor's
    pitch), of the live years, and of the live years net of the signal already owned."""
    r = trial_report()
    return {h: {k: breakeven(4 * r[k], CAPITAL, COST, h, YEARS) for k in ("ls_back", "ls_new", "ls_inc")}
            for h in half_lives}


def value(ls_quarter: float):
    """Break-even annual fee: a quarterly long-short return earned four times a year on CAPITAL, less COST a year,
    decaying with HALF_LIFE years, over a YEARS-year contract."""
    return breakeven(4 * ls_quarter, CAPITAL, COST, HALF_LIFE, YEARS)


# ------------------------------------------------------------------------------------------------ text
POS = ["growth", "strong", "improved", "record", "gain", "exceeded", "robust", "success"]
NEG = ["loss", "decline", "weak", "impairment", "adverse", "shortfall", "litigation", "downturn"]
FIN = ["liability", "tax", "cost", "capital", "vice", "board", "foreign", "excess"]      # negative in general usage
NEUTRAL = [f"w{i:02d}" for i in range(60)]
VOCAB = POS + NEG + FIN + NEUTRAL


@functools.lru_cache(maxsize=1)
def corpus(n: int = 2000, length: int = 400, seed: int = 5):
    """Documents of `length` words: tone tau ~ N(0, 1) raises positive and lowers negative word rates; the finance
    words are frequent and unrelated to tone."""
    rng = np.random.default_rng(seed)
    tau = rng.standard_normal(n)
    base = np.r_[np.full(8, 0.004), np.full(8, 0.004), np.full(8, 0.016), np.full(60, 1.0)]
    base[24:] *= (1.0 - base[:24].sum()) / base[24:].sum()
    counts = np.empty((n, len(VOCAB)), int)
    for i, t in enumerate(tau):
        p = base.copy()
        p[:8] *= np.exp(0.6 * t)
        p[8:16] *= np.exp(-0.6 * t)
        counts[i] = rng.multinomial(length, p / p.sum())
    return tau, counts


def text_scores():
    tau, counts = corpus()
    general = tone(counts, VOCAB, set(NEG + FIN))
    finance = tone(counts, VOCAB, set(NEG))
    net = finance - tone(counts, VOCAB, set(POS))
    fin_share = counts[:, 16:24].sum() / counts[:, 8:24].sum()
    return {"general": float(np.corrcoef(general, -tau)[0, 1]), "finance": float(np.corrcoef(finance, -tau)[0, 1]),
            "net": float(np.corrcoef(net, -tau)[0, 1]), "fin_share": float(fin_share)}
