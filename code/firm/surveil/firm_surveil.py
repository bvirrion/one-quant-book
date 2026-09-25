"""firm.surveil -- detectors for spoofing, marking the close and wash trades, and their errors (Book 9, ch. 29).

The data are account-days: each row summarises one account's orders and trades on one day. Legitimate types are chosen
to trip the detectors: market makers who cancel almost everything; market makers who refresh all their quotes after
every fill; deep-book liquidity providers whose large orders, far from the touch, rarely fill; directional traders;
index funds that trade heavily at the close; firms whose independent algorithms occasionally cross each other.
Labelled episodes follow the patterns described in public enforcement records: large orders that almost never fill
and are cancelled right after small orders on the other side fill (the testimony in United States v. Coscia); heavy
trading against a position priced at the settlement, in the closing minutes, with a move that reverses (the CFTC's
Optiver case); trades with no change in beneficial ownership. Detectors are scores; each is evaluated by its
true-positive rate at a fixed false-positive rate. No manipulation's profitability is modelled. NumPy only.

API (stable):
    SurveilConfig(...)                           parameters (seed 199)
    spoofing_days(cfg), close_days(cfg), wash_days(cfg)   dict of feature arrays and labels (1 = planted episode)
    spoof_scores(d), close_scores(d), wash_scores(d)      detector scores by name
    tpr_at_fpr(score, label, fpr)                true-positive rate at the threshold giving that false-positive rate
    flagged_by_type(score, d, fpr)               share of each account type flagged at that threshold
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SurveilConfig:
    seed: int = 199
    counts: tuple = (5000, 3000, 1500, 2000, 100)   # market makers, refreshers, deep providers, directional, spoofers
    close_counts: tuple = (4000, 1500, 100)         # ordinary accounts, index funds at the close, close markers
    wash_counts: tuple = (4000, 1000, 100)          # ordinary accounts, multi-algorithm firms, wash traders


TYPES = ("market maker", "quote refresher", "deep provider", "directional", "spoofer")


def spoofing_days(cfg: SurveilConfig | None = None) -> dict:
    """Per account-day: small and large orders placed and filled, large-order cancellations, and those cancelled within
    a second after a fill on the account's other side."""
    cfg = cfg or SurveilConfig()
    rng = np.random.default_rng(cfg.seed)
    kind = np.repeat(np.arange(5), cfg.counts)
    n = len(kind)
    u = rng.random(n)
    # orders a day: small (at the touch) and large (bigger size, possibly away from it)
    n_small = np.select([kind == 0, kind == 1, kind == 2, kind == 3, kind == 4],
                        [rng.poisson(600, n), rng.poisson(600, n), rng.poisson(300, n), rng.poisson(150, n),
                         rng.poisson(100, n)])
    n_large = np.select([kind == 0, kind == 1, kind == 2, kind == 3, kind == 4],
                        [rng.poisson(150, n), rng.poisson(150, n), rng.poisson(300, n), rng.poisson(10, n),
                         rng.poisson(300, n)])
    p_small = np.select([kind == 0, kind == 1, kind == 2, kind == 3, kind == 4],
                        [0.05, 0.05, 0.15, 0.40, 0.30 + 0.30 * u])
    v = rng.random(n)
    p_large = np.select([kind == 0, kind == 1, kind == 2, kind == 3, kind == 4],
                        [0.04, 0.05, 0.004 + 0.02 * u, 0.40, 0.002 + 0.04 * u])
    link = np.select([kind == 0, kind == 1, kind == 2, kind == 3, kind == 4],                # share of large cancels
                     [0.03, 0.25 + 0.30 * v, 0.03 + 0.40 * v, 0.02, 0.15 + 0.75 * v])   # right after a fill
    f_small, f_large = rng.binomial(n_small, p_small), rng.binomial(n_large, p_large)
    c_large = n_large - f_large
    linked = rng.binomial(c_large, link)
    return {"kind": kind, "label": (kind == 4).astype(int), "n_small": n_small, "n_large": n_large,
            "f_small": f_small, "f_large": f_large, "c_large": c_large, "linked": linked}


