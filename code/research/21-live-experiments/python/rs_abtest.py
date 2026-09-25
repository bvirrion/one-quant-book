"""Live experiments (One Quant Book 7, chapter 21).

A simulated A/B test of two execution algorithms on the firm's order flow: 2,400 parent orders a day in 500 stocks,
each with an implementation shortfall in basis points made of the pre-trade cost estimate, the estimate's error, the
beta-adjusted market move over the order's scheduled window (signed by side), idiosyncratic noise and a day effect.
The new algorithm saves 0.30 bp on its own orders but adds 0.25 bp to the orders of the same stock, side and day that
trade alongside it (it trades earlier in the window and leaves them more impact): interference. Randomisation by
order, by day and by stock-day; the difference in means, stratification, CUPED; power and the days needed; peeking
and the mixture sequential test; the canary's detection time. NumPy only.
"""
from __future__ import annotations

import functools
import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm" / "abtest"))
from firm_abtest import (  # noqa: E402
    always_valid_p,
    assign,
    cluster_diff,
    cuped,
    demean_by,
    diff_means,
    mde,
    sample_size,
    srm_pvalue,
    stratified,
)

ORDERS, STOCKS = 2400, 500
EFFECT, SPILL = -0.30, 0.25
SD_MODEL, SD_MKT, SD_IDIO, SD_DAY = 5.0, 15.0, 15.0, 3.0
SEED, TARGET, TAU = 21, 0.30, 0.30


@functools.lru_cache(maxsize=1)
def universe():
    """Per-stock daily volatility and spread (bp) and the popularity of each stock in the firm's flow."""
    rng = np.random.default_rng(SEED)
    sigma = np.exp(np.log(180.0) + 0.35 * rng.standard_normal(STOCKS))
    spread = np.exp(np.log(4.0) + 0.5 * rng.standard_normal(STOCKS))
    pop = 1.0 / np.arange(1, STOCKS + 1)
    return sigma, spread, pop / pop.sum()


def orders(days: int, seed: int, share: float = 0.5, unit: str = "order", treat=None):
    """One experiment. `unit` is 'order', 'day' or 'stockday'; `treat` (0 or 1) forces every order into one arm
    (a rollout). Returns a dict of order-level arrays."""
    sigma, spread, pop = universe()
    rng = np.random.default_rng(seed)
    n = days * ORDERS
    day = np.repeat(np.arange(days), ORDERS)
    stock = rng.choice(STOCKS, size=n, p=pop)
    buy = rng.random(n) < 0.5
    q = np.minimum(np.exp(np.log(0.004) + 1.2 * rng.standard_normal(n)), 0.1)
    pre = spread[stock] / 2 + 0.6 * sigma[stock] * np.sqrt(q)
    mkt = SD_MKT * rng.standard_normal(n)
    noise = SD_MODEL * rng.standard_normal(n) + SD_IDIO * rng.standard_normal(n)
    dayfx = SD_DAY * rng.standard_normal(days)[day]
    cell = (day * STOCKS + stock) * 2 + buy
    if treat is not None:
        t = np.full(n, bool(treat))
    elif unit == "order":
        t = rng.random(n) < share
    elif unit == "day":
        t = (rng.random(days) < share)[day]
    else:
        t = (rng.random(days * STOCKS) < share)[day * STOCKS + stock]
    size = np.bincount(cell, minlength=2 * days * STOCKS)[cell]
    treated = np.bincount(cell, weights=t, minlength=2 * days * STOCKS)[cell]
    sib = np.where(size > 1, (treated - t) / np.maximum(size - 1, 1), 0.0)
    y = pre + mkt + noise + dayfx + EFFECT * t + SPILL * sib
    return {"y": y, "t": t, "pre": pre, "mkt": mkt, "day": day, "stock": stock, "cell": cell,
            "stockday": day * STOCKS + stock, "alone": size == 1,
            "stratum": np.digitize(pre, np.quantile(pre, [0.2, 0.4, 0.6, 0.8]))}


def world():
    """The flow's statistics on one long sample: sd of the shortfall, R^2 of the covariates, siblings."""
    o = orders(60, SEED + 1, treat=0)
    y = o["y"]
    sd = float(y.std())
    r_pre = 1 - float(np.var(y - np.polyval(np.polyfit(o["pre"], y, 1), o["pre"]))) / sd**2
    X = np.column_stack([o["pre"], o["mkt"]])
    Xc = X - X.mean(axis=0)
    res = y - y.mean() - Xc @ np.linalg.lstsq(Xc, y - y.mean(), rcond=None)[0]
    return {"sd": sd, "mean": float(y.mean()), "pre_sd": float(o["pre"].std()), "r2_pre": r_pre,
            "r2_both": 1 - float(res.var()) / sd**2, "with_siblings": 1 - float(o["alone"].mean())}


def rollout(days: int = 60):
    """The global effect: every order on the new algorithm against every order on the old, same market."""
    return float(orders(days, SEED + 2, treat=1)["y"].mean() - orders(days, SEED + 2, treat=0)["y"].mean())


def hook():
    """Two weeks, 10% of orders, hash-assigned by order id: the estimate, its standard error and the SRM check."""
    o = orders(10, SEED + 3, treat=0)
    ids = [f"{d}-{k}" for d in range(10) for k in range(ORDERS)]
    t = assign(ids, "algo-v2", 0.10)
    y = o["y"] + EFFECT * t                                    # 10% of flow: negligible sibling spillover here
    d, se = diff_means(y, t)
    return d, se, int(t.sum()), srm_pvalue(int(t.sum()), int((~t).sum()), 0.10)


