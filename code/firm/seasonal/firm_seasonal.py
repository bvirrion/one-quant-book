"""firm.seasonal -- calendar rules and seasonality (build of One Quant Book 8, chapter 23).

A stylised trading calendar (years of 12 months of 21 trading days, weeks of 5, and a fixed set of holidays), a
generator of calendar rules (day of the week, month of the year, day of the month, turn-of-the-month windows, days
before and after holidays, weeks of the month, fortnights of the year), a tester that compares each rule's days with
the others (Welch t-statistic and two-sided p-value), a seasonal profile by phase, and the same-calendar-month
signal of Heston and Sadka on a panel of monthly returns. NumPy only.

API (stable):
    calendar(years, holidays)          dict of (T,) arrays: dow, dom, moy, year, pre, post (holiday neighbours)
    rules(cal)                         list of (name, mask)
    score_rules(r, rules)              (names, t, p): Welch t of mean(r on rule days) - mean(r on other days)
    profile(x, period)                 mean of x by phase (index mod period)
    same_month(M, lags)                (months, N) signal: mean return in the same calendar month 12, 24, ... months ago
"""
from __future__ import annotations

import math

import numpy as np

DPM, MPY, DPW = 21, 12, 5
HOLIDAYS = ((0, 0), (0, 12), (1, 10), (3, 18), (5, 15), (6, 2), (8, 0), (10, 16), (11, 17))   # (month, day index)


def calendar(years: int, holidays=HOLIDAYS):
    T = years * MPY * DPM
    t = np.arange(T)
    dom, moy, year = t % DPM, (t // DPM) % MPY, t // (DPM * MPY)
    hol = np.zeros(T, bool)
    for m, d in holidays:
        hol[(moy == m) & (dom == d)] = True                          # the trading day after a holiday
    post = hol
    pre = np.zeros(T, bool)
    pre[:-1] = hol[1:]
    return {"dow": t % DPW, "dom": dom, "moy": moy, "year": year, "pre": pre, "post": post}


def rules(cal):
    out = [(f"weekday {k}", cal["dow"] == k) for k in range(DPW)]
    out += [(f"month {k + 1}", cal["moy"] == k) for k in range(MPY)]
    out += [(f"day {k + 1} of month", cal["dom"] == k) for k in range(DPM)]
    for last in (1, 2, 3):
        for first in (1, 2, 3, 4):
            out.append((f"turn of month -{last}..+{first}", (cal["dom"] >= DPM - last) | (cal["dom"] < first)))
    out += [("pre-holiday", cal["pre"]), ("post-holiday", cal["post"])]
    out += [(f"week {k + 1} of month", np.minimum(cal["dom"] // DPW, 3) == k) for k in range(4)]
    fortnight = (cal["moy"] * DPM + cal["dom"]) // 10
    out += [(f"fortnight {k + 1}", fortnight == k) for k in range(int(fortnight.max()) + 1)]
    out += [(f"last {k} days of month", cal["dom"] >= DPM - k) for k in range(1, 6)]
    out += [(f"first {k} days of month", cal["dom"] < k) for k in range(1, 6)]
    out += [("first half of month", cal["dom"] < DPM // 2), ("second half of month", cal["dom"] >= DPM // 2)]
    out += [("quarter-end month", cal["moy"] % 3 == 2), ("quarter-start month", cal["moy"] % 3 == 0),
            ("first half of year", cal["moy"] < 6), ("May to October", (cal["moy"] >= 4) & (cal["moy"] <= 9)),
            ("December and January", (cal["moy"] == 11) | (cal["moy"] == 0)),
            ("summer", (cal["moy"] >= 5) & (cal["moy"] <= 7))]
    return out


def score_rules(r, rule_list):
    r = np.asarray(r, float)
    names, ts = [], []
    for name, m in rule_list:
        a, b = r[m], r[~m]
        se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
        names.append(name)
        ts.append((a.mean() - b.mean()) / se)
    t = np.array(ts)
    p = np.array([math.erfc(abs(x) / math.sqrt(2)) for x in t])
    return names, t, p


def profile(x, period: int):
    x = np.asarray(x, float)
    return np.array([np.nanmean(x[k::period]) for k in range(period)])


def same_month(M, lags=(1, 2, 3, 4, 5)):
    M = np.asarray(M, float)
    s = np.full(M.shape, np.nan)
    for t in range(len(M)):
        past = np.array([M[t - 12 * k] for k in lags if t - 12 * k >= 0])
        if len(past):
            n = (~np.isnan(past)).sum(0)
            s[t] = np.where(n > 0, np.nansum(past, axis=0) / np.maximum(n, 1), np.nan)
    return s
