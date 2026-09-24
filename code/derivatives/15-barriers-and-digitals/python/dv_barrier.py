"""Barriers and digitals (Book 5, Chapter 15): the digital at the close, the smile's effect on digitals, the
call-spread overhedge, barrier closed forms against discrete monitoring, a barrier under chapter 9's local
volatility, static hedges and their failure under skew, and the gap at the barrier."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "localvol", "barrier"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
sys.path.insert(0, str(ROOT / "code/derivatives/09-local-volatility/python"))
from dv_localvol import grid as lv_grid  # noqa: E402
from firm_barrier import (  # noqa: E402
    barrier,
    bgk_shift,
    calendar_hedge,
    calendar_hedge_on_barrier,
    digital,
    digital_delta,
    digital_smile,
    double_no_touch,
    mc_barrier,
    no_touch,
    one_touch,
    symmetry_down_in_call,
)
from firm_bs import bs, greeks  # noqa: E402
from firm_svi import ssvi  # noqa: E402

# ---------------------------------------------------------------- the digital at the close
INDEX, NOTIONAL = 5000.0, 10_000_000.0
MINUTE = 1 / (252 * 6.5 * 60)                     # one trading minute, in years


def hook(spot: float = 4999.9, vol: float = 0.20) -> dict:
    d = NOTIONAL * digital_delta(spot, INDEX, MINUTE, 0.0, 0.0, vol)       # per index point
    return {"per_point": d, "index_notional": d * spot, "value": NOTIONAL * digital(spot, INDEX, MINUTE, 0, 0, vol)}


def delta_curves(vol: float = 0.20):
    spots = np.linspace(4900.0, 5100.0, 201)
    out = {}
    for name, t in (("week", 1 / 52), ("day", 1 / 252), ("hour", 1 / (252 * 6.5))):
        out[name] = np.array([NOTIONAL * digital_delta(x, INDEX, t, 0.0, 0.0, vol) for x in spots]) / 1e6
    return spots, out


# ---------------------------------------------------------------- the smile and the overhedge
T_DIG = 0.25


def market_vol(strike: float, t: float = T_DIG) -> float:
    """Chapter 9's surface, scaled to an index at 5000 (strike 5000 = 100 on the original)."""
    theta = (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t
    return math.sqrt(float(ssvi(math.log(strike / INDEX), theta, -0.6, 1.0, 0.45)) / t)


def digital_prices() -> dict:
    atm = market_vol(INDEX)
    flat = NOTIONAL * digital(INDEX, INDEX, T_DIG, 0.0, 0.0, atm)
    smile = NOTIONAL * digital_smile(INDEX, INDEX, T_DIG, 0.0, 0.0, market_vol)
    g = greeks(INDEX, INDEX, T_DIG, 0.0, 0.0, atm, "C")
    h = 1.0
    slope = (market_vol(INDEX + h) - market_vol(INDEX - h)) / (2 * h)
    return {"atm": atm, "flat": flat, "smile": smile, "vega_term": -NOTIONAL * g["vega"] * slope}


def overhedge(width: float) -> dict:
    """Price of notional / width call spreads struck at (5000 - width, 5000), and its excess over the digital."""
    lo, hi = INDEX - width, INDEX
    spread = NOTIONAL / width * (bs(INDEX, lo, T_DIG, 0, 0, market_vol(lo), "C")
                                 - bs(INDEX, hi, T_DIG, 0, 0, market_vol(hi), "C"))
    dig = NOTIONAL * digital_smile(INDEX, INDEX, T_DIG, 0.0, 0.0, market_vol)
    return {"width": width, "per_point": NOTIONAL / width, "spread": spread, "cost": spread - dig}


def width_for_loss_cap(cap_per_point: float = 50_000.0) -> float:
    """The width at which a one-point error in the settlement print moves the call spread by at most the cap."""
    return NOTIONAL / cap_per_point


def payoff_curves(width: float = 200.0):
    s = np.linspace(4600.0, 5200.0, 601)
    dig = NOTIONAL * (s >= INDEX)
    spread = NOTIONAL / width * (np.maximum(s - (INDEX - width), 0) - np.maximum(s - INDEX, 0))
    return s, dig / 1e6, spread / 1e6


# ---------------------------------------------------------------- barriers
S, K, R, Q, VOL, T = 100.0, 100.0, 0.03, 0.01, 0.20, 1.0


def barrier_table() -> dict:
    out = {"call": bs(S, K, T, R, Q, VOL, "C"),
           "doc": barrier(S, K, 90.0, T, R, Q, VOL, "down-out", "C"),
           "dic": barrier(S, K, 90.0, T, R, Q, VOL, "down-in", "C"),
           "doc_rebate": barrier(S, K, 90.0, T, R, Q, VOL, "down-out", "C", rebate=2.0),
           "uoc": barrier(S, K, 130.0, T, R, Q, VOL, "up-out", "C"),
           "one_touch_hit": one_touch(S, 90.0, T, R, Q, VOL, True),
           "one_touch_exp": one_touch(S, 90.0, T, R, Q, VOL, False),
           "no_touch": no_touch(S, 90.0, T, R, Q, VOL),
           "dnt": double_no_touch(S, 85.0, 115.0, T, R, Q, VOL)}
    return out


def barrier_curves():
    spots = np.linspace(88.0, 130.0, 85)
    rows = []
    for x in spots:
        call = bs(x, K, T, R, Q, VOL, "C")
        if x > 90:
            rows.append((x, call, barrier(x, K, 90.0, T, R, Q, VOL, "down-out", "C"),
                         barrier(x, K, 90.0, T, R, Q, VOL, "down-in", "C")))
        else:
            rows.append((x, call, 0.0, call))
    return rows


def monitoring(h: float = 90.0, kind: str = "down-out", counts=(4, 12, 52, 252)) -> list[dict]:
    cont = barrier(S, K, h, T, R, Q, VOL, kind, "C")
    rows = []
    for n in counts:
        mc, se = mc_barrier(S, K, h, T, R, Q, VOL, kind, "C", n)
        shifted = barrier(S, K, bgk_shift(h, S, VOL, T / n), T, R, Q, VOL, kind, "C")
        rows.append({"n": n, "mc": mc, "se": se, "shifted": shifted, "cont": cont})
    return rows


def local_vol_doc(h: float = 90.0, steps: int = 252, n: int = 100_000, seed: int = 15) -> dict:
    """Down-and-out call (strike 100, barrier 90, one year, daily monitoring) under chapter 9's local volatility
    (zero rates), against Black-Scholes at the at-the-money and at the strike's implied volatility with the
    barrier shift."""
    g = lv_grid()
    rng = np.random.default_rng(seed)
    dt = 1.0 / steps
    x = np.full(n, math.log(100.0))
    alive = np.ones(n, bool)
    for i in range(steps):
        z = rng.standard_normal(n // 2)
        z = np.concatenate([z, -z])
        sig = g.sigma((i + 0.5) * dt, np.exp(x))
        x = x - 0.5 * sig * sig * dt + sig * math.sqrt(dt) * z
        alive &= np.exp(x) > h
    pay = np.maximum(np.exp(x) - 100.0, 0.0) * alive
    vanilla = np.maximum(np.exp(x) - 100.0, 0.0)
    theta = (0.20 - 0.06 * math.exp(-1.0 / 0.5)) ** 2
    atm = math.sqrt(float(ssvi(0.0, theta, -0.6, 1.0, 0.45)))
    hb = bgk_shift(h, 100.0, atm, dt)
    return {"lv": float(pay.mean()), "se": float(pay.std() / math.sqrt(n)), "lv_vanilla": float(vanilla.mean()),
            "bs_atm": barrier(100.0, 100.0, hb, 1.0, 0.0, 0.0, atm, "down-out", "C"), "atm": atm}


# ---------------------------------------------------------------- static hedges
def symmetry_example() -> dict:
    """Down-and-in call, strike 100, barrier 90, one year, zero carry, 20% flat: the symmetry hedge, and what the
    skew does to it at a hit with half a year left (chapter 9's smile, sticky moneyness)."""
    price = symmetry_down_in_call(100.0, 90.0, 100.0, 1.0, 0.20)
    closed = barrier(100.0, 100.0, 90.0, 1.0, 0.0, 0.0, 0.20, "down-in", "C")
    tau = 0.5
    theta = (0.20 - 0.06 * math.exp(-tau / 0.5)) ** 2 * tau

    def vol(k):
        return math.sqrt(float(ssvi(k, theta, -0.6, 1.0, 0.45)) / tau)
    put_k = 90.0 * 90.0 / 100.0
    puts = 100.0 / 90.0 * bs(90.0, put_k, tau, 0, 0, vol(math.log(put_k / 90.0)), "P")
    call = bs(90.0, 100.0, tau, 0, 0, vol(math.log(100.0 / 90.0)), "C")
    return {"puts_strike": put_k, "ratio": 100 / 90, "price": price, "closed": closed, "hit_puts": puts,
            "hit_call": call, "mismatch": puts - call}


def calendar_example(ns=(2, 4, 8, 16, 32, 64)) -> dict:
    k, h, t, vol = 100.0, 120.0, 1.0, 0.20
    uoc = barrier(100.0, k, h, t, 0.0, 0.0, vol, "up-out", "C")
    prices = {n: calendar_hedge(100.0, k, h, t, 0.0, 0.0, vol, n)[1] for n in ns}
    times = np.linspace(0.0, 0.999, 400)
    paths = {n: calendar_hedge_on_barrier(calendar_hedge(100.0, k, h, t, 0.0, 0.0, vol, n)[0], h, 0, 0, vol, times)
             for n in (4, 16)}
    return {"uoc": uoc, "prices": prices, "times": times, "on_barrier": paths}


# ---------------------------------------------------------------- the gap
def reverse_barrier(t: float = 1 / 12) -> dict:
    """Up-and-out call, strike 100, barrier 120, one month left, 20% flat, zero carry: value and delta by spot,
    and the hedger's P&L if the price gaps from 119 to 125."""
    spots = np.linspace(95.0, 119.9, 100)
    val = np.array([barrier(x, 100.0, 120.0, t, 0, 0, 0.2, "up-out", "C") for x in spots])
    h = 1e-3
    dl = np.array([(barrier(x + h, 100.0, 120.0, t, 0, 0, 0.2, "up-out", "C")
                    - barrier(x - h, 100.0, 120.0, t, 0, 0, 0.2, "up-out", "C")) / (2 * h) for x in spots])
    v119 = barrier(119.0, 100.0, 120.0, t, 0, 0, 0.2, "up-out", "C")
    d119 = (barrier(119.0 + h, 100.0, 120.0, t, 0, 0, 0.2, "up-out", "C")
            - barrier(119.0 - h, 100.0, 120.0, t, 0, 0, 0.2, "up-out", "C")) / (2 * h)
    # the seller is short the option and holds d119 shares (negative: short shares); a gap to 125 kills the option
    pnl_gap = v119 + d119 * (125.0 - 119.0)
    pnl_small = -(barrier(119.5, 100.0, 120.0, t, 0, 0, 0.2, "up-out", "C") - v119) + d119 * 0.5
    return {"spots": spots, "value": val, "delta": dl, "v119": v119, "d119": d119, "pnl_gap": pnl_gap,
            "pnl_small": pnl_small}
