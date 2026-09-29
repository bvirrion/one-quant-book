"""One Quant Book 16, chapter 25: a fund's first five years, with and without a seed deal ($ million; illustrative).

A manager whose strategy has a true Sharpe ratio of 1 at 10 per cent volatility launches with $50 million from a
seeder that takes 20 per cent of the fee revenue, or with $15 million from friends and family and no seeder. Fees are
1.5 and 20; costs are $2.2 million a year plus 5 basis points of assets. Investors add money as the track record's
t-statistic rises and redeem after a drawdown beyond 10 per cent.
"""
import pathlib
import sys
from dataclasses import replace

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/fundlaunch"))
import firm_fundlaunch as fl  # noqa: E402

BASE = fl.Launch()
CASES = {"seeded, 20% revenue share": BASE, "unseeded, $15 million": replace(BASE, seed=15.0, revenue_share=0.0)}
TARGET, GROSS = 100.0, 0.10


def run(case, n=2000, months=60, seed=25):
    return fl.simulate(CASES[case], seed, n, months)


def summary():
    out = {}
    for k, launch in CASES.items():
        a, f = run(k)
        fm = fl.first_month(a, TARGET)
        out[k] = {"breakeven": fl.breakeven_aum(launch, GROSS), "p36": fl.prob_reach(a, TARGET, 36),
                  "median_month": float(np.median(fm[fm > 0])) if (fm > 0).any() else None,
                  "q36": np.percentile(a[:, 35], [10, 50, 90]), "manager": fl.manager_value(a, f, launch),
                  "seeder": fl.seed_value(f, launch.revenue_share) if launch.revenue_share else 0.0,
                  "below_be_60": float((a[:, 59] < fl.breakeven_aum(launch, GROSS)).mean())}
    return out


def fan(case="seeded, 20% revenue share"):
    a, _ = run(case)
    return np.percentile(a, [10, 25, 50, 75, 90], axis=0)


def reach_curve():
    return {k: [fl.prob_reach(run(k)[0], TARGET, m) for m in range(1, 61)] for k in CASES}
