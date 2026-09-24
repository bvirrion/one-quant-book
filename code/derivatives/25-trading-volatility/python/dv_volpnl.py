"""Trading volatility (Book 5, Chapter 25): gamma scalping on the right and the wrong days, carry and roll-down, a
risk reversal under sticky strike and sticky delta, a volatility book's daily explain on a stochastic-volatility path,
and ten years of a short-volatility programme."""
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/volpnl"))
sys.path.insert(0, str(ROOT / "code/firm/bs"))
from firm_bs import greeks  # noqa: E402
from firm_volpnl import (  # noqa: E402
    DT,
    Option,
    SkewSurface,
    book_greeks,
    explain,
    gamma_scalp,
    hedged_pnl,
    roll_down,
    value,
)

SIGMA_R, SIGMA_I = 0.25, 0.18
TOTAL_VAR = SIGMA_R ** 2 * 21 * DT


def alternating(n: int, size: float) -> np.ndarray:
    return size * np.array([(-1.0) ** i for i in range(n)])


def scenarios() -> dict:
    """Three 21-day paths with the same realised volatility of 25%: moves spread evenly; three quiet weeks of drift away
    from the strike and a wild last week far from it (the wrong days); three quiet weeks at the strike and a wild last
    week there (the right days)."""
    x = math.sqrt((TOTAL_VAR - 15 * 0.005 ** 2) / 6)
    return {"uniform": alternating(21, SIGMA_R * math.sqrt(DT)),
            "wrong": np.concatenate([np.full(15, 0.005), alternating(6, x)]),
            "right": np.concatenate([alternating(15, 0.005), alternating(6, x)])}


@functools.cache
def scalp() -> dict:
    out = {name: gamma_scalp(r, vol=SIGMA_I) for name, r in scenarios().items()}
    w = scenarios()["wrong"]
    daily = out["wrong"]["daily"]
    out["wrong_split"] = {"quiet": float(daily[:15].sum()), "wild": float(daily[15:].sum()),
                          "move": float(math.sqrt((TOTAL_VAR - 15 * 0.005 ** 2) / 6)),
                          "quiet_vol": 0.005 * math.sqrt(252), "wild_vol": float(abs(w[-1]) * math.sqrt(252))}
    return out


# ---------------------------------------------------------------- carry and roll-down
def atm_term(tau: float) -> float:
    """An upward-sloping term structure of at-the-money volatility."""
    return 0.24 - 0.06 * math.exp(-tau / 0.25)


@functools.cache
def carry() -> dict:
    """A long three-month straddle held one month with spot and the term structure unchanged; and a calendar
    (long three months, short one month) per unit of vega."""
    surf = SkewSurface(atm_term)
    book = [Option(100.0, 0.25, "C"), Option(100.0, 0.25, "P")]
    v0 = value(book, 100.0, 0.0, surf)
    v1 = value(book, 100.0, 1 / 12, surf)
    v1_flat = value(book, 100.0, 1 / 12, SkewSurface(lambda tau: atm_term(0.25)))
    rd = roll_down(atm_term, 0.25, 1 / 12)
    one_day = value(book, 100.0, DT, surf) - v0
    theta_day = book_greeks(book, 100.0, 0.0, surf)["theta"] * DT
    vega = book_greeks(book, 100.0, 0.0, surf)["vega"]
    short = [Option(100.0, 1 / 12, "C", -1), Option(100.0, 1 / 12, "P", -1)]
    ratio = vega / book_greeks(short, 100.0, 0.0, surf)["vega"] * -1
    cal = book + [Option(o.strike, o.expiry, o.right, o.qty * ratio) for o in short]
    cal_day = value(cal, 100.0, DT, surf) - value(cal, 100.0, 0.0, surf)
    return {"v0": v0, "v1": v1, "carry": v1 - v0, "theta_only": v1_flat - v0, "roll": v1 - v1_flat, "roll_down": rd,
            "vols": (atm_term(1 / 12), atm_term(2 / 12), atm_term(0.25), atm_term(1.0)), "one_day": one_day,
            "theta_day": theta_day, "vega": vega, "ratio": ratio, "cal_day": cal_day,
            "cal_gamma": book_greeks(cal, 100.0, 0.0, surf)["gamma"]}


# ---------------------------------------------------------------- skew trade
def strike_for_delta(delta: float, tau: float, surf: SkewSurface, right: str) -> float:
    lo, hi = 50.0, 200.0
    for _ in range(100):
        k = 0.5 * (lo + hi)
        d = greeks(100.0, k, tau, 0.0, 0.0, surf.vol(k, tau, 100.0), right)["delta"]
        if d > delta:
            lo = k
        else:
            hi = k
    return k


