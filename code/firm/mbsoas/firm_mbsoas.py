"""Path-wise prepayment model and option-adjusted spread (build of One Quant Book 6, chapter 12).

Monthly Hull-White short-rate paths (chapter 7's Gaussian form, simulated exactly enough at monthly
steps) drive a mortgage rate (the ten-year par rate on the path plus a spread); a prepayment model
turns each path into a pool's cash flows:
  CPR = turnover(age) + refi_S_curve(WAC - mortgage rate) * burnout,
  burnout = exp(-lambda * cumulative positive incentive, in percentage-point years),
with Book 2's pass-through mechanics (`firm_prepay`, imported). Cash flows are discounted along each
path at the short rate plus a constant spread; the OAS makes the average equal the market price.
Interest-only and principal-only strips split the same flows. Common random numbers throughout.
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "prepay"))
from firm_prepay import level_payment, psa_cpr  # noqa: E402


def _B(k: float, tau: float) -> float:
    return (1 - math.exp(-k * tau)) / k


@dataclass
class Pool:
    balance: float = 100.0
    wac: float = 0.060          # borrowers' rate
    coupon: float = 0.055       # pass-through coupon to investors
    term: int = 360             # months
    age: int = 12               # months already paid


@dataclass
class PrepayModel:
    turnover_speed: float = 1.0     # PSA multiple for the housing-turnover part
    refi_top: float = 0.45          # maximum refinancing CPR
    refi_slope: float = 200.0       # steepness of the S-curve (per unit of incentive)
    refi_centre: float = 0.0075     # incentive at the middle of the S-curve
    burnout: float = 0.25           # decay per percentage-point year of past positive incentive
    mortgage_spread: float = 0.0175  # mortgage rate over the ten-year par rate

    def refi(self, incentive):
        return self.refi_top / (1.0 + np.exp(-self.refi_slope * (incentive - self.refi_centre)))

    def cpr(self, age: int, incentive, cum):
        return np.minimum(psa_cpr(age, self.turnover_speed) + self.refi(incentive) * np.exp(-self.burnout * cum), 0.95)


def simulate_paths(curve, kappa: float, sigma: float, months: int, paths: int, seed: int = 17, shift: float = 0.0):
    """Short rate r (paths x months, rate for each month) and ten-year par rate at each month start,
    in Hull-White on `curve` shifted in parallel by `shift` (zero rates)."""
    rng = np.random.default_rng(seed)
    dt = 1.0 / 12
    half = paths // 2
    df = [curve.df_t(k * dt) * math.exp(-shift * k * dt) for k in range(months + 121)]
    x = np.zeros(2 * half)
    rs, par10 = np.empty((2 * half, months)), np.empty((2 * half, months))
    ann_b = [_B(kappa, float(i)) for i in range(1, 11)]
    for k in range(months):
        t = k * dt
        yt = sigma * sigma * (1 - math.exp(-2 * kappa * t)) / (2 * kappa)
        bonds = [df[k + 12 * i] / df[k] * np.exp(-b * x - 0.5 * b * b * yt) for i, b in enumerate(ann_b, 1)]
        par10[:, k] = (1.0 - bonds[-1]) / sum(bonds)
        f0 = -math.log(df[k + 1] / df[k]) / dt
        rs[:, k] = f0 + x
        z = rng.standard_normal(half)
        x = x + (yt - kappa * x) * dt + sigma * math.sqrt(dt) * np.concatenate([z, -z])
    return rs, par10


def pool_flows(pool: Pool, model: PrepayModel, par10: np.ndarray):
    """Interest and principal to investors (paths x months)."""
    n, months = par10.shape
    bal = np.full(n, pool.balance)
    cum = np.zeros(n)
    interest, principal = np.zeros((n, months)), np.zeros((n, months))
    r = pool.wac / 12.0
    for k in range(months):
        age = pool.age + k + 1
        remaining = pool.term - pool.age - k
        if remaining <= 0:
            break
        incentive = pool.wac - (par10[:, k] + model.mortgage_spread)
        pay = level_payment(1.0, r, remaining) * bal
        sched = pay - bal * r
        pre = (bal - sched) * smm_vec(model.cpr(age, incentive, cum))
        interest[:, k] = bal * pool.coupon / 12.0
        principal[:, k] = sched + pre
        bal = bal - sched - pre
        cum += np.maximum(incentive, 0.0) * 100.0 / 12.0
    return interest, principal


def smm_vec(cpr):
    return 1.0 - (1.0 - cpr) ** (1.0 / 12.0)


def pv_paths(flows: np.ndarray, rs: np.ndarray, oas: float) -> np.ndarray:
    """Present value per path of monthly flows paid at month ends, discounted at r + oas."""
    disc = np.exp(-np.cumsum((rs + oas) / 12.0, axis=1))
    return (flows * disc).sum(axis=1)


def solve_oas(price: float, flows: np.ndarray, rs: np.ndarray) -> float:
    lo, hi = -0.05, 0.10
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if pv_paths(flows, rs, mid).mean() > price else (lo, mid)
    return 0.5 * (lo + hi)


def analyse(curve, pool: Pool, model: PrepayModel, price: float, kappa: float = 0.03, sigma: float = 0.009,
            paths: int = 4000, seed: int = 17, dy: float = 0.0025) -> dict:
    months = pool.term - pool.age
    rs, p10 = simulate_paths(curve, kappa, sigma, months, paths, seed)
    io, po = pool_flows(pool, model, p10)
    oas = solve_oas(price, io + po, rs)
    rs0, p0 = simulate_paths(curve, kappa, 1e-7, months, 2, seed)            # zero-volatility path
    io0, po0 = pool_flows(pool, model, p0)
    zvo = solve_oas(price, io0[:1] + po0[:1], rs0[:1])
    out = {"oas": oas, "zv_spread": zvo, "option_cost": zvo - oas,
           "io": pv_paths(io, rs, oas).mean(), "po": pv_paths(po, rs, oas).mean()}
    vals = {}
    for s in (-dy, dy):
        rs_s, p_s = simulate_paths(curve, kappa, sigma, months, paths, seed, shift=s)
        io_s, po_s = pool_flows(pool, model, p_s)
        vals[s] = pv_paths(io_s + po_s, rs_s, oas).mean()
        out["io" + ("_dn" if s < 0 else "_up")] = pv_paths(io_s, rs_s, oas).mean()
        out["po" + ("_dn" if s < 0 else "_up")] = pv_paths(po_s, rs_s, oas).mean()
    out["duration"] = (vals[-dy] - vals[dy]) / (2 * price * dy)
    out["convexity"] = (vals[-dy] + vals[dy] - 2 * price) / (price * dy * dy)
    out["wal"] = float(((po * np.arange(1, months + 1) / 12).sum(axis=1) / po.sum(axis=1)).mean())
    return out


def s_curve_table(model: PrepayModel, lo: float = -0.02, hi: float = 0.03, n: int = 51):
    return [(x, float(model.refi(np.array(x)))) for x in np.linspace(lo, hi, n)]
