"""Monitoring and retraining (One Quant Book 12, chapter 27).

A linear cross-sectional model (five features, 200 names a day) fitted on 60 days and run for 400 more, with its
monitors: the largest population stability index and Kolmogorov-Smirnov statistic over the features, the stability
index of the predictions, the share of predictions inside the no-trade threshold, and a CUSUM on the daily information
coefficient. Thresholds are calibrated on 20 runs without failures to one false alarm a month (21 trading days). Three
failures planted at day 200 of production, each in 20 runs: a feature arriving in units a hundred times smaller, a
reversal of the strongest feature's effect, and a feature whose effect fades and whose spread grows over 150 days.
Then a challenger refitted after the reversal is run in shadow and promoted by an always-valid sequential test."""
from __future__ import annotations

import functools
import os
import pathlib
import sys

for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "mlmonitor"))
from firm_mlmonitor import (  # noqa: E402
    Cusum,
    Reference,
    calibrate_pages,
    daily_ic,
    first_alarm,
    ks,
    onsets,
    psi,
    shadow_verdict,
)

K, N, TRAIN, DAYS, START = 5, 200, 60, 400, 200
BETA = np.array([0.08, -0.06, 0.05, 0.0, 0.0])
FAILURES = ("none", "unit change", "reversal", "slow fade")
MONITORS = ("feature PSI", "feature KS", "prediction PSI", "inside threshold", "IC CUSUM")
SUSTAIN = (5, 21)
RATE = 1 / 21
K_CUSUM = 0.5


def day(rng, t, failure):
    """One day's features as the model receives them and the returns that follow."""
    X = rng.standard_normal((N, K))
    b = BETA.copy()
    if failure == "reversal" and t >= START:
        b[0] = -b[0]
    if failure == "slow fade" and t >= START:
        f = min(1.0, (t - START) / 150)
        b[2] *= 1 - f
        X[:, 2] *= 1 + 0.5 * f
    y = X @ b + rng.standard_normal(N)
    if failure == "unit change" and t >= START:
        X = X.copy()
        X[:, 1] /= 100.0
    return X, y


@functools.lru_cache(maxsize=1)
def model():
    rng = np.random.default_rng(0)
    Xs, ys = zip(*(day(rng, t, "none") for t in range(TRAIN)), strict=True)
    X, y = np.vstack(Xs), np.concatenate(ys)
    b = np.linalg.lstsq(np.column_stack([np.ones(len(y)), X]), y, rcond=None)[0]
    pred = X @ b[1:] + b[0]
    thr = float(np.quantile(np.abs(pred), 0.5))                         # trade the half with the strongest forecasts
    ic_ref = float(np.mean([daily_ic(Xs[t] @ b[1:], ys[t]) for t in range(TRAIN)]))
    return b, X, pred, thr, ic_ref


def run(failure, seed):
    """Daily monitor statistics over the production days of one run."""
    b, Xref, pref, thr, ic_ref = model()
    rng = np.random.default_rng(1000 + seed)
    out = {m: np.zeros(DAYS) for m in MONITORS}
    ics, shares = np.zeros(DAYS), np.zeros(DAYS)
    refs, pref_r = [Reference(Xref[:, j]) for j in range(K)], Reference(pref)
    inside_ref = float(np.mean(np.abs(pref) < thr))
    for t in range(DAYS):
        X, y = day(rng, t, failure)
        p = X @ b[1:] + b[0]
        out["feature PSI"][t] = max(psi(refs[j], X[:, j]) for j in range(K))
        out["feature KS"][t] = max(ks(refs[j], X[:, j]) for j in range(K))
        out["prediction PSI"][t] = psi(pref_r, p)
        share = float(np.mean(np.abs(p) < thr))
        out["inside threshold"][t] = abs(share - inside_ref)
        shares[t] = share
        ics[t] = daily_ic(p, y)
    out["IC"], out["share inside"] = ics, shares
    return out


@functools.lru_cache(maxsize=4)
def runs(failure, n=20):
    return [run(failure, s) for s in range(n)]


def cusum_path(ics, k, h, target):
    c = Cusum(target, k, h)
    return np.array([float(c.update(v)) for v in ics])


@functools.lru_cache(maxsize=1)
def thresholds():
    """Thresholds at one false page a month on the no-failure runs; for the CUSUM, the h that gives it."""
    null = runs("none")
    th = {m: calibrate_pages(np.array([r[m] for r in null]), RATE) for m in MONITORS if m != "IC CUSUM"}
    ic_ref = float(np.mean([r["IC"] for r in null]))                    # the IC expected in production
    ic_sd = float(np.std(np.concatenate([r["IC"] for r in null])))
    k = K_CUSUM * ic_sd
    hs = np.round(np.arange(0.01, 1.0, 0.01), 2)
    ics = np.array([r["IC"] for r in null])                             # runs x days
    s, alarms = np.zeros((len(hs), len(ics))), np.zeros(len(hs))
    for t in range(ics.shape[1]):                                        # every h and every run at once
        s = np.maximum(0.0, s + ic_ref - ics[:, t] - k)
        hit = s > hs[:, None]
        alarms += hit.sum(axis=1)
        s[hit] = 0.0
    h = float(hs[np.argmax(alarms / ics.size <= RATE)])
    th["IC CUSUM"] = (float(k), float(h), ic_ref)
    return th


