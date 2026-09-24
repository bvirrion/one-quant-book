"""Jumps and Levy models (Book 5, Chapter 13): a scheduled binary event, jump models fitted to a short-dated
smile, the short-expiry behaviour that separates jumps from diffusion, and what a delta hedge cannot do.
Zero rates and dividends throughout."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "heston", "jumps"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
sys.path.insert(0, str(ROOT / "code/derivatives/10-stochastic-volatility/python"))
from dv_heston import calibration  # noqa: E402
from firm_bs import black, greeks, implied_vol  # noqa: E402
from firm_heston import implied_vols as heston_vols  # noqa: E402
from firm_jumps import (  # noqa: E402
    Bates,
    EventJump,
    Kou,
    Merton,
    VarianceGamma,
    calibrate,
    implied_vols,
    skew_kurtosis,
)
from firm_svi import ssvi  # noqa: E402

# ---------------------------------------------------------------- the scheduled event
S0, T_EVENT, SIGMA_D = 50.0, 1 / 52, 0.35          # one-week options on a biotechnology share
EVENT = EventJump.from_up(SIGMA_D, 0.4, 0.20)       # success with probability 0.4: +20% in log
EVENT_STRIKES = np.arange(38.0, 62.01, 2.0)


def event_smile(model: EventJump = EVENT, strikes=EVENT_STRIKES) -> np.ndarray:
    out = []
    for k in strikes:
        c = model.mixture_call(S0, k, T_EVENT)
        right = "C" if k >= S0 else "P"
        out.append(implied_vol(c if right == "C" else c - (S0 - k), S0, k, T_EVENT, 1.0, right))
    return np.array(out)


def event_density(model: EventJump = EVENT, xs=None) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Density of S_T under the event model and under a lognormal with the event model's at-the-money vol."""
    xs = np.linspace(25.0, 80.0, 221) if xs is None else xs
    c = model.p * math.exp(model.a) + (1 - model.p) * math.exp(model.b)
    sd = model.sigma * math.sqrt(T_EVENT)

    def lognormal(x, f, s):
        return np.exp(-(np.log(x / f) + 0.5 * s * s) ** 2 / (2 * s * s)) / (x * s * math.sqrt(2 * math.pi))
    mix = (model.p * lognormal(xs, S0 * math.exp(model.a) / c, sd)
           + (1 - model.p) * lognormal(xs, S0 * math.exp(model.b) / c, sd))
    atm = float(event_smile(model, [S0])[0])
    return xs, mix, lognormal(xs, S0, atm * math.sqrt(T_EVENT))


def event_summary(model: EventJump = EVENT) -> dict:
    atm = float(event_smile(model, [S0])[0])
    c = model.p * math.exp(model.a) + (1 - model.p) * math.exp(model.b)
    move_var = atm ** 2 * T_EVENT - model.sigma ** 2 * T_EVENT   # event variance, as in chapter 8
    jumps = np.array([model.a, model.b]) - math.log(c)
    true_sd = math.sqrt(model.p * jumps[0] ** 2 + (1 - model.p) * jumps[1] ** 2
                        - (model.p * jumps[0] + (1 - model.p) * jumps[1]) ** 2)
    straddle = model.mixture_call(S0, S0, T_EVENT) * 2               # call + put at the forward
    return {"atm": atm, "up": math.exp(model.a) - 1, "down": math.exp(model.b) - 1,
            "implied_move": math.sqrt(move_var), "true_move_sd": true_sd, "straddle": straddle}


def market_outcomes(seed: int = 13, n: int = 400) -> list[EventJump]:
    """A richer 'market': the outcome sizes are themselves uncertain (log-jumps around +0.20 and around the
    fair down move, each with a standard deviation of 0.04); each draw is a fair two-point event."""
    rng = np.random.default_rng(seed)
    ups, downs = 0.20 + 0.04 * rng.standard_normal(n), EVENT.b + 0.04 * rng.standard_normal(n)
    return [EventJump(SIGMA_D, EVENT.p, a, b) for a, b in zip(ups, downs, strict=True)]