DESIGNS = ("difference in means", "stratified", "CUPED (pre-trade)", "CUPED (pre-trade + market)", "randomised by day",
           "randomised by stock-day", "by stock-day, within day", "by stock-day, within day + CUPED")


def analyse(seed: int, days: int = 60):
    """One 60-day experiment at 50/50 under each design (same market, own assignment): (estimate, se) per design."""
    o = orders(days, seed)
    y, t = o["y"], o["t"]
    out = {"difference in means": diff_means(y, t), "stratified": stratified(y, t, o["stratum"]),
           "CUPED (pre-trade)": cuped(y, o["pre"], t)[:2],
           "CUPED (pre-trade + market)": cuped(y, np.column_stack([o["pre"], o["mkt"]]), t)[:2]}
    od = orders(days, seed, unit="day")
    out["randomised by day"] = cluster_diff(od["y"], od["t"], od["day"])
    os_ = orders(days, seed, unit="stockday")
    out["randomised by stock-day"] = cluster_diff(os_["y"], os_["t"], os_["stockday"])
    out["by stock-day, within day"] = within_day(os_, adjust=False)
    out["by stock-day, within day + CUPED"] = within_day(os_)
    return out


@functools.lru_cache(maxsize=1)
def calibration(reps: int = 100):
    """Over `reps` experiments: per design, the mean estimate, the standard deviation of the estimates, the mean
    reported standard error, and the days needed for 80% power on 0.3 bp at that standard error."""
    runs = [analyse(500 + s) for s in range(reps)]
    out = {}
    for k in DESIGNS:
        v = np.array([r[k] for r in runs])
        se = float(v[:, 1].mean())
        out[k] = (float(v[:, 0].mean()), float(v[:, 0].std()), se, days_needed(se))
    return out


def within_day(o, adjust: bool = True):
    """Stock-day randomisation analysed within each day (every day's mean removed from outcome and covariates),
    optionally with the CUPED adjustment, then the cluster-robust comparison."""
    y = demean_by(o["y"], o["day"])
    if adjust:
        X = np.column_stack([demean_by(o["pre"], o["day"]), demean_by(o["mkt"], o["day"])])
        y = y - X @ np.linalg.lstsq(X, y, rcond=None)[0]
    return cluster_diff(y, o["t"], o["stockday"])


def days_needed(se: float, days: int = 60, effect: float = TARGET):
    """Trading days for 80% power at a two-sided 5% test: the standard error scales with 1 / sqrt(days)."""
    return days * (se / (effect / mde(1.0))) ** 2


def simulated_power(days: int, reps: int = 100):
    """Share of `reps` order-randomised experiments of `days` days (the planted direct saving is 0.30 bp) that reject
    no effect at 5%: (difference in means, CUPED on pre-trade estimate and market move), on the same samples."""
    hits = np.zeros(2)
    for k in range(reps):
        o = orders(days, 10_000 + 1_000 * days + k)
        y = o["y"]
        d, se = diff_means(y, o["t"])
        dc, sec, _ = cuped(y, np.column_stack([o["pre"], o["mkt"]]), o["t"])
        hits += [abs(d) / se > 1.959964, abs(dc) / sec > 1.959964]
    return tuple(float(h) / reps for h in hits)


def sequential(sd: float, days: int = 120, reps: int = 4000, effect: float = 0.0, share: float = 0.5, seed: int = 5):
    """Daily looks at a running order-level comparison (day effects cancel within a day): the running estimate and
    its standard error after each day, for `reps` experiments."""
    rng = np.random.default_rng(seed)
    nt, nc = share * ORDERS, (1 - share) * ORDERS
    inc = effect + sd * math.sqrt(1 / nt + 1 / nc) * rng.standard_normal((reps, days))
    k = np.arange(1, days + 1)
    return inc.cumsum(axis=1) / k, sd * math.sqrt(1 / nt + 1 / nc) / np.sqrt(k)


def peeking(sd: float, horizons=(1, 5, 10, 20, 40, 60, 120)):
    """False-positive rate under no effect: a fixed-horizon z-test looked at every day up to the horizon, against the
    mixture sequential test's always-valid p-value."""
    d, se = sequential(sd)
    z = np.abs(d / se) > 1.959964
    p = always_valid_p(d, se, TAU)
    return {h: (float(z[:, :h].any(axis=1).mean()), float((p[:, h - 1] < 0.05).mean())) for h in horizons}


def stopping(sd: float, effect: float = -TARGET, days: int = 120, tau: float = TAU):
    """Under a real effect: the day each experiment's always-valid p-value first falls below 5% (inf if never)."""
    d, se = sequential(sd, days=days, effect=effect, seed=6)
    p = always_valid_p(d, se, tau)
    hit = p < 0.05
    return np.where(hit.any(axis=1), hit.argmax(axis=1) + 1.0, np.inf)


def canary(delta: float, sd: float, share: float, z: float = 3.0, per_day: int = ORDERS):
    """A defect adds `delta` bp to every canary order; the alarm is a one-sided z-test of canary against control.
    Canary orders before the expected alarm, and days: n = z^2 sd^2 / (delta^2 (1 - share))."""
    n = (z * sd / delta) ** 2 / (1 - share)
    return n, n / (share * per_day)


def required(sd: float, r2: float, effect: float = TARGET):
    """Days at 50/50 from the sample-size formula, raw and with a covariate adjustment of R^2 = r2."""
    return (sample_size(effect, sd) / ORDERS, sample_size(effect, sd * math.sqrt(1 - r2)) / ORDERS)
