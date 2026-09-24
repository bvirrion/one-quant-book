"""Autocallables (Book 5, Chapter 18): a three-year Phoenix on chapter 9's index under local volatility, its fair
coupon, vega by expiry bucket, skew, dividend and correlation sensitivities, a snowball, and the issuer's hedge
across the knock-in. Zero rates; prices per 100 of notional."""
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "volsurface", "localvol", "barrier", "autocall"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_autocall import TermSheet, hedge_across_ki, price, snowball_tail  # noqa: E402
from firm_localvol import build_grid  # noqa: E402
from firm_svi import ssvi  # noqa: E402

GRID_T = np.concatenate([[0.004], np.arange(0.02, 3.0601, 0.04)])
GRID_K = np.linspace(-1.6, 0.8, 161)
PILLARS = (1.0, 2.0, 3.0)


def theta(t: float) -> float:
    return (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t


def w_surface(rho: float = -0.6, bump=None):
    """Chapter 9's surface in total variance, with an optional implied-volatility bump function bump(t)."""
    def w(k: float, t: float) -> float:
        base = float(ssvi(k, theta(t), rho, 1.0, 0.45))
        if bump is None:
            return base
        return (math.sqrt(base / t) + bump(t)) ** 2 * t
    return w


def tent(i: int, size: float = 0.01):
    """Implied-volatility bump of `size` on pillar i, linear to zero at the neighbouring pillars (flat beyond the
    ends)."""
    p = PILLARS

    def f(t: float) -> float:
        if i == 0 and t <= p[0]:
            return size
        if i == len(p) - 1 and t >= p[-1]:
            return size
        lo = p[i - 1] if i > 0 else p[0]
        hi = p[i + 1] if i < len(p) - 1 else p[-1]
        if lo <= t <= p[i] and p[i] > lo:
            return size * (t - lo) / (p[i] - lo)
        if p[i] <= t <= hi and hi > p[i]:
            return size * (hi - t) / (hi - p[i])
        return 0.0
    return f


def lv_sigma(rho: float = -0.6, bump=None, carry: float = 0.0):
    g = build_grid(w_surface(rho, bump), GRID_T, GRID_K, carry=carry)
    return lambda t, s: g.sigma(t, 100.0 * s)


def flat(vol: float):
    return lambda t, s: np.full_like(s, vol)


PHOENIX = TermSheet(obs_times=tuple(np.arange(1, 13) / 4), trigger=1.0, coupon=1.0, coupon_barrier=0.7, memory=True,
                    protection=0.6, ki_daily=False)


def with_coupon(ts: TermSheet, c: float) -> TermSheet:
    return TermSheet(ts.obs_times, ts.trigger, c, ts.coupon_barrier, ts.memory, ts.protection, ts.ki_daily,
                     ts.snowball_rate, ts.first_call)


def fair_coupon(sigma_fn, ts: TermSheet = PHOENIX, q: float = 0.0, n: int = 100_000, seed: int = 18, **kw) -> dict:
    """The quarterly coupon that prices the note at par: the price is linear in the coupon."""
    p0 = price(with_coupon(ts, 0.0), sigma_fn, q=q, n_paths=n, seed=seed, **kw)["price"]
    p1 = price(with_coupon(ts, 1.0), sigma_fn, q=q, n_paths=n, seed=seed, **kw)
    c = (100.0 - p0) / (p1["price"] - p0)
    return {"coupon": c, "annual": 4 * c, "zero_coupon_value": p0, "per_coupon_point": p1["price"] - p0,
            "call_probs": p1["call_probs"], "ki_prob": p1["ki_prob"], "maturity_prob": p1["maturity_prob"]}


@functools.cache
def sensitivities(n: int = 100_000, seed: int = 18) -> dict:
    """At the local-volatility fair coupon: price changes (per 100) for +1 vol point by pillar and in parallel, a
    steeper skew (rho -0.7), a 1% dividend yield, and flat-volatility prices for comparison."""
    base_sig = lv_sigma()
    fc = fair_coupon(base_sig, n=n, seed=seed)
    ts = with_coupon(PHOENIX, fc["coupon"])

    def px(sig, q=0.0):
        return price(ts, sig, q=q, n_paths=n, seed=seed)["price"]
    base = px(base_sig)
    out = {"fair": fc, "base": base}
    out["vega_buckets"] = [px(lv_sigma(bump=tent(i))) - base for i in range(len(PILLARS))]
    out["vega_parallel"] = px(lv_sigma(bump=lambda t: 0.01)) - base
    out["skew"] = px(lv_sigma(rho=-0.7)) - base
    out["dividend"] = px(lv_sigma(carry=-0.01), q=0.01) - base
    atm3 = math.sqrt(theta(3.0) / 3.0)
    out["flat_atm3"] = px(flat(atm3))
    out["flat_vol"] = atm3
    return out


@functools.cache
def price_vs_vol(shifts=(-0.04, -0.02, 0.0, 0.02, 0.04, 0.06), n: int = 60_000, seed: int = 18) -> list[tuple]:
    base_sig = lv_sigma()
    fc = fair_coupon(base_sig, n=n, seed=seed)
    ts = with_coupon(PHOENIX, fc["coupon"])
    return [(d, price(ts, lv_sigma(bump=lambda t, d=d: d), n_paths=n, seed=seed)["price"]) for d in shifts]


@functools.cache
def worst_of(corrs=(0.5, 0.7), n: int = 60_000, seed: int = 18) -> dict:
    """The same Phoenix on the worst of three identical underlyings (each with the local volatility), fair coupon
    by correlation."""
    sig = lv_sigma()
    out = {}
    for c in corrs:
        corr = np.full((3, 3), c) + (1 - c) * np.eye(3)
        out[c] = fair_coupon(sig, n=n, seed=seed, corr=corr, n_assets=3)
    return out


# ---------------------------------------------------------------- the snowball and the cliff
SNOWBALL = TermSheet(obs_times=tuple(np.arange(1, 25) / 12), trigger=1.03, coupon=0.0, coupon_barrier=0.0,
                     memory=False, protection=0.75, ki_daily=True, snowball_rate=0.15, first_call=2)


@functools.cache
def snowball_price(n: int = 100_000, seed: int = 18) -> dict:
    return price(SNOWBALL, lv_sigma(), n_paths=n, seed=seed)


@functools.cache
def cliff(vol: float = 0.25, notional: float = 100e6) -> dict:
    """One month before maturity, knock-in at 75%, the full two-year snowball coupon (30%) due if never knocked
    in: the hedge sold on a 1% fall from 1% above the barrier, and the issuer's delta by spot."""
    out = {m: hedge_across_ki(0.75, m / 12, vol, 30.0, notional) for m in (1, 3, 12)}
    spots = np.linspace(0.7501, 0.95, 120)
    h = 1e-4

    def delta(x, knocked):
        up = snowball_tail(x + h, 0.75, 1 / 12, vol, 30.0, knocked)
        return (up - snowball_tail(x - h, 0.75, 1 / 12, vol, 30.0, knocked)) / (2 * h) / 100
    before = [delta(x, False) for x in spots]
    after_spots = np.linspace(0.60, 0.7499, 60)
    after = [delta(x, True) for x in after_spots]
    out["curve"] = (spots, np.array(before), after_spots, np.array(after))
    return out


@functools.cache
def fair_coupon_daily_ki(n: int = 100_000, seed: int = 18) -> dict:
    """The Phoenix with its 60% protection barrier monitored daily instead of at maturity."""
    ts = TermSheet(PHOENIX.obs_times, PHOENIX.trigger, 1.0, PHOENIX.coupon_barrier, PHOENIX.memory, PHOENIX.protection,
                   True)
    return fair_coupon(lv_sigma(), ts, n=n, seed=seed)