def market_event_smile(seed: int = 13) -> np.ndarray:
    """The one-week smile of the richer market: prices averaged over the outcome-size draws."""
    draws = market_outcomes(seed)
    vols = []
    for k in EVENT_STRIKES:
        c = float(np.mean([m.mixture_call(S0, k, T_EVENT) for m in draws]))
        right = "C" if k >= S0 else "P"
        vols.append(implied_vol(c if right == "C" else c - (S0 - k), S0, k, T_EVENT, 1.0, right))
    return np.array(vols)


def fit_event(vols=None) -> tuple[EventJump, float]:
    """Fit (sigma, p, a) of the two-point event model, b set by fairness, to a one-week smile."""
    vols = market_event_smile() if vols is None else vols

    def make(z):
        return EventJump.from_up(math.exp(z[0]), 1 / (1 + math.exp(-z[1])), math.exp(z[2]))
    model, _, rmse = calibrate(make, [math.log(0.3), 0.0, math.log(0.15)], [(T_EVENT, EVENT_STRIKES, vols)], S0)
    return model, rmse


def _straddle_after(s, sigma: float):
    t_after = T_EVENT - 1 / 252
    return black(s, S0, t_after, 1.0, sigma, "C") + black(s, S0, t_after, 1.0, sigma, "P")


def event_hedge(model: EventJump = EVENT) -> dict:
    """Hedge a short at-the-money straddle across the announcement, from just before to just after: the P&L
    of each outcome is -(V(S e^J) - V(S)) + Delta S (e^J - 1), with V after the event valued by Black at the
    diffusion volatility and four trading days to run. Deltas: none, Black's at the straddle's implied
    volatility, the model's dV/dS, and the ratio that minimises the variance over the two outcomes."""
    c = model.p * math.exp(model.a) + (1 - model.p) * math.exp(model.b)
    moves = np.array([math.exp(model.a) / c, math.exp(model.b) / c]) - 1
    probs = np.array([model.p, 1 - model.p])

    def straddle_before(s):
        return 2 * model.mixture_call(s, S0, T_EVENT) - (s - S0)

    v0 = straddle_before(S0)
    dv = np.array([_straddle_after(S0 * (1 + m), model.sigma) for m in moves]) - v0
    h = 1e-4 * S0
    deltas = {
        "none": 0.0,
        "black": 2 * greeks(S0, S0, T_EVENT, 0.0, 0.0, event_summary(model)["atm"], "C")["delta"] - 1,
        "model": (straddle_before(S0 + h) - straddle_before(S0 - h)) / (2 * h),
        "minvar": float(np.sum(probs * dv * S0 * moves) / np.sum(probs * (S0 * moves) ** 2)),
    }
    out = {"premium": v0, "moves": moves, "dv": dv, "deltas": deltas, "pnl": {}}
    for name, d in deltas.items():
        pnl = -(dv - d * S0 * moves)                 # short straddle, long d shares
        mean = float(np.sum(probs * pnl))
        out["pnl"][name] = (pnl, mean, float(math.sqrt(np.sum(probs * (pnl - mean) ** 2))))
    return out


def event_hedge_uncertain(seed: int = 13) -> dict:
    """The same hedge when the outcome sizes are uncertain (the richer market): the best single ratio no
    longer removes the risk. Returns the ratio and the residual standard deviation, in premium units too."""
    draws = market_outcomes(seed)
    moves, probs, dvs = [], [], []
    v0 = float(np.mean([2 * m.mixture_call(S0, S0, T_EVENT) for m in draws]))
    for m in draws:
        c = m.p * math.exp(m.a) + (1 - m.p) * math.exp(m.b)
        for prob, j in ((m.p, m.a), (1 - m.p, m.b)):
            mv = math.exp(j) / c - 1
            moves.append(mv)
            probs.append(prob / len(draws))
            dvs.append(_straddle_after(S0 * (1 + mv), m.sigma) - v0)
    moves, probs, dvs = np.array(moves), np.array(probs), np.array(dvs)
    ratio = float(np.sum(probs * dvs * S0 * moves) / np.sum(probs * (S0 * moves) ** 2))
    pnl = -(dvs - ratio * S0 * moves)
    mean = float(np.sum(probs * pnl))
    sd = float(math.sqrt(np.sum(probs * (pnl - mean) ** 2)))
    return {"premium": v0, "ratio": ratio, "sd": sd, "sd_rel": sd / v0}


