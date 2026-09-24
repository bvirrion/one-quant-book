"""Managing an exotic book (Book 5, Chapter 27): a three-year worst-of autocallable sold at a 2 % margin, its bid-offer,
model and parameter reserves, the day-one P&L split and its release, and a stress grid."""
import functools
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("autocall", "reserves"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_autocall import TermSheet, cashflows, simulate  # noqa: E402
from firm_reserves import (  # noqa: E402
    aggregate,
    bid_offer_reserve,
    concentration_days,
    day_one,
    model_reserve,
    parameter_reserve,
    prudent_point,
    release_schedule,
    stress_grid,
)

VOLS, R, Q, RHO = (0.20, 0.25), 0.03, 0.02, 0.5
NOTIONAL = 100e6                      # the notes sold; values are per 100 of notional
PER_100 = NOTIONAL / 100
N_PATHS = 200_000


def note_value(coupon: float, rho: float = RHO, vols=VOLS, spots=(1.0, 1.0), obs=(1.0, 2.0, 3.0),
               mixture: float = 0.0, seed: int = 27) -> float:
    """Value per 100 of a worst-of Phoenix autocallable on two indices (annual observations, autocall at 100 %,
    coupon barrier 70 % with memory, protection 60 % at maturity), from `spots` (performances against the initial
    fixing) with observation times `obs` from now. With mixture = m, half the paths run at vols x (1 - m) and
    half at vols x (1 + m) (an uncertain-volatility model). Lognormal, annual steps (exact), common random numbers."""
    ts = TermSheet(obs_times=tuple(obs), trigger=1.0, coupon=coupon, coupon_barrier=0.7, memory=True, protection=0.6)
    corr = [[1.0, rho], [rho, 1.0]]
    parts = [(1.0, 1.0)] if mixture == 0.0 else [(0.5, 1 - mixture), (0.5, 1 + mixture)]
    total = 0.0
    for weight, scale in parts:
        fns = [lambda t, s, v=v * scale: np.full_like(s, v) for v in vols]
        times, perf = simulate(fns, np.ones(2), obs[-1], R, Q, N_PATHS, seed, steps_per_year=1, corr=corr)
        perf = perf * np.asarray(spots)[None, None, :]
        total += weight * float(cashflows(ts, times, perf, R)["pv"].mean())
    return total


@functools.cache
def fair_coupon(target: float = 98.0) -> float:
    lo, hi = 0.0, 20.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        if note_value(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def model_set(coupon: float, spots=(1.0, 1.0), obs=(1.0, 2.0, 3.0)) -> dict[str, float]:
    """The note's value under four models: flat at-the-money volatilities (booked), flat volatilities at the knock-in
    strike (three points higher: the skew), flat volatilities at the autocall trigger's forward strike (half a point
    lower), and uncertain volatility (+-20 %)."""
    return {"flat ATM": note_value(coupon, spots=spots, obs=obs),
            "flat at the knock-in strike": note_value(coupon, vols=(0.23, 0.28), spots=spots, obs=obs),
            "flat at the trigger": note_value(coupon, vols=(0.195, 0.245), spots=spots, obs=obs),
            "uncertain volatility": note_value(coupon, spots=spots, obs=obs, mixture=0.2)}


@functools.cache
def reserves_at(when: int, level: float = 0.95, lo_hi: tuple | None = None) -> dict:
    """Reserves on the note (as a liability of the firm, per 100) at inception (when = 0) or after one or two years with
    both indices at 95 % and the note alive; correlation plausible in [0.35, 0.65] at inception and observable within
    [0.47, 0.53] afterwards."""
    c = fair_coupon()
    spots = (1.0, 1.0) if when == 0 else (level, level)
    obs = tuple(float(x) for x in range(1, 4 - when))
    lo, hi = lo_hi if lo_hi is not None else ((0.35, 0.65) if when == 0 else (0.47, 0.53))
    book = {name: -v for name, v in model_set(c, spots, obs).items()}          # the firm is short the note
    mr = model_reserve(book, "flat ATM")
    pr = parameter_reserve(lambda rho: -note_value(c, rho=rho, spots=spots, obs=obs), RHO, lo, hi, n=13)
    # sensitivities for the bid-offer reserve: vega per volatility point per index, delta per 1 % per index
    base = note_value(c, spots=spots, obs=obs)
    vega = [(note_value(c, vols=tuple(v + 0.01 * (i == j) for j, v in enumerate(VOLS)), spots=spots, obs=obs) - base)
            for i in range(2)]
    delta = [(note_value(c, spots=tuple(s * (1 + 0.01 * (i == j)) for j, s in enumerate(spots)), obs=obs) - base)
             for i in range(2)]
    bo = bid_offer_reserve({"vega 1": vega[0], "vega 2": vega[1], "delta 1": delta[0], "delta 2": delta[1]},
                           {"vega 1": 0.5, "vega 2": 0.5, "delta 1": 0.02, "delta 2": 0.02})
    return {"coupon": c, "value": base, "models": book, "model_reserve": mr, "param": pr, "bid_offer": bo,
            "vega": vega, "delta": delta, "unobservable": mr + pr["reserve"]}


@functools.cache
def day_one_study() -> dict:
    r0 = reserves_at(0)
    d = day_one(100.0, r0["value"], r0["bid_offer"]["total"], r0["unobservable"])
    r1, r2 = reserves_at(1), reserves_at(2)
    sched = release_schedule([(0.0, r0["unobservable"]), (1.0, r1["unobservable"]), (2.0, r2["unobservable"]),
                              (3.0, 0.0)])
    return {"day_one": d, "schedule": sched, "r0": r0, "r1": r1, "r2": r2,
            "aggregated": aggregate([r0["bid_offer"]["total"], r0["model_reserve"], r0["param"]["reserve"]])}


@functools.cache
def rho_curve() -> list[tuple[float, float]]:
    c = fair_coupon()
    return [(rho, note_value(c, rho=rho)) for rho in np.linspace(0.2, 0.8, 13)]


@functools.cache
def stress() -> dict:
    """The note's P&L to the firm (short, per 100, delta-hedged at inception) under joint shocks to both indices
    and to both volatilities."""
    c = fair_coupon()
    base = note_value(c)
    d_up = note_value(c, spots=(1.01, 1.01)) - base                       # value change for +1 % on both indices
    hedge = 100 * d_up                                                    # per unit relative shock, long the indices

    def value_of(ds, dv):
        return -note_value(c, vols=(VOLS[0] + dv, VOLS[1] + dv), spots=(1 + ds, 1 + ds))
    shocks, vols = (-0.3, -0.2, -0.1, 0.0, 0.1), (-0.05, 0.0, 0.05)
    grid = stress_grid(value_of, shocks, vols, hedge_delta=hedge)
    return {"shocks": shocks, "vols": vols, "grid": grid, "hedge": hedge}


def concentration() -> float:
    """Days to exit the note's index-2 vega at 10 % of an assumed market volume of 100,000 per point a day."""
    vega2 = reserves_at(0)["vega"][1] * PER_100                            # currency per volatility point
    return concentration_days(vega2, 100_000.0, participation=0.1)


def prudent_check() -> float:
    return prudent_point([1.0, 2.0, 3.0], 0.9)


@functools.cache
def exercises() -> dict:
    """Exercise 7 (a wider correlation range) and question 14 (indices at 80 % after one year)."""
    r0, wide = reserves_at(0), reserves_at(0, lo_hi=(0.2, 0.8))
    d_wide = day_one(100.0, r0["value"], r0["bid_offer"]["total"], r0["model_reserve"] + wide["param"]["reserve"])
    low = reserves_at(1, level=0.80)
    return {"wide": wide["param"], "d_wide": d_wide, "low": low,
            "release_low": r0["unobservable"] - low["unobservable"]}
