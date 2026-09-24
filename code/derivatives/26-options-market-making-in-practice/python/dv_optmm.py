"""Options market making in practice (Book 5, Chapter 26): the cost of a stale surface, the width model, hedging bands
against time-based hedging, the dividend play, and a toy market maker with bucketed vega limits."""
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/optmm"))
sys.path.insert(0, str(ROOT / "code/firm/bs"))
from firm_bs import greeks  # noqa: E402
from firm_optmm import (  # noqa: E402
    Bucket,
    Option,
    SkewSurface,
    best_play,
    dividend_play,
    hedge_paths,
    optimal_width,
    quote,
    should_exercise,
    theo,
    vega_by_bucket,
    width_profit,
)

SECONDS_PER_YEAR = 252 * 23_400


# ---------------------------------------------------------------- a stale surface
def stale_error(interval_s: float, tau: float, skew: float = -0.10, vol: float = 0.20) -> float:
    """Mean absolute error, in volatility points, of a theo that keeps its strikes' volatilities (sticky strike) for
    `interval_s` seconds while the market's smile moves with the spot (sticky delta): skew ln(S_t/S_fit)/sqrt(tau),
    with ln(S_t/S_fit) ~ N(0, vol^2 interval)."""
    sd = vol * math.sqrt(interval_s / SECONDS_PER_YEAR)
    return 100 * abs(skew) / math.sqrt(tau) * sd * math.sqrt(2 / math.pi)


def stale_table() -> dict:
    return {(dt, tau): stale_error(dt, tau) for dt in (1, 10, 60, 300) for tau in (1 / 12, 0.25)}


# ---------------------------------------------------------------- the width model
# theo error (vol pts), uninformed orders an hour, their width scale (vol pts)
ERR, LAM_U, W_SCALE = 0.50, 20.0, 0.30


@functools.cache
def width_study() -> dict:
    """Profit per hour against the half-width (volatility points), informed flow of 0, 2, 5, 10, 20 orders an hour."""
    grid = np.linspace(0.0, 1.5, 61)
    out = {}
    for lam_i in (0.0, 2.0, 5.0, 10.0, 20.0):
        w_star = optimal_width(ERR, LAM_U, W_SCALE, lam_i)
        out[lam_i] = {"curve": [width_profit(w, ERR, LAM_U, W_SCALE, lam_i) for w in grid], "w_star": w_star,
                      "profit": width_profit(w_star, ERR, LAM_U, W_SCALE, lam_i)}
    out["grid"] = grid
    o1 = Option(100.0, 1 / 12, "C")
    o3 = Option(100.0, 0.25, "C")
    flat = SkewSurface(lambda tau: 0.20)
    out["vega_1m"], out["vega_3m"] = theo(o1, 100.0, 0.0, flat)[1], theo(o3, 100.0, 0.0, flat)[1]
    return out


# ---------------------------------------------------------------- hedging bands
@functools.cache
def hedge_study(n: int = 4000, cost: float = 0.0005) -> dict:
    """A short one-month at-the-money straddle hedged over its life (13 steps a day) on 20% paths: time-based
    re-hedging against bands; mean cost and P&L standard deviation."""
    steps, dt = 21 * 13, 1 / 252 / 13
    rng = np.random.default_rng(1)
    z = rng.standard_normal((n, steps))
    paths = 100 * np.exp(np.cumsum(-0.5 * 0.04 * dt + 0.2 * math.sqrt(dt) * z, axis=1))
    paths = np.column_stack([np.full(n, 100.0), paths])
    book = [Option(100.0, 21 / 252, "C", -1.0), Option(100.0, 21 / 252, "P", -1.0)]
    out = {"time": {}, "band": {}}
    for every in (1, 2, 3, 6, 13, 26):
        r = hedge_paths(paths, book, 0.2, dt, cost, every=every)
        out["time"][every] = (float(r["costs"].mean()), float(r["pnl"].std()), float(r["trades"].mean()))
    for c in (0.25, 0.5, 1.0, 2.0, 4.0):
        r = hedge_paths(paths, book, 0.2, dt, cost, band=c)
        out["band"][c] = (float(r["costs"].mean()), float(r["pnl"].std()), float(r["trades"].mean()))
    return out


# ---------------------------------------------------------------- the dividend play
PUBLIC, DIVIDEND, PUT, TRADE_FEE, EXERCISE_FEE = 10_000, 50.0, 2.0, 0.10, 0.05    # per contract of 100 shares


@functools.cache
def dividend_study() -> dict:
    gain = DIVIDEND - PUT
    out = {"exercise": should_exercise(DIVIDEND, PUT), "gain": gain}
    for fail in (0.1, 0.3, 0.5):
        q, res = best_play(PUBLIC, fail, gain, TRADE_FEE, EXERCISE_FEE)
        curve = [(qq, dividend_play(PUBLIC, fail, qq, gain, TRADE_FEE, EXERCISE_FEE)["net"])
                 for qq in np.linspace(0, 100_000, 51)]
        out[fail] = {"q": q, "res": res, "curve": curve}
    out["no_fee"] = dividend_play(PUBLIC, 0.3, 1e9, gain, 0.0, 0.0)
    return out


# ---------------------------------------------------------------- bucketed limits and a toy market maker
BUCKETS = (Bucket("1m", 0.0, 1.5 / 12, 3000.0), Bucket("3m", 1.5 / 12, 4.5 / 12, 5000.0),
           Bucket("6m", 4.5 / 12, 0.75, 6000.0))
EXPIRIES = (1 / 12, 0.25, 0.5)
STRIKES = (90.0, 95.0, 100.0, 105.0, 110.0)


def true_surf(level: float) -> SkewSurface:
    return SkewSurface(lambda tau, lv=level: lv, -0.10, None)


