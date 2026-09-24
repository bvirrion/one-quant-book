"""Local volatility: from the implied surface to Dupire's local volatility, repricing the vanillas, the
forward smile and the smile's dynamics (Book 5, Chapter 9). Zero rates and dividends: F = S."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "volsurface", "localvol"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_bs import implied_vol  # noqa: E402
from firm_localvol import build_grid, local_variance, simulate  # noqa: E402
from firm_svi import ssvi  # noqa: E402

RHO, ETA, GAMMA = -0.6, 1.0, 0.45
S0 = 100.0


def theta(t: float) -> float:
    return (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t


def w_fn(k: float, t: float) -> float:
    """The chapter's implied surface: SSVI with the power law (arbitrage-free by chapter 8's theorem)."""
    return float(ssvi(k, theta(t), RHO, ETA, GAMMA))


def implied(k: float, t: float) -> float:
    return math.sqrt(w_fn(k, t) / t)


def local(k: float, t: float) -> float:
    return math.sqrt(local_variance(w_fn, k, t))


GRID_T = np.concatenate([[0.004], np.arange(0.02, 1.2001, 0.02)])
GRID_K = np.linspace(-1.0, 0.6, 161)


def grid():
    return build_grid(w_fn, GRID_T, GRID_K)


def atm_skew(fn, t: float, h: float = 0.01) -> float:
    """d sigma / dk at k = 0 by central difference."""
    return (fn(h, t) - fn(-h, t)) / (2 * h)


def mc_smile(t: float = 0.5, n: int = 200_000, seed: int = 7, strikes=(80, 90, 100, 110, 120), s0: float = S0):
    g = grid()
    st, _ = simulate(g, s0, t, int(round(252 * t)), n, seed)
    out = []
    for k in strikes:
        pay = np.maximum(st - k, 0.0) if k >= s0 else np.maximum(k - st, 0.0)
        p = float(pay.mean())
        se = float(pay.std(ddof=1) / math.sqrt(n))
        right = "C" if k >= s0 else "P"
        iv = implied_vol(p, s0, k, t, 1.0, right)
        out.append({"strike": k, "mc_vol": iv, "surface_vol": implied(math.log(k / S0), t),
                    "se_vol": se / (s0 * math.sqrt(t) * math.exp(-0.5 * (math.log(k / s0) / (iv * math.sqrt(t))) ** 2)
                                    / math.sqrt(2 * math.pi))})
    return out


def forward_smile(t1: float = 0.5, t2: float = 1.0, n: int = 200_000, seed: int = 11, xs=None):
    """Implied volatility of forward-start calls paying (S_t2 - x S_t1)^+ against today's smile of the same
    maturity t2 - t1."""
    xs = np.linspace(0.80, 1.20, 17) if xs is None else xs
    g = grid()
    st2, rec = simulate(g, S0, t2, int(round(252 * t2)), n, seed, record=(t1,))
    st1 = rec[t1]
    tau = t2 - t1
    out = []
    for x in xs:
        pay = np.maximum(st2 - x * st1, 0.0) if x >= 1 else np.maximum(x * st1 - st2, 0.0)
        p = float(pay.mean()) / S0
        out.append((float(x), implied_vol(p, 1.0, float(x), tau, 1.0, "C" if x >= 1 else "P"),
                    implied(math.log(x), tau)))
    return out


def fwd_skew_ratio(fs) -> dict[str, float]:
    by = {round(x, 3): (v, today) for x, v, today in fs}
    fwd = (by[0.95][0] - by[1.05][0]) / (math.log(1.05) - math.log(0.95))
    tod = (by[0.95][1] - by[1.05][1]) / (math.log(1.05) - math.log(0.95))
    return {"fwd_skew": -fwd, "today_skew": -tod, "ratio": fwd / tod, "fwd_atm": by[1.0][0], "today_atm": by[1.0][1]}


def dynamics(move: float = -0.05, t: float = 0.25, n: int = 200_000, seed: int = 5, strikes=(90, 95, 100, 105, 110)):
    """The 3-month smile implied by the same local-volatility function before and after a spot move,
    on common random numbers."""
    g = grid()
    out = []
    for s0 in (S0, S0 * (1 + move)):
        st, _ = simulate(g, s0, t, int(round(252 * t)), n, seed)
        row = []
        for k in strikes:
            right = "C" if k >= s0 else "P"
            pay = np.maximum(st - k, 0.0) if right == "C" else np.maximum(k - st, 0.0)
            row.append(implied_vol(float(pay.mean()), s0, k, t, 1.0, right))
        out.append(row)
    return {"strikes": list(strikes), "before": out[0], "after": out[1]}


