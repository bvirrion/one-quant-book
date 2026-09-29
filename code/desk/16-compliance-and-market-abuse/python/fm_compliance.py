"""One Quant Book 16, chapter 16: a year of personal-trade pre-clearance, and an alert queue with fixed analyst hours.

Synthetic. 150 employees ask to trade 60 listed names on 250 days; the firm trades 15 of them often; deals put names
on the restricted list and the watch list for weeks; three projects wall-cross five people each. The alert stream is
firm.surveil's spoofing account-days (One Quant Book 9), scored by its best detector; each alert takes half an hour.
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/compliance"))
sys.path.insert(0, str(ROOT / "code/firm/surveil"))
import firm_compliance as fc  # noqa: E402
import firm_surveil as fs  # noqa: E402

DAYS, EMPLOYEES, NAMES, REQUESTS = 250, 150, 60, 1200
HOURS_PER_ALERT = 0.5
DEFAULT_RATE = 0.05
RATES = tuple(round(x, 4) for x in np.r_[np.arange(0.001, 0.02, 0.001), np.arange(0.02, 0.105, 0.005), 0.15, 0.2])


def year(seed=16):
    rng = np.random.default_rng(seed)
    syms = [f"N{i:02d}" for i in range(NAMES)]
    restricted = [(syms[int(rng.integers(0, NAMES))], int(a), int(a + rng.integers(20, 41)))
                  for a in rng.integers(0, 220, 8)]
    watch = [(syms[int(rng.integers(0, NAMES))], int(a), int(a + rng.integers(10, 31)))
             for a in rng.integers(0, 230, 6)]
    lists = fc.Lists(restricted, watch)
    traded = syms[:15]
    firm_trades = {s: sorted(int(d) for d in np.nonzero(rng.random(DAYS) < 0.3)[0]) for s in traded}
    reg = fc.Register()
    for p, (s, day) in enumerate(zip(rng.choice(syms, 3, replace=False), (40, 120, 190), strict=True)):
        for e in rng.choice(EMPLOYEES, 5, replace=False):
            reg.cross(int(e), f"project {p + 1}", str(s), day)
        reg.cleanse(f"project {p + 1}", day + 35)
    reqs = sorted((int(rng.integers(0, DAYS)), int(rng.integers(0, EMPLOYEES)), syms[int(rng.integers(0, NAMES))],
                   int(rng.choice([1, 1, -1]))) for _ in range(REQUESTS))
    for p, e in enumerate(reg.entries):             # planted: each crossed person asks once during their project
        reqs.append((e[3] + 5 + p, e[0], e[2], 1))
    reqs.sort()
    holdings, out = {}, []
    for day, emp, sym, side in reqs:
        insiders = {(i, sym) for i in reg.insiders(sym, day)}
        if side < 0 and (emp, sym) not in holdings:
            side = 1
        ok, why = fc.preclear((emp, sym, side, day), lists, firm_trades, holdings, insiders)
        if ok and side > 0:
            holdings.setdefault((emp, sym), day)
        if ok and side < 0:
            holdings.pop((emp, sym), None)
        out.append((day, emp, sym, side, ok, why))
    return out


def reasons(seed=16):
    out = {}
    for *_, why in year(seed):
        out[why] = out.get(why, 0) + 1
    return out


def alerts():
    d = fs.spoofing_days()
    return fs.spoof_scores(d)["gap x cancel"], d["label"]


def queue(hours, order="arrival"):
    score, label = alerts()
    cap = int(hours / HOURS_PER_ALERT)
    best, res = fc.best_rate(score, label, cap, RATES, order)
    default = fc.triage(score, label, DEFAULT_RATE, cap, order)
    return {"capacity": cap, "best_rate": best, "best_found": res[best], "curve": res, "default": default,
            "true": int(label.sum())}


def naive(hours=50):
    d = fs.spoofing_days()
    s = fs.spoof_scores(d)["order-to-trade"]
    return fc.triage(s, d["label"], DEFAULT_RATE, int(hours / HOURS_PER_ALERT))
