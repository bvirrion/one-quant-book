"""FX volatility (build of Book 5, Chapter 20): the vanna-volga smile and its barrier adjustment, a
stochastic-local volatility model whose leverage function L(t, S) is calibrated by the particle method, and a
target-redemption forward on simulated paths.

Garman-Kohlhagen conventions (Book 2's firm_fxsmile): spot S in quote units per base unit, rd the quote
currency's rate, rf the base currency's; a call is a call on the base currency.
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

FIRM = pathlib.Path(__file__).resolve().parents[1]
for comp in ("fxsmile", "bs"):
    sys.path.insert(0, str(FIRM / comp))
from firm_fxsmile import N, forward, gk  # noqa: E402


# ---------------------------------------------------------------- vanna-volga
def _greeks(s, k, t, rd, rf, vol):
    f, sd = forward(s, t, rd, rf), vol * math.sqrt(t)
    d1 = math.log(f / k) / sd + 0.5 * sd
    d2 = d1 - sd
    vega = s * math.exp(-rf * t) * math.sqrt(t) * math.exp(-0.5 * d1 * d1) / math.sqrt(2 * math.pi)
    return vega, -vega * d2 / (s * vol), vega * d1 * d2 / vol           # vega, vanna, volga


def vv_weights(k, pillars, s, t, rd, rf, vol_atm):
    """Weights on the three pillar options that match the vega, vanna and volga of an option at strike k, all
    computed at the at-the-money volatility."""
    a = np.array([_greeks(s, kp, t, rd, rf, vol_atm) for kp in pillars]).T
    b = np.array(_greeks(s, k, t, rd, rf, vol_atm))
    return np.linalg.solve(a, b)


def vv_price(k, pillars, pillar_vols, s, t, rd, rf, phi: int = 1) -> float:
    """Vanna-volga price of a vanilla at strike k: its Black price at the ATM volatility plus the weighted market
    costs of the three pillars (pillars ordered put wing, ATM, call wing)."""
    vol_atm = pillar_vols[1]
    w = vv_weights(k, pillars, s, t, rd, rf, vol_atm)
    cost = [gk(s, kp, t, rd, rf, v) - gk(s, kp, t, rd, rf, vol_atm) for kp, v in zip(pillars, pillar_vols, strict=True)]
    return gk(s, k, t, rd, rf, vol_atm, phi) + float(w @ np.array(cost))


def vv_implied(k, pillars, pillar_vols, s, t, rd, rf) -> float:
    target = vv_price(k, pillars, pillar_vols, s, t, rd, rf)
    lo, hi = 1e-4, 3.0
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if gk(s, k, t, rd, rf, mid) < target else (lo, mid)
    return 0.5 * (lo + hi)


def up_hit_probability(s, h, t, rd, rf, vol) -> float:
    """Probability of touching an upper barrier h > s by t (drift rd - rf - vol^2 / 2 in log)."""
    nu = rd - rf - 0.5 * vol * vol
    sv = vol * math.sqrt(t)
    x = math.log(h / s)
    return N((-x + nu * t) / sv) + math.exp(2 * nu * x / (vol * vol)) * N((-x - nu * t) / sv)


def one_touch_bs(s, h, t, rd, rf, vol) -> float:
    """Upper one-touch paying 1 (quote currency) at expiry."""
    return math.exp(-rd * t) * up_hit_probability(s, h, t, rd, rf, vol)


def one_touch_vv(s, h, t, rd, rf, pillars, pillar_vols) -> float:
    """Market-practice vanna-volga one-touch: the Black price at the ATM volatility plus the vanna and volga
    costs of the smile, weighted by the probability of not touching (the correction fades as the touch becomes
    likely). Vanna and volga of the touch by finite differences; costs from the 25-delta risk reversal and
    butterfly."""
    vol_atm = pillar_vols[1]
    p_nt = 1 - up_hit_probability(s, h, t, rd, rf, vol_atm)
    dv, ds = 1e-4, 1e-4 * s

    def ot(x, v):
        return one_touch_bs(x, h, t, rd, rf, v)
    up = ot(s + ds, vol_atm + dv) - ot(s - ds, vol_atm + dv)
    down = ot(s + ds, vol_atm - dv) - ot(s - ds, vol_atm - dv)
    vanna = (up - down) / (4 * ds * dv)
    volga = (ot(s, vol_atm + dv) - 2 * ot(s, vol_atm) + ot(s, vol_atm - dv)) / (dv * dv)
    kp, katm, kc = pillars
    rr = gk(s, kc, t, rd, rf, pillar_vols[2]) - gk(s, kc, t, rd, rf, vol_atm) \
        - (gk(s, kp, t, rd, rf, pillar_vols[0], -1) - gk(s, kp, t, rd, rf, vol_atm, -1))
    bf = 0.5 * (gk(s, kc, t, rd, rf, pillar_vols[2]) - gk(s, kc, t, rd, rf, vol_atm)
                + gk(s, kp, t, rd, rf, pillar_vols[0], -1) - gk(s, kp, t, rd, rf, vol_atm, -1))
    _, rr_vanna, _ = (a - b for a, b in zip(_greeks(s, kc, t, rd, rf, vol_atm), _greeks(s, kp, t, rd, rf, vol_atm),
                                            strict=True))
    bf_volga = 0.5 * (_greeks(s, kc, t, rd, rf, vol_atm)[2] + _greeks(s, kp, t, rd, rf, vol_atm)[2])
    return ot(s, vol_atm) + p_nt * (vanna / rr_vanna * rr + volga / bf_volga * bf)


# ---------------------------------------------------------------- stochastic-local volatility
@dataclass(frozen=True)
class SLV:
    """dS/S = (rd - rf) dt + L(t, S) sqrt(v) dW1, dv = kappa (vbar - v) dt + mix eta sqrt(v) dW2, <dW1, dW2> =
    rho dt. mix = 0 is local volatility, mix = 1 with L = 1 is Heston."""
    v0: float
    kappa: float
    vbar: float
    eta: float
    rho: float
    mix: float


def calibrate_leverage(model: SLV, local_vol, s0: float, rd: float, rf: float, t_end: float, steps_per_year: int = 252,
                       n: int = 50_000, bins: int = 40, seed: int = 20):
    """Particle method: simulate the model, and at every step set L(t, S)^2 = sigma_LV(t, S)^2 / E[v_t | S_t = S],
    the conditional expectation estimated by binning the particles in S (quantile bins, linear interpolation).
    Returns (times, list of (bin centres, L values))."""
    rng = np.random.default_rng(seed)
    steps = round(t_end * steps_per_year)
    dt = t_end / steps
    x = np.full(n, math.log(s0))
    v = np.full(n, model.v0)
    c = math.sqrt(1 - model.rho ** 2)
    table = []
    times = []
    for i in range(steps):
        t = i * dt
        s = np.exp(x)
        vp = np.maximum(v, 1e-12)
        order = np.argsort(s)
        edges = np.array_split(order, bins)
        centres = np.array([s[e].mean() for e in edges])
        ev = np.array([vp[e].mean() for e in edges])
        lv = local_vol(max(t, 1e-3), centres)
        lev = lv / np.sqrt(ev)
        table.append((centres, lev))
        times.append(t)
        lpart = np.interp(s, centres, lev)
        z1 = rng.standard_normal(n)
        z2 = model.rho * z1 + c * rng.standard_normal(n)
        sig = lpart * np.sqrt(vp)
        x = x + (rd - rf - 0.5 * sig * sig) * dt + sig * math.sqrt(dt) * z1
        v = v + model.kappa * (model.vbar - vp) * dt + model.mix * model.eta * np.sqrt(vp * dt) * z2
    return np.array(times), table


def simulate_slv(model: SLV, leverage, s0: float, rd: float, rf: float, t_end: float, n: int = 100_000,
                 steps_per_year: int = 252, seed: int = 21, record_every: int = 1) -> np.ndarray:
    """Paths (n, steps / record_every + 1) of the SLV model with a calibrated leverage table (antithetic)."""
    times, table = leverage
    rng = np.random.default_rng(seed)
    steps = round(t_end * steps_per_year)
    dt = t_end / steps
    half = n // 2
    x = np.full(2 * half, math.log(s0))
    v = np.full(2 * half, model.v0)
    c = math.sqrt(1 - model.rho ** 2)
    out = [np.exp(x)]
    for i in range(steps):
        centres, lev = table[min(i, len(table) - 1)]
        s = np.exp(x)
        vp = np.maximum(v, 1e-12)
        z1 = rng.standard_normal(half)
        z2 = rng.standard_normal(half)
        z1, z2 = np.concatenate([z1, -z1]), np.concatenate([z2, -z2])
        z2 = model.rho * z1 + c * z2
        sig = np.interp(s, centres, lev) * np.sqrt(vp)
        x = x + (rd - rf - 0.5 * sig * sig) * dt + sig * math.sqrt(dt) * z1
        v = v + model.kappa * (model.vbar - vp) * dt + model.mix * model.eta * np.sqrt(vp * dt) * z2
        if (i + 1) % record_every == 0:
            out.append(np.exp(x))
    return np.column_stack(out)


# ---------------------------------------------------------------- target-redemption forward
def tarf_client_pnl(fixings: np.ndarray, strike: float, target: float, leverage: float = 2.0,
                    notional: float = 1e6) -> dict:
    """Client sells `notional` of the base currency at `strike` at each fixing while the spot is below it (a gain
    of strike - S per unit), and `leverage` times the notional when the spot is above it (a loss); the contract
    ends at the fixing where the accumulated gain reaches `target` (per unit), that fixing's gain capped at the
    target. fixings: (n_paths, n_fixings). Returns the P&L per path (quote currency, undiscounted) and the number
    of fixings each path lived."""
    n, m = fixings.shape
    alive = np.ones(n, bool)
    gained = np.zeros(n)
    pnl = np.zeros(n)
    lived = np.zeros(n, int)
    for j in range(m):
        s = fixings[:, j]
        gain = np.maximum(strike - s, 0.0)
        gain = np.minimum(gain, np.maximum(target - gained, 0.0))
        loss = leverage * np.maximum(s - strike, 0.0)
        pnl += np.where(alive, notional * (gain - loss), 0.0)
        gained += np.where(alive, gain, 0.0)
        lived += alive
        alive &= gained < target - 1e-12
    return {"pnl": pnl, "fixings": lived, "redeemed": ~alive}
