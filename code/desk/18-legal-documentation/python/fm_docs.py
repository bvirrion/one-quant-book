"""One Quant Book 16, chapter 18: a fund, five counterparties and a bad year (illustrative terms, $ million).

The fund's NAV starts at 400 and runs a year of 252 days: a quiet half-year, then a three-month drawdown of a third
or more, then a partial recovery. Four counterparties have NAV triggers (drops over 21, 63 and 252 days, and a floor);
three swap dealers post and call collateral daily under their annexes on the fund's swap exposure. On the first
trip, one dealer terminates and closes out its swaps and a repo with the fund, with and without set-off.
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/docterms"))
import firm_docterms as dt  # noqa: E402

DAYS, NAV0 = 252, 400.0
TRIGGERS = [dt.Trigger("prime broker 1", ((21, 0.15), (63, 0.25), (252, 0.35))),
            dt.Trigger("prime broker 2", ((21, 0.20), (63, 0.30), (252, 0.40))),
            dt.Trigger("dealer A", ((21, 0.25), (63, 0.35), (252, 0.50)), floor=280.0),
            dt.Trigger("dealer B", ((21, 0.12), (63, 0.20), (252, 0.30)))]
ANNEXES = {"dealer A": dt.Annex(0.0, 0.5, 0.1, 5.0, {"cash": 0.0, "bonds": 0.02}),
           "dealer B": dt.Annex(2.0, 0.5, 0.1, 0.0, {"cash": 0.0}),
           "dealer C": dt.Annex(10.0, 1.0, 0.5, 0.0, {"cash": 0.0})}


def nav_path(seed=18):
    rng = np.random.default_rng(seed)
    mu = np.r_[np.full(126, 0.0004), np.full(63, -0.0065), np.full(63, 0.002)]
    r = mu + rng.normal(0, 0.008, DAYS)
    return NAV0 * np.cumprod(1 + r)


def exposures(seed=18):
    """Daily exposure of each dealer to the fund on the swaps (positive: the fund owes the dealer)."""
    rng = np.random.default_rng(seed + 1)
    nav = nav_path(seed)
    base = {"dealer A": 0.08, "dealer B": 0.05, "dealer C": 0.03}
    out = {}
    for k, b in base.items():
        out[k] = b * (NAV0 - nav) + np.cumsum(rng.normal(0, 0.4, DAYS))
    return out


def calls(seed=18):
    """Daily calls on the fund under each annex, collateral all cash and settled the same day."""
    ex = exposures(seed)
    out = {}
    for k, a in ANNEXES.items():
        held, series = 0.0, []
        for e in ex[k]:
            c = dt.call(a, e, {"cash": held})
            held += c
            series.append(c)
        out[k] = np.array(series)
    return out


def trips(seed=18):
    nav = nav_path(seed)
    return {t.name: dt.first_trip(nav, t) for t in TRIGGERS}


REPLACEMENT_COST = 3.0      # the terminating dealer's cost of replacing the swaps in the market, added to mid
REPO_EXCESS = 6.0           # collateral the dealer holds under a repo with the fund beyond the cash it lent


def first_trip(seed=18):
    t = {k: v for k, v in trips(seed).items() if v is not None}
    name = min(t, key=lambda k: t[k][0])
    return name, t[name][0], t[name][1]


def close_out_first(seed=18):
    """The dealer whose trigger trips first terminates on that day: the swaps' close-out amount is its exposure plus
    its replacement cost; it holds the cash the fund posted under the annex; under a repo it owes the fund the
    excess collateral. Balances with and without set-off."""
    name, day, _ = first_trip(seed)
    ex = float(exposures(seed)[name][day])
    posted = float(sum(calls(seed)[name][: day + 1]))
    amounts = {"swaps": ex + REPLACEMENT_COST, "repo": -REPO_EXCESS}
    coll = {"swaps": posted}
    return {"dealer": name, "day": day, "exposure": ex, "posted": posted,
            "with": dt.close_out(amounts, coll, True), "without": dt.close_out(amounts, coll, False)}
