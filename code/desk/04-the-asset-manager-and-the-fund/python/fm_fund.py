"""One Quant Book 16, chapter 4: the asset manager and the fund -- fees by investor, and liquidity terms.

Liquidity ladders: the aggregate portfolio liquidity of US qualifying hedge funds (SEC Private Funds Statistics,
2025Q3, data/desk/form_pf_liquidity.csv) and a fund with 8 per cent of its assets sellable within seven days (the
figure the UK regulator gave for the fund suspended on 3 June 2019), the rest spread illustratively. Selling
costs per bucket are illustrative.
"""
import csv
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/fundterms"))
import firm_fundterms as ft  # noqa: E402

DATA = ROOT / "data/desk"
COSTS = {1: 0.001, 7: 0.005, 30: 0.015, 90: 0.04, 180: 0.08, 365: 0.15, 730: 0.20}
FIRE = 2.0            # selling a bucket faster than its horizon costs twice its normal cost


def form_pf():
    with open(DATA / "form_pf_liquidity.csv") as f:
        return [{k: float(v) for k, v in r.items()} for r in csv.DictReader(f)]


def restrictions():
    with open(DATA / "form_pf_restrictions.csv") as f:
        return {r["type"]: float(r["usd_bn"]) for r in csv.DictReader(f)}


def ladder_from_cumulative(cum):
    """Buckets from cumulative shares at 1, 7, 30, 90, 180, 365 days (per cent); the rest takes 730 days."""
    days = [1, 7, 30, 90, 180, 365]
    out, prev = [], 0.0
    for d, c in zip(days, cum, strict=True):
        out.append(ft.Bucket(d, (c - prev) / 100, COSTS[d]))
        prev = c
    out.append(ft.Bucket(730, (100 - prev) / 100, COSTS[730]))
    return out


def hedge_fund_ladder():
    return ladder_from_cumulative([r["portfolio_pct"] for r in form_pf()])


def illiquid_ladder():
    """8 per cent within seven days (4 + 4), then illustrative: 12, 16, 20, 15, and 25 beyond a year."""
    return ladder_from_cumulative([4, 8, 20, 36, 56, 75])


def stress(ladder, request=0.30, notice=7, **kw):
    return ft.redeem(ladder, request, notice, fire=FIRE, **kw)


def stress_table(request=0.30, notice=7):
    rows = {}
    for name, lad in (("hedge funds", hedge_fund_ladder()), ("illiquid fund", illiquid_ladder())):
        for label, kw in (("liquid first", {}), ("pro rata", {"policy": "pro_rata"}), ("gate 10%", {"gate": 0.10}),
                          ("liquid first, swing", {"swing": True})):
            r = stress(lad, request, notice, **kw)
            rows[(name, label)] = (r["paid"], r["cost"], r["dilution_stayers"],
                                   ft.ladder_share_within(r["ladder_after"], 7))
    return rows


def free_ride(perf=0.20):
    """Investor A subscribes 100 at a NAV of 1.00; the fund falls 10 per cent; B subscribes 100 at 0.90; the fund
    regains its mark and gains 5 per cent more. Performance fees by investor, pooled and in series."""
    rets = [-0.10, 1 / 0.9 * 1.05 - 1]
    return ft.pooled_vs_series(rets, [(0, 100.0), (1, 100.0)], ft.ff.FeeTerms(mgmt=0.0, perf=perf)), rets


def crystallisation(perf=0.20, years=5, mu=0.08, vol=0.12, seeds=range(1, 1001)):
    """Mean performance fee per unit of starting capital over `years` of monthly returns, crystallised monthly,
    quarterly and annually (1,000 seeds)."""
    out = {1: [], 3: [], 12: []}
    for s in seeds:
        rng = np.random.default_rng(s)
        r = rng.normal(mu / 12, vol / np.sqrt(12), 12 * years)
        for k in out:
            out[k].append(ft.crystallised(r, perf, k))
    return {k: float(np.mean(v)) for k, v in out.items()}