def spoof_scores(d: dict) -> dict:
    """Order-to-trade ratio; the gap between small and large orders' fill rates (log ratio); the share of large
    cancellations that follow a fill on the other side; and the product of the last two (both must be high)."""
    orders = d["n_small"] + d["n_large"]
    fills = d["f_small"] + d["f_large"]
    otr = orders / np.maximum(fills, 1)
    gap = np.log((d["f_small"] + 1) / (d["n_small"] + 2)) - np.log((d["f_large"] + 1) / (d["n_large"] + 2))
    linked = d["linked"] / np.maximum(d["c_large"], 1)
    return {"order-to-trade": otr, "fill-rate gap": gap, "cancel after fill": linked,
            "gap x cancel": np.maximum(gap, 0) * linked}


def close_days(cfg: SurveilConfig | None = None) -> dict:
    """Per account-day: share of the day's volume traded in the closing minutes, whether it opposes a position priced at
    the settlement, and the next day's reversal of the closing move (bp, positive = reversed)."""
    cfg = cfg or SurveilConfig()
    rng = np.random.default_rng(cfg.seed + 1)
    kind = np.repeat(np.arange(3), cfg.close_counts)
    n = len(kind)
    share = np.select([kind == 0, kind == 1, kind == 2], [rng.beta(1.5, 12, n), rng.beta(6, 4, n), rng.beta(5, 5, n)])
    opposes = np.select([kind == 0, kind == 1, kind == 2], [rng.random(n) < 0.05, rng.random(n) < 0.05,
                                                          rng.random(n) < 0.85])
    reversal = np.select([kind == 0, kind == 1, kind == 2], [rng.normal(0, 10, n), rng.normal(2, 10, n),
                                                           rng.normal(12, 10, n)])
    return {"kind": kind, "label": (kind == 2).astype(int), "share": share, "opposes": opposes, "reversal": reversal}


def close_scores(d: dict) -> dict:
    return {"close share": d["share"], "share x reversal": d["share"] * np.maximum(d["reversal"], 0),
            "opposes settlement position": d["share"] * np.maximum(d["reversal"], 0) * (0.2 + d["opposes"])}


def wash_days(cfg: SurveilConfig | None = None) -> dict:
    """Per account-day: trades, and trades matched against the same beneficial owner (self-matches)."""
    cfg = cfg or SurveilConfig()
    rng = np.random.default_rng(cfg.seed + 2)
    kind = np.repeat(np.arange(3), cfg.wash_counts)
    n = len(kind)
    trades = rng.poisson(np.select([kind == 0, kind == 1, kind == 2], [200, 2000, 500]))
    rate = np.select([kind == 0, kind == 1, kind == 2],
                     [0.0005, 0.01 + 0.01 * rng.random(n), 0.02 + 0.3 * rng.random(n)])
    return {"kind": kind, "label": (kind == 2).astype(int), "trades": trades, "self": rng.binomial(trades, rate)}


def wash_scores(d: dict) -> dict:
    return {"self-match count": d["self"].astype(float), "self-match share": d["self"] / np.maximum(d["trades"], 1)}


def tpr_at_fpr(score, label, fpr: float = 0.01) -> dict:
    score, label = np.asarray(score, float), np.asarray(label)
    thr = np.quantile(score[label == 0], 1 - fpr)
    return {"threshold": float(thr), "tpr": float((score[label == 1] > thr).mean()),
            "fpr": float((score[label == 0] > thr).mean())}


def flagged_by_type(score, d: dict, fpr: float = 0.01) -> np.ndarray:
    thr = tpr_at_fpr(score, d["label"], fpr)["threshold"]
    return np.array([(np.asarray(score)[d["kind"] == k] > thr).mean() for k in range(d["kind"].max() + 1)])
