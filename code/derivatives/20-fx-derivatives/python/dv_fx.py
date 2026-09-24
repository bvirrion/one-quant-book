"""FX derivatives (Book 5, Chapter 20): a dollar-emerging-currency pair whose market is a Heston model (the
'true' smile at every expiry), the broker quotes it implies, vanna-volga against it, one-touch prices under
local, stochastic and stochastic-local volatility, the leverage function, and a target-redemption forward.
Spot 7.00, quote-currency rate 3%, dollar rate 5%."""
import functools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "volsurface", "localvol", "heston", "jumps", "fxsmile", "fxvol"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_fxsmile import atm_dns, forward, gk, strike_from_delta  # noqa: E402
from firm_fxvol import (  # noqa: E402
    SLV,
    calibrate_leverage,
    one_touch_bs,
    one_touch_vv,
    simulate_slv,
    tarf_client_pnl,
    vv_implied,
)
from firm_heston import Heston  # noqa: E402
from firm_jumps import implied_vols  # noqa: E402  (its Fourier grid reaches the short, low-volatility expiries)
from firm_localvol import LocalVolGrid  # noqa: E402
from firm_volsurface import density_factor  # noqa: E402

S0, RD, RF = 7.00, 0.03, 0.05
MARKET = Heston(v0=0.0036, kappa=1.5, vbar=0.0049, eta=0.30, rho=0.5)


def market_vol(k: float, t: float) -> float:
    return float(implied_vols(MARKET, forward(S0, t, RD, RF), [k], t)[0])


def quotes(t: float = 1.0) -> dict:
    """Broker quotes implied by the market at t: ATM delta-neutral straddle, 25- and 10-delta risk reversals and
    butterflies (smile strangle convention), with the strikes."""
    # iterate: the ATM strike depends on the ATM vol, a delta strike on its own vol
    atm_v = market_vol(forward(S0, t, RD, RF), t)
    for _ in range(20):
        k_atm = atm_dns(S0, t, RD, RF, atm_v)
        atm_v = market_vol(k_atm, t)
    out = {"atm": atm_v, "k_atm": k_atm}
    for d in (0.25, 0.10):
        vc = vp = atm_v
        for _ in range(30):
            kc = strike_from_delta(S0, t, RD, RF, vc, d, 1)
            kp = strike_from_delta(S0, t, RD, RF, vp, -d, -1)
            vc, vp = market_vol(kc, t), market_vol(kp, t)
        tag = f"{round(100 * d)}"
        out.update({f"k{tag}c": kc, f"k{tag}p": kp, f"v{tag}c": vc, f"v{tag}p": vp, f"rr{tag}": vc - vp,
                    f"bf{tag}": 0.5 * (vc + vp) - atm_v})
    return out


def vv_smile(t: float = 1.0, n: int = 41) -> dict:
    q = quotes(t)
    pillars = (q["k25p"], q["k_atm"], q["k25c"])
    vols = (q["v25p"], q["atm"], q["v25c"])
    ks = np.linspace(q["k10p"] * 0.99, q["k10c"] * 1.01, n)
    return {"ks": ks, "market": np.array([market_vol(k, t) for k in ks]),
            "vv": np.array([vv_implied(k, pillars, vols, S0, t, RD, RF) for k in ks]), "q": q}


# ---------------------------------------------------------------- local volatility of the market and SLV
@functools.cache
def lv_grid():
    """Dupire on a mesh: the market's total variance on 53 slices x 121 log-moneyness points (one Fourier
    evaluation per slice), differentiated by central differences, the butterfly factor of chapter 7 in the
    denominator."""
    times = np.arange(0.02, 1.0801, 0.02)
    ks = np.linspace(-0.30, 0.30, 121)
    w = np.empty((len(times), len(ks)))
    for i, t in enumerate(times):
        bound = 5 * 0.06 * math.sqrt(t)
        kc = np.clip(ks, -bound, bound)
        f = forward(S0, t, RD, RF)
        vols = implied_vols(MARKET, f, f * np.exp(np.unique(kc)), t)
        w[i] = np.interp(kc, np.unique(kc), vols) ** 2 * t
    dk, dt = ks[1] - ks[0], times[1] - times[0]
    wk = np.gradient(w, dk, axis=1)
    wkk = np.gradient(wk, dk, axis=1)
    wt = np.gradient(w, dt, axis=0)
    g = np.vectorize(density_factor)(w, wk, wkk, ks[None, :])
    var = np.where((g > 0) & (wt > 0), wt / np.maximum(g, 1e-12), np.nan)
    for i in range(len(times)):                       # fill any bad node from its neighbours in k
        row = var[i]
        good = np.isfinite(row)
        var[i] = np.interp(ks, ks[good], row[good])
    return LocalVolGrid(times, ks, np.sqrt(var), S0, RD - RF)