@functools.cache
def toy_mm(days: int = 20, steps_per_day: int = 13, seed: int = 7, informed: float = 0.2, half_width: float = 0.4,
           limits: bool = True, put_demand: float = 0.65) -> dict:
    """A toy options market maker on 15 series (three expiries, five strikes), 20 days of 13 steps. Every step the true
    surface's level wanders; the market maker's theo sees it with a 0.5-point error; orders of 10 contracts arrive
    (Poisson, 3 a step) on random series; uninformed customers buy puts with probability `put_demand` (and calls with
    probability one half); informed ones trade only when the true value is beyond the quote. The market maker quotes
    theo +- `half_width` volatility points, shaded by its bucket vega against the limits, and hedges its delta every
    step at 5 bp. P&L (dollars, 100 shares a contract) by source: edge (quote against theo), selection (theo against
    true value), hedging cost, inventory (true value change of the book plus the hedge)."""
    rng = np.random.default_rng(seed)
    dt = 1 / 252 / steps_per_day
    s, level, t = 100.0, 0.20, 0.0
    book: dict[tuple[float, float, str], float] = {}
    edge = selection = hedge_cost = inventory = 0.0
    hedge = 0.0
    trades = refused = 0
    vega_path = []

    def options():
        return [Option(k, e, r, q) for (k, e, r), q in book.items() if abs(q) > 0]

    def dollars(v: dict) -> dict:
        return {name: 100 * x for name, x in v.items()}

    for _ in range(days * steps_per_day):
        surf = true_surf(level)
        mm_surf = true_surf(level + 0.01 * ERR * rng.standard_normal())
        buckets = dollars(vega_by_bucket(options(), s, t, mm_surf, BUCKETS))
        for _ in range(rng.poisson(3)):
            k, e, right = STRIKES[rng.integers(5)], EXPIRIES[rng.integers(3)], ("C", "P")[rng.integers(2)]
            o = Option(k, e, right)
            b = next(bb for bb in BUCKETS if bb.lo < e - t <= bb.hi)
            bid, ask = quote(o, s, t, mm_surf, half_width, buckets[b.name] if limits else 0.0, b.limit)
            value, vega = theo(o, s, t, mm_surf)
            true_value = theo(o, s, t, surf)[0]
            if rng.uniform() < informed:
                if true_value > ask:
                    buy = True
                elif true_value < bid:
                    buy = False
                else:
                    continue
            else:
                buy = rng.uniform() < (put_demand if right == "P" else 0.5)
            price = ask if buy else bid
            if math.isnan(price):
                refused += 1
                continue
            qty = -10.0 if buy else 10.0
            book[(k, e, right)] = book.get((k, e, right), 0.0) + qty
            buckets[b.name] += 100 * qty * vega
            edge += 100 * abs(qty) * abs(price - value)
            selection += 100 * qty * (true_value - value)
            trades += 1
        delta = sum(o.qty * greeks(s, o.strike, o.expiry - t, 0.0, 0.0, mm_surf.vol(o.strike, o.expiry - t, s),
                                   o.right)["delta"] for o in options())
        hedge_cost += 100 * 0.0005 * abs(-delta - hedge) * s
        hedge = -delta
        v0 = sum(o.qty * theo(o, s, t, surf)[0] for o in options())
        s_new = s * math.exp(-0.5 * level * level * dt + level * math.sqrt(dt) * rng.standard_normal())
        level_new = max(level + 0.3 * (0.20 - level) * dt + 0.8 * level * math.sqrt(dt) * rng.standard_normal(), 0.05)
        v1 = sum(o.qty * theo(o, s_new, t + dt, true_surf(level_new))[0] for o in options())
        inventory += 100 * (v1 - v0 + hedge * (s_new - s))
        s, level, t = s_new, level_new, t + dt
        vega_path.append(dollars(vega_by_bucket(options(), s, t, true_surf(level), BUCKETS)))
    return {"edge": edge, "selection": selection, "hedge_cost": -hedge_cost, "inventory": inventory,
            "total": edge + selection - hedge_cost + inventory, "trades": trades, "refused": refused,
            "vega_path": vega_path, "final_buckets": vega_path[-1]}


# ---------------------------------------------------------------- exercises 7 and 8
@functools.cache
def play_spread(n: int = 200_000, seed: int = 3) -> dict:
    """Random assignment: the market makers' assigned short calls are hypergeometric (2 q of N + 2 q shorts)."""
    q, res = best_play(PUBLIC, 0.3, DIVIDEND - PUT, TRADE_FEE, EXERCISE_FEE)
    q = round(q)
    shorts, mm = PUBLIC + 2 * q, 2 * q
    exercised = mm + round(0.7 * PUBLIC)
    assigned = np.random.default_rng(seed).hypergeometric(mm, shorts - mm, exercised, size=n)
    net = (DIVIDEND - PUT) * (mm - assigned) - res["cost"]
    p = mm / shorts
    var = exercised * p * (1 - p) * (shorts - exercised) / (shorts - 1)
    return {"q": q, "mean": float(net.mean()), "sd": float(net.std()), "sd_exact": (DIVIDEND - PUT) * math.sqrt(var),
            "p01": float(np.percentile(net, 1))}


@functools.cache
def limits_by_seed(seeds: tuple = tuple(range(1, 21))) -> dict:
    """The toy market maker with and without limit shading over 20 seeds."""
    diff = np.array([toy_mm(seed=s, limits=True)["total"] - toy_mm(seed=s, limits=False)["total"] for s in seeds])
    return {"mean": float(diff.mean()), "sd": float(diff.std()), "se": float(diff.std() / math.sqrt(len(seeds))),
            "positive": int((diff > 0).sum()), "n": len(seeds)}
