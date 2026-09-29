"""One Quant Book 17, chapter 10: crypto-native firms as employers.

data/industry/crypto_headcount.csv: one listed crypto exchange's year-end employees and total revenue from its Forms
10-K; the token grant uses firm.tokencomp with illustrative parameters (volatility 80%, no drift, tax 40% at vesting).
"""
import csv
import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/tokencomp"))
import firm_tokencomp as tc  # noqa: E402

DATA = ROOT / "data/industry"
GRANT = tc.Grant(400_000.0, months=48, cliff=12, lockup=6, tax=0.40)


def headcount():
    with open(DATA / "crypto_headcount.csv") as f:
        return [dict(year=int(r["year"]), employees=int(r["employees"]) if r["employees"] else None,
                     revenue=float(r["revenue_m"])) for r in csv.DictReader(f)]


def per_head():
    """Revenue per year-end employee, $ million, for the years with both figures."""
    return {r["year"]: r["revenue"] / r["employees"] for r in headcount() if r["employees"]}


def changes():
    rows = headcount()
    out = []
    for a, b in zip(rows[:-1], rows[1:], strict=True):
        out.append(dict(year=b["year"], revenue=b["revenue"] / a["revenue"] - 1,
                        employees=(b["employees"] / a["employees"] - 1) if a["employees"] and b["employees"] else None))
    return out


@functools.cache
def grant(vol=0.8, drift=0.0, n=20_000, seed=10):
    return tc.summary(tc.simulate(GRANT, vol, drift, n, np.random.default_rng(seed)))


def grant_hist(vol=0.8, n=20_000, seed=10, width=50_000):
    net = tc.simulate(GRANT, vol, 0.0, n, np.random.default_rng(seed))["net"]
    edges = np.arange(-100_000, 1_000_001, width)
    counts, _ = np.histogram(np.clip(net, edges[0], edges[-1] - 1), bins=edges)
    return edges, counts