# ---------------------------------------------------------------- jump models against chapter 9's surface
Z_GRID = np.linspace(-2.0, 2.0, 9)          # quoted strikes: 100 exp(0.2 sqrt(T) z), two 'standard moves' each way
TENORS = (1 / 52, 2 / 52, 1 / 12, 2 / 12, 0.25, 0.5, 1.0, 2.0)


def market_vol(k: float, t: float) -> float:
    """Chapter 9's market at strike k (spot 100): SSVI with rho -0.6, eta 1.0, gamma 0.45."""
    theta = (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t
    return math.sqrt(float(ssvi(math.log(k / 100.0), theta, -0.6, 1.0, 0.45)) / t)


def strikes_for(t: float) -> np.ndarray:
    return 100.0 * np.exp(0.2 * math.sqrt(t) * Z_GRID)


def quotes(t: float):
    ks = strikes_for(t)
    return (t, ks, np.array([market_vol(k, t) for k in ks]))


def _pos(x):
    return math.exp(x)


def fit_models(t: float = 1 / 12) -> dict:
    """Merton, Kou and variance gamma fitted to one expiry of the market."""
    q = [quotes(t)]
    fits = {}
    fits["merton"] = calibrate(lambda z: Merton(_pos(z[0]), _pos(z[1]), z[2], _pos(z[3])),
                               [math.log(0.12), math.log(1.0), -0.1, math.log(0.1)], q, 100.0)
    fits["kou"] = calibrate(lambda z: Kou(_pos(z[0]), _pos(z[1]), 1 / (1 + math.exp(-z[2])), 1 + _pos(z[3]),
                                          _pos(z[4])),
                            [math.log(0.12), math.log(1.0), -1.0, math.log(20.0), math.log(10.0)], q, 100.0)
    fits["vg"] = calibrate(lambda z: VarianceGamma(_pos(z[0]), _pos(z[1]), z[2]),
                           [math.log(0.12), math.log(0.2), -0.1], q, 100.0)
    return fits


def fit_bates() -> tuple[Bates, float]:
    """Bates fitted to the whole surface, from one week to two years."""
    q = [quotes(t) for t in TENORS]

    def make(z):
        return Bates(_pos(z[0]), _pos(z[1]), _pos(z[2]), _pos(z[3]), math.tanh(z[4]), _pos(z[5]), z[6], _pos(z[7]))
    z0 = [math.log(0.03), math.log(2.0), math.log(0.05), math.log(0.6), -0.9, math.log(0.5), -0.1, math.log(0.1)]
    model, _, rmse = calibrate(make, z0, q, 100.0, max_iter=60)
    return model, rmse


def atm_skew(vol_fn, t: float) -> float:
    h = 0.05 * math.sqrt(t)
    lo, hi = vol_fn(np.array([100 * math.exp(-h), 100 * math.exp(h)]), t)
    return float((hi - lo) / (2 * h))


def skew_terms(fits=None, bates=None) -> dict[str, np.ndarray]:
    fits = fit_models() if fits is None else fits
    bates = fit_bates()[0] if bates is None else bates
    heston = calibration()[0]
    out = {"market": np.array([atm_skew(lambda ks, t: np.array([market_vol(k, t) for k in ks]), t) for t in TENORS])}
    for name in ("merton", "vg"):
        m = fits[name][0]
        out[name] = np.array([atm_skew(lambda ks, t, m=m: implied_vols(m, 100.0, ks, t), t) for t in TENORS])
    out["heston"] = np.array([atm_skew(lambda ks, t: heston_vols(heston, 100.0, ks, t), t) for t in TENORS])
    out["bates"] = np.array([atm_skew(lambda ks, t: implied_vols(bates, 100.0, ks, t), t) for t in TENORS])
    return out


# ---------------------------------------------------------------- short expiries: jumps against diffusion
def otm_put_decay(model: Merton, ts=None, strike: float = 90.0) -> dict[str, np.ndarray]:
    """Price of a 10% out-of-the-money put as expiry shrinks, under the jump model and under Black-Scholes at
    the model's own root-mean variance; divided by T it tends, with jumps, to lam E[(K - S e^J)^+]."""
    ts = np.geomspace(1 / 365, 0.25, 25) if ts is None else ts
    c2 = model.cumulants(1.0)[0]
    jump_prices = np.array([model.series_call(100.0, strike, t) - (100.0 - strike) for t in ts])
    bs_prices = np.array([black(100.0, strike, t, 1.0, math.sqrt(c2), "P") for t in ts])
    z, w = np.polynomial.hermite_e.hermegauss(80)
    limit = float(model.lam * np.sum(w * np.maximum(strike - 100.0 * np.exp(model.mu + model.delta * z), 0.0))
                  / math.sqrt(2 * math.pi))
    return {"t": ts, "jump": jump_prices, "bs": bs_prices, "limit": limit}


def moments_table(model, ts=(1 / 52, 1 / 12, 0.25, 1.0, 4.0)) -> list[tuple[float, float, float]]:
    return [(t, *skew_kurtosis(model, t)) for t in ts]


# ---------------------------------------------------------------- what a delta hedge leaves: Merton world
def merton_delta(model: Merton, fwd: np.ndarray, strike: float, t: float, n_max: int = 25) -> np.ndarray:
    """dC/dF for Merton's series formula, vectorised over forwards."""
    kbar = math.exp(model.mu + 0.5 * model.delta ** 2) - 1
    out = np.zeros_like(fwd)
    w = math.exp(-model.lam * t)
    for n in range(n_max):
        if n:
            w *= model.lam * t / n
        g = math.exp(n * (model.mu + 0.5 * model.delta ** 2) - model.lam * kbar * t)
        vol = math.sqrt(model.sigma ** 2 + n * model.delta ** 2 / t)
        d1 = (np.log(fwd * g / strike) + 0.5 * vol * vol * t) / (vol * math.sqrt(t))
        out += w * g * 0.5 * np.vectorize(math.erfc)(-d1 / math.sqrt(2))
    return out


def hedge_experiment(model: Merton, t: float = 1 / 12, steps: int = 21, n: int = 20_000, seed: int = 13) -> dict:
    """Sell a one-month at-the-money call at the model price and delta-hedge it daily with the model delta,
    under Merton dynamics and under a diffusion with the same total variance hedged with Black's delta.
    Returns the hedged P&L per unit premium for both worlds."""
    rng = np.random.default_rng(seed)
    dt = t / steps
    kbar = math.exp(model.mu + 0.5 * model.delta ** 2) - 1
    vol_eq = math.sqrt(model.cumulants(1.0)[0])
    out = {}
    for world in ("merton", "diffusion"):
        s = np.full(n, 100.0)
        cash = np.full(n, model.series_call(100.0, 100.0, t) if world == "merton"
                       else black(100.0, 100.0, t, 1.0, vol_eq, "C"))
        premium = float(cash[0])
        pos = np.zeros(n)
        for i in range(steps):
            tau = t - i * dt
            if world == "merton":
                d = merton_delta(model, s, 100.0, tau)
            else:
                d1 = (np.log(s / 100.0) + 0.5 * vol_eq ** 2 * tau) / (vol_eq * math.sqrt(tau))
                d = 0.5 * np.vectorize(math.erfc)(-d1 / math.sqrt(2))
            cash -= (d - pos) * s
            pos = d
            z = rng.standard_normal(n)
            if world == "merton":
                nj = rng.poisson(model.lam * dt, n)
                jump = nj * model.mu + np.sqrt(nj) * model.delta * rng.standard_normal(n)
                s = s * np.exp((-0.5 * model.sigma ** 2 - model.lam * kbar) * dt
                               + model.sigma * math.sqrt(dt) * z + jump)
            else:
                s = s * np.exp(-0.5 * vol_eq ** 2 * dt + vol_eq * math.sqrt(dt) * z)
        pnl = cash + pos * s - np.maximum(s - 100.0, 0.0)
        out[world] = pnl / premium
    out["premium"] = premium
    return out
