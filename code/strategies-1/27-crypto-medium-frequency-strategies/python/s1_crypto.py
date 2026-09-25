"""Crypto medium-frequency strategies (One Quant Book 8, chapter 27).

Real data (Book 3): Binance BTCUSDT perpetual funding by calendar year, 2020 to September 2026 (mean annualised rate,
negative share), turned into the yearly return on capital of a book long spot and short the perpetual, with 20% of
the notional as margin and 0.2% a year of trading costs (assumed); FTX.com's petition-time balances (customer
payables against located assets, which give a loss given failure) and its customers' daily flows in November 2022.
Synthetic (firm.cryptomf): six years of 50 coins (a 60% market factor, 80% specific volatility with Student-t tails, a
planted persistent drift with a half-life of 60 days), a weekly momentum book by lookback and cost, and exchange net
inflows that lead the next day's specific return with a correlation of -0.03; venue failure over one to eight
venues, each failing with a 5% yearly probability and losing the FTX share of assets. NumPy only.
"""
from __future__ import annotations

import csv
import functools
import math
import os
import pathlib
import sys

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import numpy as np  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "firm" / "cryptomf"))
from firm_cryptomf import CoinConfig, carry_return, flow_ic, momentum_book, simulate_coins, venue_losses  # noqa: E402

DATA = ROOT.parent / "data" / "markets-3"
MARGIN, COST, P_FAIL = 0.2, 0.002, 0.05


def _rows(name):
    with open(DATA / name) as fh:
        return list(csv.DictReader(fh))


def funding():
    out = []
    for r in _rows("binance_btcusdt_funding_by_year.csv"):
        f = float(r["mean_annualised_pct"]) / 100
        out.append((int(r["year"]), f, float(carry_return(f, MARGIN, COST)), float(r["negative_share"])))
    return out


def ftx():
    bal = _rows("ftx_com_petition_balances.csv")
    pay = sum(float(b["customer_payables"]) for b in bal)
    loc = sum(float(b["located_assets"]) for b in bal)
    flows = _rows("ftx_com_daily_flows_nov2022.csv")
    net = sum(float(f["customer_deposits"]) - float(f["customer_withdrawals"]) for f in flows)
    worst = min(flows, key=lambda f: float(f["customer_deposits"]) - float(f["customer_withdrawals"]))
    return {"payables": pay, "located": loc, "lgd": 1 - loc / pay, "net_customer": net, "worst_day": worst["date"],
            "worst_net": float(worst["customer_deposits"]) - float(worst["customer_withdrawals"])}


@functools.lru_cache(maxsize=1)
def coins():
    return simulate_coins(CoinConfig(), np.random.default_rng(27))


def momentum_table(lookbacks=(7, 28, 56), costs=(0.0, 0.001, 0.002)):
    r = coins()["r"]
    out = {}
    for lb in lookbacks:
        for c in costs:
            p = momentum_book(r, lb, 7, 0.2, c)[60:]
            out[(lb, c)] = (float(p.mean() / p.std(ddof=1) * math.sqrt(365)), float(p.mean() * 365))
    return out


def flows():
    C = coins()
    return flow_ic(C["flow"], C["r"], 30)


def venues(ks=(1, 2, 4, 8)):
    lgd = ftx()["lgd"]
    out = {}
    for k in ks:
        L = venue_losses(k, P_FAIL, lgd, 100_000, np.random.default_rng(28))
        out[k] = {"mean": float(L.mean()), "any": float((L > 0).mean()), "one": lgd / k,
                  "q99": float(np.quantile(L, 0.99))}
    return out


def venues_correlated(k: int = 4, contagion: float = 0.3, years: int = 100_000):
    """Venue losses when, in a year with a failure, every other venue also fails with probability `contagion`."""
    lgd = ftx()["lgd"]
    rng = np.random.default_rng(29)
    first = rng.random((years, k)) < P_FAIL
    spread = first.any(1)[:, None] & (rng.random((years, k)) < contagion)
    L = (first | spread).sum(1) * lgd / k
    return {"mean": float(L.mean()), "q99": float(np.quantile(L, 0.99)), "any": float((L > 0).mean())}
