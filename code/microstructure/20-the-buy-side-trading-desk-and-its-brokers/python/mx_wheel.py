"""One Quant Book 10, chapter 20: a buy-side desk's algo wheel over six brokers.

    EFFECTS, desk(months, seed)      the desk's simulated flow: ORDERS a month; each order's difficulty (its pre-trade
                                     cost estimate, lognormal, mean 15 bp, s.d. 25 bp), its cost = the broker's effect +
                                     difficulty + noise (Student t with 4 degrees of freedom, s.d. 30 bp)
    cost_of(broker, flow)            the costs the flow would have had with those brokers (common random numbers)
    power_study()                    uniform wheel: the probability of telling broker 1 (the best) from broker 2 with
                                     a two-sided 5% test, raw and difficulty-adjusted, against months of flow
    stratified_study()               the dispersion of the raw estimate of that difference, random against
                                     stratified allocation, after 12 months
    thompson_study()                 24 months of Thompson sampling against the uniform wheel: excess cost over
                                     always choosing the best broker, share of flow to it, power on the best pair
    routing_study()                  the desk without a wheel: its traders send the hardest orders to the broker they
                                     trust most, and the raw ranking puts that broker last
    card()                           a year of the uniform wheel as a broker scorecard
All deterministic (fixed seeds).
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for c in ("algowheel", "tca"):
    sys.path.insert(0, str(ROOT / "code" / "firm" / c))
from firm_algowheel import Thompson, evaluate, months_needed, scorecard, stratified_allocation  # noqa: E402

EFFECTS = np.array([0.0, 3.0, 4.0, 5.0, 6.0, 8.0])        # bp, broker 1 the best
K = len(EFFECTS)
ORDERS = 600
D_MEAN, D_SD, NOISE_SD, DOF = 15.0, 25.0, 30.0, 4
NAMES = tuple(f"broker {i + 1}" for i in range(K))


def desk(months: int, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n = months * ORDERS
    s2 = math.log(1 + (D_SD / D_MEAN) ** 2)
    d = rng.lognormal(math.log(D_MEAN) - s2 / 2, math.sqrt(s2), n)
    eps = rng.standard_t(DOF, n) * NOISE_SD / math.sqrt(DOF / (DOF - 2))
    return {"d": d, "eps": eps, "month": np.repeat(np.arange(months), ORDERS), "rng": rng}


def cost_of(broker, flow) -> np.ndarray:
    return EFFECTS[np.asarray(broker)] + flow["d"] + flow["eps"]


def _test(cost, broker, d, adjust):
    ev = evaluate(cost, broker, d, K, adjust)
    diff = ev["mean"][1] - ev["mean"][0]
    se = math.sqrt(ev["cov"][0, 0] + ev["cov"][1, 1] - 2 * ev["cov"][0, 1])
    return diff, se


MONTHS = tuple(range(2, 41, 2))


@functools.cache
def power_study(reps: int = 300) -> dict:
    top = max(MONTHS)
    hits = {True: np.zeros(len(MONTHS)), False: np.zeros(len(MONTHS))}
    for r in range(reps):
        f = desk(top, 2000 + r)
        b = f["rng"].integers(0, K, len(f["d"]))
        c = cost_of(b, f)
        for i, m in enumerate(MONTHS):
            sel = f["month"] < m
            for adj in (True, False):
                diff, se = _test(c[sel], b[sel], f["d"][sel], adj)
                hits[adj][i] += diff / se > 1.959964
    power = {k: v / reps for k, v in hits.items()}

    def first(p):
        return next((m for m, x in zip(MONTHS, p, strict=True) if x >= 0.8), None)
    sd_raw = math.sqrt(NOISE_SD**2 + D_SD**2)
    return {"power_adj": power[True], "power_raw": power[False], "months_adj": first(power[True]),
            "months_raw": first(power[False]), "formula_adj": months_needed(3.0, NOISE_SD, ORDERS, K),
            "formula_raw": months_needed(3.0, sd_raw, ORDERS, K), "sd_raw": sd_raw}


@functools.cache
def stratified_study(reps: int = 400, months: int = 12) -> dict:
    est = {"random": [], "stratified": []}
    for r in range(reps):
        f = desk(months, 3000 + r)
        rng = f["rng"]
        for name, b in (("random", rng.integers(0, K, len(f["d"]))),
                        ("stratified", stratified_allocation(f["d"], K, 20, rng))):
            est[name].append(_test(cost_of(b, f), b, f["d"], False)[0])
    return {k: (float(np.mean(v)), float(np.std(v, ddof=1))) for k, v in est.items()}


@functools.cache
def thompson_study(reps: int = 60, months: int = 24) -> dict:
    out = {"thompson": [], "uniform": []}
    for r in range(reps):
        f = desk(months, 4000 + r)
        rng = f["rng"]
        n = len(f["d"])
        ts = Thompson(K, 5.0, 10.0, NOISE_SD)
        b = np.empty(n, int)
        for i in range(n):
            b[i] = ts.choose(rng)
            ts.update(b[i], EFFECTS[b[i]] + f["eps"][i])           # the adjusted cost: cost minus the estimate
        u = rng.integers(0, K, n)
        for name, bb in (("thompson", b), ("uniform", u)):
            diff, se = _test(cost_of(bb, f), bb, f["d"], True)
            by_month = (bb == 0).reshape(months, ORDERS).mean(axis=1)
            second = float((bb == 1).mean())
            out[name].append((float(EFFECTS[bb].mean()), float((bb == 0).mean()), diff / se > 1.959964,
                              by_month, second))
    return {k: {"excess": float(np.mean([x[0] for x in v])), "best": float(np.mean([x[1] for x in v])),
                "power": float(np.mean([x[2] for x in v])), "by_month": np.mean([x[3] for x in v], axis=0),
                "second": float(np.mean([x[4] for x in v]))}
            for k, v in out.items()}


@functools.cache
def routing_study(months: int = 12, seed: int = 5000) -> dict:
    """Without a wheel: orders above the 80th percentile of difficulty go to broker 1, the rest uniformly to the
    others."""
    f = desk(months, seed)
    rng = f["rng"]
    hard = f["d"] > np.quantile(f["d"], 0.8)
    b = np.where(hard, 0, rng.integers(1, K, len(f["d"])))
    c = cost_of(b, f)
    raw = evaluate(c, b, f["d"], K, adjust=False)
    adj = evaluate(c, b, f["d"], K, adjust=True)
    return {"raw": raw["mean"] - raw["mean"][1], "adj": adj["mean"] - adj["mean"][0], "adj_se": adj["se"],
            "raw_rank": np.argsort(np.argsort(raw["mean"])) + 1}


@functools.cache
def card(months: int = 12, seed: int = 6000) -> list:
    f = desk(months, seed)
    b = f["rng"].integers(0, K, len(f["d"]))
    return scorecard(cost_of(b, f), b, f["d"], K, NAMES)