@functools.cache
def risk_reversal() -> dict:
    """Short a 25-delta put, long a 25-delta call, three months, delta-hedged; spot falls 5% in a day with the
    at-the-money level unchanged, marked sticky strike and sticky delta."""
    atm = SkewSurface(lambda tau: 0.20, -0.10, 100.0)
    kp, kc = strike_for_delta(-0.25, 0.25, atm, "P"), strike_for_delta(0.25, 0.25, atm, "C")
    book = [Option(kp, 0.25, "P", -1.0), Option(kc, 0.25, "C", 1.0)]
    out = {"kp": kp, "kc": kc, "vol_p": atm.vol(kp, 0.25, 100.0), "vol_c": atm.vol(kc, 0.25, 100.0)}
    for name, ref in (("sticky_strike", 100.0), ("sticky_delta", None)):
        surf = SkewSurface(lambda tau: 0.20, -0.10, ref)
        hedge = -book_greeks(book, 100.0, 0.0, surf)["delta"]
        out[name] = explain(book, 100.0, 95.0, 0.0, DT, surf, surf, hedge)
        out[name + "_hedge"] = hedge
    return out


# ---------------------------------------------------------------- a volatility book's explain on a Heston path
def heston_day_path(days: int, seed: int, v0=0.04, kappa=3.0, vbar=0.04, eta=0.5, rho=-0.7, lam=0.0, mu=0.0,
                    delta=0.0) -> tuple[np.ndarray, np.ndarray]:
    """One daily path of spot and variance (full-truncation Euler, optional Merton jumps), s0 = 100."""
    rng = np.random.default_rng(seed)
    s, v = [100.0], [v0]
    kbar = math.exp(mu + 0.5 * delta ** 2) - 1
    for _ in range(days):
        z1, z2 = rng.standard_normal(2)
        vp = max(v[-1], 0.0)
        jump = 0.0
        if lam > 0 and rng.uniform() < lam * DT:
            jump = mu + delta * rng.standard_normal()
        x = (-0.5 * vp - lam * kbar) * DT + math.sqrt(vp * DT) * z1 + jump
        s.append(s[-1] * math.exp(x))
        z_v = rho * z1 + math.sqrt(1 - rho * rho) * z2
        v.append(v[-1] + kappa * (vbar - vp) * DT + eta * math.sqrt(vp * DT) * z_v)
    return np.array(s), np.maximum(np.array(v), 0.0)


@functools.cache
def book_explain(days: int = 63, seed: int = 3) -> dict:
    """Long a three-month at-the-money straddle and short two three-month 90 puts, delta-hedged daily for 63 days;
    the market's surface is the term structure shifted by the instantaneous volatility's move, skew -0.1."""
    s, v = heston_day_path(days, seed)
    book = [Option(100.0, 0.30, "C"), Option(100.0, 0.30, "P"), Option(90.0, 0.30, "P", -2.0)]
    out = {"spot": s, "vol": np.sqrt(v)}
    for name, ref in (("sticky_strike", 100.0), ("sticky_delta", None)):
        surfs = [SkewSurface(atm_term, -0.10, ref).shifted(float(np.sqrt(x)) - 0.2) for x in v]
        out[name] = hedged_pnl(s, book, surfs)
    return out


# ---------------------------------------------------------------- the short-volatility programme
@functools.cache
def short_vol(years: int = 10, premium: float = 0.02, seed: int = 5) -> dict:
    """Sell a one-month at-the-money straddle every 21 days at the current volatility plus `premium`, delta-hedge
    daily at that volatility, on a Heston path with Merton crashes; P&L per month in % of the spot at sale."""
    n = 21 * 12 * years
    s, v = heston_day_path(n, seed, lam=1.0, mu=-0.06, delta=0.04)
    pnl, realised, implied = [], [], []
    t = 21 * DT
    for m in range(0, n, 21):
        mean_var = 0.04 + (v[m] - 0.04) * (1 - math.exp(-3.0 * t)) / (3.0 * t)     # E[realised variance], diffusion
        vol = math.sqrt(mean_var + 1.0 * (0.06 ** 2 + 0.04 ** 2)) + premium          # plus the jumps' variance
        g = gamma_scalp(np.diff(np.log(s[m:m + 22])), strike=s[m], vol=vol, s0=s[m])
        pnl.append(-100 * float(g["daily"].sum()) / s[m])
        realised.append(g["realised"])
        implied.append(vol)
    pnl = np.array(pnl)
    return {"pnl": pnl, "mean": float(pnl.mean()), "sd": float(pnl.std()), "worst": float(pnl.min()),
            "best": float(pnl.max()), "hit": float((pnl > 0).mean()),
            "sharpe": float(pnl.mean() / pnl.std() * math.sqrt(12)),
            "skew": float(((pnl - pnl.mean()) ** 3).mean() / pnl.std() ** 3),
            "realised": np.array(realised), "implied": np.array(implied)}