def _alarm_series(r, m, th):
    if m == "IC CUSUM":
        k, h, target = th[m]
        return cusum_path(r["IC"], k, h, target), 0.5
    return r[m], th[m]


def sustained(alarms, start):
    """Days from start to the first day that opens a 21-day window with at least 5 alarm days (a page that keeps
    coming back); None if none does."""
    a = np.asarray(alarms, dtype=bool)[start:].astype(int)
    n, w = SUSTAIN
    c = np.convolve(a, np.ones(w, dtype=int), "valid")
    hit = np.flatnonzero(c >= n)
    return int(hit[0]) if len(hit) else None


@functools.lru_cache(maxsize=1)
def delays():
    """For each failure (and for none, the baseline) and monitor, medians over 20 runs of: days from day 200 to the
    first alarm, and to a sustained alarm (a run with neither counts as 200); with the false pages a day on days
    0-200."""
    th = thresholds()
    out = {}
    for f in FAILURES:
        for m in MONITORS:
            d, su, fa = [], [], []
            for r in runs(f):
                s, t = _alarm_series(r, m, th)
                a = np.asarray(s) > t
                x = first_alarm(s, t, START)
                d.append(DAYS - START if x is None else x)
                x = sustained(a, START)
                su.append(DAYS - START if x is None else x)
                fa.append(float(onsets(a[:START]).mean()))
            out[(f, m)] = (float(np.median(d)), float(np.median(su)), float(np.mean(fa)))
    return out


def shadow_run(seed, failure="reversal", min_days=10):
    """After the reversal: a challenger refitted on the first 40 days after it, run in shadow from day 240 beside the
    champion; the number of shadow days until the always-valid p-value of their IC difference falls below 0.05."""
    b, *_ = model()
    rng = np.random.default_rng(5000 + seed)
    data = [day(rng, t, failure) for t in range(START + 40 + 60)]
    Xs = np.vstack([d[0] for d in data[START:START + 40]])
    ys = np.concatenate([d[1] for d in data[START:START + 40]])
    bc = np.linalg.lstsq(np.column_stack([np.ones(len(ys)), Xs]), ys, rcond=None)[0]
    ic_ch = [daily_ic(X @ bc[1:], y) for X, y in data[START + 40:]]
    ic_cp = [daily_ic(X @ b[1:], y) for X, y in data[START + 40:]]
    p = shadow_verdict(ic_ch, ic_cp, min_days=min_days)
    hit = np.flatnonzero(p < 0.05)
    return (int(hit[0]) + 1 if len(hit) else None), float(np.mean(ic_ch)), float(np.mean(ic_cp)), bc, p


@functools.lru_cache(maxsize=1)
def shadow(n=20):
    """Over 20 runs: median days to promotion, the mean shadow ICs of challenger and champion, and the challenger's
    coefficient on the reversed feature."""
    rs = [shadow_run(s) for s in range(n)]
    days = [r[0] for r in rs]
    return {"median days": float(np.median([d if d is not None else 60 for d in days])),
            "max days": max(d if d is not None else 60 for d in days), "promoted": sum(d is not None for d in days),
            "challenger IC": float(np.mean([r[1] for r in rs])), "champion IC": float(np.mean([r[2] for r in rs])),
            "challenger b1": float(np.mean([r[3][1] for r in rs]))}


def false_promotions(n=100, min_days=10):
    """Without a failure, a challenger refitted on 40 fresh days replaces nothing better: the share of 100 runs in
    which the shadow test would promote it anyway within its 60 days, and the challenger's mean IC deficit."""
    rs = [shadow_run(s, "none", min_days) for s in range(n)]
    return sum(r[0] is not None for r in rs) / n, float(np.mean([r[2] - r[1] for r in rs]))


def ic_levels(n=20):
    """Mean daily IC of the champion: without failures (the CUSUM's target), and over days 200-400 under each (the
    fade over its last 50 days), with the daily IC's standard deviation on days without failures."""
    out = {"before": float(np.mean([r["IC"] for r in runs("none")])),
           "sd": float(np.std(np.concatenate([r["IC"] for r in runs("none")])))}
    for f in FAILURES[1:3]:
        out[f] = float(np.mean([r["IC"][START:].mean() for r in runs(f)]))
    out["slow fade"] = float(np.mean([r["IC"][DAYS - 50:].mean() for r in runs("slow fade")]))
    return out


