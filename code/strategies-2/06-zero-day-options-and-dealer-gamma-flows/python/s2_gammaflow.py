"""Zero-day options and dealer-gamma flows (One Quant Book 9, chapter 6).

Synthetic: firm.gammaflow's 2,000 days of an index opening at 100 with zero-day calls and puts, customer sides drawn
each day (on average short calls and long puts, so dealers long calls and short puts), dealers hedging a tenth of
their unhedged delta each five minutes and the rest over the last 30 minutes, with price impact. Dealer gamma at the
open is estimated from open interest under the usual convention (dealers long every call, short every put) and under
the average sides. The trade: over the last 30 minutes, follow the day's move when dealers are estimated short gamma
and fade it when long. NumPy.
"""
from __future__ import annotations

import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "gammaflow"))
from firm_gammaflow import YEAR_HOURS, FlowConfig, dealer_gamma, flip_level, simulate_days, strikes  # noqa: E402

LAST = 72                      # the bar at which the last 30 minutes begin


@functools.lru_cache(maxsize=2)
def days():
    cfg = FlowConfig()
    d = simulate_days(cfg)
    oi_c = -d["pos_c"] / np.where(d["call_side"] == 0, 1.0, d["call_side"])[:, None]
    oi_p = -d["pos_p"] / np.where(d["put_side"] == 0, 1.0, d["put_side"])[:, None]
    tau0 = 6.5 / YEAR_HOURS
    d["avg_gamma"] = dealer_gamma(np.full(cfg.days, 100.0), tau0, -cfg.call_side * oi_c, -cfg.put_side * oi_p, cfg)
    return cfg, d


def estimates():
    """How well each estimate of dealer gamma at the open tracks the truth: sign agreement and correlation."""
    _, d = days()
    t = d["true_gamma"]
    return {name: {"agree": float((np.sign(e) == np.sign(t)).mean()), "corr": float(np.corrcoef(e, t)[0, 1])}
            for name, e in (("convention", d["est_gamma"]), ("average sides", d["avg_gamma"]))} | {
        "short_share": float((t < 0).mean()), "est_short_share": float((d["est_gamma"] < 0).mean())}


def trade():
    """Last-30-minute return times the sign of the day's move so far, in basis points, per day."""
    _, d = days()
    S = d["S"]
    return 1e4 * np.sign(S[:, LAST] / S[:, 0] - 1) * (S[:, -1] / S[:, LAST] - 1)


def regimes(cost: float = 1.0):
    """The momentum trade by regime (true and estimated), and the rule 'follow if short, fade if long', gross and net
    of a round-trip cost in basis points."""
    _, d = days()
    x = trade()
    out = {}
    for name, g in (("true", d["true_gamma"]), ("convention", d["est_gamma"]), ("average sides", d["avg_gamma"])):
        short, rule = g < 0, np.where(g < 0, x, -x)
        out[name] = {"short_mean": float(x[short].mean()), "short_t": float(x[short].mean() / x[short].std(ddof=1)
                                                                            * math.sqrt(short.sum())),
                     "long_mean": float(x[~short].mean()), "long_t": float(x[~short].mean() / x[~short].std(ddof=1)
                                                                           * math.sqrt((~short).sum())),
                     "rule_mean": float(rule.mean()), "rule_sr": float(rule.mean() / rule.std(ddof=1) * math.sqrt(252)),
                     "net_sr": float((rule.mean() - cost) / rule.std(ddof=1) * math.sqrt(252))}
    out["unconditional"] = {"mean": float(x.mean()), "sr": float(x.mean() / x.std(ddof=1) * math.sqrt(252))}
    return out


def day_vol():
    """Standard deviation of the day's log return (%) on true short- and long-gamma days and without feedback."""
    _, d = days()
    S, t = d["S"], d["true_gamma"]
    lr = np.log(S[:, -1] / 100)
    return {"short": float(lr[t < 0].std() * 100), "long": float(lr[t > 0].std() * 100),
            "free": float(np.log(d["S_free"][:, -1] / 100).std() * 100)}


def pinning(within: float = 0.05):
    """Share of closes within `within` of a round strike (a multiple of 0.5), by true regime and without feedback."""
    _, d = days()
    near = lambda s: np.abs(s - np.round(s * 2) / 2) <= within          # noqa: E731
    t = d["true_gamma"]
    return {"long": float(near(d["S"][t > 0, -1]).mean()), "short": float(near(d["S"][t < 0, -1]).mean()),
            "free": float(near(d["S_free"][:, -1]).mean())}


def flips(n: int = 200):
    """For the first n days: share with a flip level in 97-103 at the open, and its median, true and conventional."""
    cfg, d = days()
    oi_c = -d["pos_c"] / np.where(d["call_side"] == 0, 1.0, d["call_side"])[:, None]
    oi_p = -d["pos_p"] / np.where(d["put_side"] == 0, 1.0, d["put_side"])[:, None]
    tau0 = 6.5 / YEAR_HOURS
    true = np.array([flip_level(d["pos_c"][i], d["pos_p"][i], cfg, tau0) for i in range(n)])
    conv = np.array([flip_level(-cfg.conv_call * oi_c[i], -cfg.conv_put * oi_p[i], cfg, tau0) for i in range(n)])
    return {"true_share": float(np.isfinite(true).mean()), "conv_share": float(np.isfinite(conv).mean()),
            "conv_median": float(np.nanmedian(conv)), "true_median": float(np.nanmedian(true)),
            "strikes": len(strikes(cfg))}


def no_impact():
    """Exercise 7: the same days with no price impact; the trade's mean (bp) and t, unconditional and by true regime."""
    d = simulate_days(FlowConfig(impact=0.0))
    S, g = d["S"], d["true_gamma"]
    x = 1e4 * np.sign(S[:, LAST] / S[:, 0] - 1) * (S[:, -1] / S[:, LAST] - 1)
    rule = np.where(g < 0, x, -x)
    t = lambda y: float(y.mean() / y.std(ddof=1) * math.sqrt(len(y)))          # noqa: E731
    return {"mean": float(x.mean()), "t": t(x), "rule_mean": float(rule.mean()), "rule_t": t(rule)}
