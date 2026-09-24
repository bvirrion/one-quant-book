"""Parametrising the surface: SVI fitted to bid and ask, SSVI, wings, events and business time
(Book 5, Chapter 8)."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "volsurface"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_svi import event_variance, fit_ssvi, fit_svi, implied_move, ssvi, ssvi_check, svi, svi_check  # noqa: E402
from firm_volsurface import _natural_spline, _spline_eval  # noqa: E402

T3 = 91 / 365
KS = np.round(np.linspace(-0.40, 0.25, 27), 4)


def theta(t: float) -> float:
    """At-the-money total variance of the synthetic market."""
    return (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t


def rho_t(t: float) -> float:
    """Spot-vol correlation of each slice: more negative for short expiries, so that no single-rho
    surface fits every slice exactly."""
    return -0.55 - 0.25 * math.exp(-t / 0.25)


def true_vol(k, t):
    """The 'market' behind the synthetic quotes: each slice is an SSVI smile with its own rho."""
    return math.sqrt(float(ssvi(k, theta(t), rho_t(t), 1.2, 0.45)) / t)


def quotes(t: float = T3, seed: int = 3):
    """Bid and ask volatilities: half-width 0.2 point at the money widening to 1 point at k = -0.4,
    mids off the true smile by up to 0.15 point."""
    rng = np.random.default_rng(seed)
    mid = np.array([true_vol(k, t) for k in KS]) + 0.0015 * rng.uniform(-1, 1, len(KS))
    half = 0.002 + 0.02 * KS ** 2 / 0.16 * 0.4
    return mid - half, mid, mid + half


def fit_slice(t: float = T3, seed: int = 3):
    bid, mid, ask = quotes(t, seed)
    w = lambda v: v * v * t  # noqa: E731
    wts = 1.0 / (ask - bid) ** 2
    p, rmse = fit_svi(KS, w(mid), w(bid), w(ask), wts)
    fitted = np.sqrt(svi(KS, *p) / t)
    inside = int(np.sum((fitted >= bid - 1e-12) & (fitted <= ask + 1e-12)))
    return {"params": p, "rmse_w": rmse, "inside": inside, "n": len(KS), "check": svi_check(*p),
            "max_err_pts": float(np.max(np.abs(fitted - mid)) * 100), "wing_left": p[1] * (1 - p[2]),
            "wing_right": p[1] * (1 + p[2]), "bid": bid, "mid": mid, "ask": ask, "fitted": fitted}


def spline_through_mids(t: float = T3, seed: int = 3, grid=None):
    """Not-a-knot spline through the mid total variances: exact at the quotes, noisy between."""
    _, mid, _ = quotes(t, seed)
    y = mid * mid * t
    m = _natural_spline(KS, y)
    grid = np.linspace(KS[0], KS[-1], 131) if grid is None else grid
    return grid, np.array([math.sqrt(_spline_eval(KS, y, m, g)[0] / t) for g in grid])


TENORS = (30, 91, 182, 365, 730)


def ssvi_fit():
    slices = []
    for d in TENORS:
        t = d / 365
        _, mid, _ = quotes(t, seed=d)
        w = mid * mid * t
        slices.append((KS, w, theta(t)))
    p, rmse = fit_ssvi(slices)
    return {"params": p, "rmse_w": rmse, "check": ssvi_check([s[2] for s in slices], *p),
            "thetas": [s[2] for s in slices], "rmse_vol_pts": [
                float(np.sqrt(np.mean((np.sqrt(ssvi(k, th, *p) / (d / 365)) - np.sqrt(w / (d / 365))) ** 2)) * 100)
                for (k, w, th), d in zip(slices, TENORS, strict=True)]}


# ---------------------------------------------------------------- events and business time
EARN = {"base": 0.32, "event_sd": 0.08, "day": 7}          # earnings after the close of day 7
EXPIRIES = (4, 11, 18, 25)                                  # days to expiry


def earnings_vols():
    """At-the-money implied volatility of each expiry: diffusive variance at the base rate, plus the
    event variance for expiries after the announcement."""
    out = []
    for d in EXPIRIES:
        t = d / 365
        w = EARN["base"] ** 2 * t + (EARN["event_sd"] ** 2 if d > EARN["day"] else 0.0)
        out.append((d, math.sqrt(w / t)))
    return out


def earnings_problem() -> dict[str, float]:
    vols = dict(earnings_vols())
    q = {d: round(v, 3) for d, v in vols.items()}          # quotes as a screen shows them (0.1 point)
    t4, t11 = 4 / 365, 11 / 365
    ev = event_variance(q[4] ** 2 * t4, t4, q[11] ** 2 * t11, t11)
    sd, absmove = implied_move(ev)
    t18 = 18 / 365
    ex_vol_18 = math.sqrt((q[18] ** 2 * t18 - ev) / t18)
    return {"q4": q[4], "q11": q[11], "q18": q[18], "q25": q[25], "event_var": ev, "sd": sd, "abs_move": absmove,
            "ex_vol_18": ex_vol_18, "w4": q[4] ** 2 * t4, "w11": q[11] ** 2 * t11,
            "day_after": math.sqrt((q[11] ** 2 * t11 - ev) / t11)}


def business_time(vol_b: float = 0.20, trading_days: int = 5, calendar_days: int = 7) -> dict[str, float]:
    """A vol quoted on a 252-trading-day clock, converted to the calendar clock (365 days) that prices the
    same option, and the share of a week's variance that elapses over a weekend on each clock."""
    w = vol_b ** 2 * trading_days / 252
    vol_c = math.sqrt(w / (calendar_days / 365))
    return {"vol_c": vol_c, "ratio": vol_c / vol_b, "weekend_share_calendar": 2 / 7, "weekend_share_business": 0.0}