def days_to_see(drop, sd, alpha_z=1.6449, power_z=1.2816):
    """Days for a one-sided test at 5% with 90% power to tell a fall of `drop` in the mean daily IC from noise."""
    return ((alpha_z + power_z) * sd / drop) ** 2


def alarm_rates(failure, width=25):
    """Alarms per month (21 days) in consecutive windows of `width` days, averaged over the 20 runs, per monitor."""
    th = thresholds()
    out = {}
    for m in MONITORS:
        rates = []
        for r in runs(failure):
            s, t = _alarm_series(r, m, th)
            s = np.asarray(s) > t
            rates.append([s[a:a + width].mean() * 21 for a in range(0, DAYS, width)])
        out[m] = np.mean(rates, axis=0)
    return out


def rollback_run(seed, weight):
    """A challenger with a sign error on the second feature is promoted at `weight` of the book (a canary at 0.1, the
    whole book at 1); the IC CUSUM rolls it back. Returns the days until the rollback and the IC given up, in
    IC-days weighted by capital, against keeping the champion."""
    b, *_ = model()
    k, h, target = thresholds()["IC CUSUM"]
    bad = b.copy()
    bad[2] = -bad[2]
    rng = np.random.default_rng(9000 + seed)
    c = Cusum(target, k, h)
    lost = 0.0
    for t in range(DAYS - START):
        X, y = day(rng, t, "none")
        ic_bad, ic_ok = daily_ic(X @ bad[1:], y), daily_ic(X @ b[1:], y)
        lost += weight * (ic_ok - ic_bad)
        if c.update(ic_bad):
            return t + 1, lost
    return None, lost


def rollbacks(n=20):
    rs = [rollback_run(s, 1.0) for s in range(n)]
    days = np.array([d for d, _ in rs], dtype=float)
    cost = np.array([x for _, x in rs])
    return {"median days": float(np.median(days)), "max days": float(days.max()),
            "cost full": float(np.mean(cost)), "cost canary": float(np.mean(cost) * 0.1)}


def pooled_series(failure, seed, pool=20):
    """Exercise 7: the largest feature index over the last `pool` days' samples together, on the same data as run()."""
    _, Xref, *_ = model()
    refs = [Reference(Xref[:, j]) for j in range(K)]
    pr = np.maximum(np.array([r.shares for r in refs]), 1e-4)
    rng = np.random.default_rng(1000 + seed)
    counts, out = np.zeros((DAYS, K, 10)), np.zeros(DAYS)
    for t in range(DAYS):
        X, _ = day(rng, t, failure)
        for j in range(K):
            counts[t, j] = np.bincount(np.searchsorted(refs[j].edges, X[:, j]), minlength=10)
        c = counts[max(0, t - pool + 1):t + 1].sum(axis=0)
        px = np.maximum(c / c.sum(axis=1, keepdims=True), 1e-4)
        out[t] = float(np.max(np.sum((px - pr) * np.log(px / pr), axis=1)))
    return out


def continuous(alarms, start, w=21):
    """Days from start to the first run of w consecutive alarm days; None if none."""
    a = np.asarray(alarms, dtype=bool)[start:].astype(int)
    hit = np.flatnonzero(np.convolve(a, np.ones(w, dtype=int), "valid") >= w)
    return int(hit[0]) if len(hit) else None


@functools.lru_cache(maxsize=1)
def pooled(pool=20, n=20):
    """Exercise 7: threshold at one page a month (days from `pool` on, once the window is full), the alarm days per
    page without failures, and the median first and sustained delays under each failure."""
    series = {f: [pooled_series(f, s, pool) for s in range(n)] for f in FAILURES}
    null = np.array([x[pool:] for x in series["none"]])
    th = calibrate_pages(null, RATE)
    out = {"threshold": th, "days per page": float((null > th).sum() / onsets(null > th).sum())}
    for f in FAILURES:
        d, su = [], []
        for x in series[f]:
            a = first_alarm(x, th, START)
            d.append(DAYS - START if a is None else a)
            a = sustained(x > th, START)
            su.append(DAYS - START if a is None else a)
        out[f] = (float(np.median(d)), float(np.median(su)))
    fade = [continuous(x > th, START) for x in series["slow fade"]]
    daily = [continuous(np.asarray(r["feature PSI"]) > thresholds()["feature PSI"], START) for r in runs("slow fade")]
    out["month in alarm, fade"] = (float(np.median(fade)), float(np.median([DAYS - START if x is None else x
                                                                            for x in daily])))
    out["false months"] = sum(continuous(x > th, pool) is not None for x in series["none"])
    return out