def local_vol(t, s):
    return lv_grid().sigma(t, np.asarray(s, float))


@functools.cache
def leverage(mix: float):
    model = SLV(MARKET.v0, MARKET.kappa, MARKET.vbar, MARKET.eta, MARKET.rho, mix)
    return model, calibrate_leverage(model, local_vol, S0, RD, RF, 1.0)


@functools.cache
def paths(mix: float, n: int = 100_000, seed: int = 21) -> np.ndarray:
    """Daily paths over a year: mix = 0 is local volatility, 1 is (close to) Heston, between them SLV."""
    model, lev = leverage(mix)
    return simulate_slv(model, lev, S0, RD, RF, 1.0, n=n, seed=seed)


def repricing(mix: float, strikes=None) -> np.ndarray:
    """One-year implied volatilities of each model's simulated calls, against the market's."""
    p = paths(mix)[:, -1]
    q = quotes()
    strikes = (q["k10p"], q["k25p"], q["k_atm"], q["k25c"], q["k10c"]) if strikes is None else strikes
    f = forward(S0, 1.0, RD, RF)
    out = []
    for k in strikes:
        c = math.exp(-RD) * float(np.maximum(p - k, 0).mean())
        lo, hi = 1e-4, 1.0
        for _ in range(80):
            mid = 0.5 * (lo + hi)
            lo, hi = (mid, hi) if gk(S0, k, 1.0, RD, RF, mid) < c else (lo, mid)
        out.append(0.5 * (lo + hi))
    return np.array(out), np.array([market_vol(k, 1.0) for k in strikes]), f


BARRIERS = (7.20, 7.40, 7.60, 7.80, 8.00)


def one_touches(mixes=(0.0, 0.5, 1.0)) -> dict:
    """Upper one-touches (paying 1 at expiry, one year, continuous monitoring) by barrier: Black at the ATM
    volatility, vanna-volga, and simulations under local, stochastic-local (mix 0.5) and stochastic volatility
    (daily paths, barrier moved in by the shift of chapter 15)."""
    q = quotes()
    pillars, vols = (q["k25p"], q["k_atm"], q["k25c"]), (q["v25p"], q["atm"], q["v25c"])
    out = {"bs": [one_touch_bs(S0, h, 1.0, RD, RF, q["atm"]) for h in BARRIERS],
           "vv": [one_touch_vv(S0, h, 1.0, RD, RF, pillars, vols) for h in BARRIERS]}
    shift = math.exp(-0.5826 * q["atm"] * math.sqrt(1 / 252))      # daily paths read as continuous monitoring
    for mix in mixes:
        mx = paths(mix).max(axis=1)
        out[f"mix{mix}"] = [math.exp(-RD) * float((mx >= h * shift).mean()) for h in BARRIERS]
    return out


# ---------------------------------------------------------------- the target-redemption forward
FIX = np.arange(21, 253, 21)                              # monthly fixings (trading-day indices)


def tarf_strike(mix: float = 0.5, target: float = 0.30) -> float:
    """The strike at which the client's TARF is worth zero at inception (bisection)."""
    fx = paths(mix)[:, FIX]
    lo, hi = 6.0, 8.0
    for _ in range(50):
        mid = 0.5 * (lo + hi)
        v = tarf_client_pnl(fx, mid, target)["pnl"].mean()
        lo, hi = (mid, hi) if v < 0 else (lo, mid)
    return 0.5 * (lo + hi)


def tarf_summary(mix: float = 0.5, target: float = 0.30) -> dict:
    k = tarf_strike(mix, target)
    res = tarf_client_pnl(paths(mix)[:, FIX], k, target)
    return {"strike": k, "fwd1y": forward(S0, 1.0, RD, RF), "expected_fixings": float(res["fixings"].mean()),
            "redeemed": float(res["redeemed"].mean()), "pnl_mean": float(res["pnl"].mean()),
            "pnl_5": float(np.percentile(res["pnl"], 5)), "fixings_hist": np.bincount(res["fixings"], minlength=13)}


def tarf_scenario(move: float = 0.10, mix: float = 0.5, target: float = 0.30) -> dict:
    """The spot moves by `move` against the client over the first quarter (linearly at the three fixings); the
    remaining nine months follow the model from there. Client's expected P&L per million of notional."""
    k = tarf_strike(mix, target)
    p = paths(mix)
    first = S0 * (1 + move * np.arange(1, 4) / 3)
    later = p[:, FIX[3:]] / p[:, [FIX[2]]] * first[-1]        # the model's returns after the third fixing
    fx = np.hstack([np.tile(first, (len(p), 1)), later])
    res = tarf_client_pnl(fx, k, target)
    return {"strike": k, "pnl_mean": float(res["pnl"].mean()), "first_quarter": float(
        tarf_client_pnl(np.tile(first, (1, 1)), k, target)["pnl"][0]), "fixings": float(res["fixings"].mean())}
