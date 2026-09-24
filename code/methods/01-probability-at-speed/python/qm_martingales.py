"""Chapter 1 of Book 4: probability at speed.

The Doob martingale of the five-card game of Book 2, chapter 30, a forecaster that under-reacts,
the closing-price forecast of the weekend problem, optional stopping for a take-profit / stop-loss
rule, and a change of measure that estimates a far tail."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/mgtest"))
from firm_mgtest import revision_regression, variance_shares

DECK = np.repeat(np.arange(1, 14), 4)          # aces 1 ... kings 13, four suits
N_CARDS = 5


# --- the card game -------------------------------------------------------------------------
def card_forecasts(n_deals: int, seed: int = 1) -> np.ndarray:
    """Doob martingale M_k = E[sum of 5 cards | first k revealed], k = 0..5, one row per deal."""
    rng = np.random.default_rng(seed)
    total, size = DECK.sum(), DECK.size
    out = np.empty((n_deals, N_CARDS + 1))
    for i in range(n_deals):
        cards = rng.choice(DECK, N_CARDS, replace=False)
        s = np.concatenate([[0], np.cumsum(cards)])
        k = np.arange(N_CARDS + 1)
        out[i] = s + (N_CARDS - k) * (total - s) / (size - k)
    return out


def underreacting(m: np.ndarray, a: float) -> np.ndarray:
    """A forecaster that moves only a fraction a of the way from the prior mean, until the end."""
    f = m[:, :1] + a * (m - m[:, :1])
    f[:, -1] = m[:, -1]
    return f


def card_table(n_deals: int = 20_000, a: float = 0.6, seed: int = 1) -> dict:
    m = card_forecasts(n_deals, seed)
    f = underreacting(m, a)
    dm, df = np.diff(m, axis=1), np.diff(f, axis=1)
    return {
        "m0": m[0, 0],
        "honest_mean": float(dm.mean()),
        "honest_corr": float(np.corrcoef(dm[:, 1:].ravel(), dm[:, :-1].ravel())[0, 1]),
        "honest_slope": revision_regression(m, col=N_CARDS - 1)["slope"],
        "under_mean": float(df.mean()),
        "under_slope": revision_regression(f, col=N_CARDS - 1)["slope"],
        "under_t": revision_regression(f, col=N_CARDS - 1)["t"],
        "theory_slope": (1 - a) / a,
    }


# --- the closing-price forecast (weekend problem) ----------------------------------------------
S0, SIG_DAY, S_J = 100.0, 1.80, 0.30           # dollars: price, daily sd, sd of the imbalance news
MINUTES, T_IMB = 390, 380                      # 09:30-16:00; imbalance published at 15:50


def close_variances(sig_day: float = SIG_DAY, s_j: float = S_J, late_mult: float = 1.0) -> dict:
    """Variance of the close and the parts resolved before and after 15:50.

    late_mult scales the per-minute variance of the last ten minutes (U-shaped days)."""
    w = np.ones(MINUTES)
    w[T_IMB:] = late_mult
    per_min = sig_day**2 / w.sum() * w          # keeps the day's diffusive variance at sig_day^2
    before = float(per_min[:T_IMB].sum())
    after = float(per_min[T_IMB:].sum()) + s_j**2
    total = before + after
    return {"total": total, "before": before, "after": after, "share_after": after / total,
            "share_jump": s_j**2 / total, "per_min": per_min}


NEWS = T_IMB + 1                               # column of the forecast just after the 15:50 news


def close_paths(n_days: int, seed: int = 2, late_mult: float = 1.0, lag_frac: float = 0.0) -> np.ndarray:
    """Forecast paths M = E[close | information], row per day, 392 columns: minutes 0..380 (09:30
    to 15:50, before the news), then just after the 15:50 news (column NEWS), then minutes 381..390.

    With lag_frac > 0 the forecaster adds only (1 - lag_frac) of the imbalance news at 15:50 and
    the rest at the close: an inefficient forecast."""
    v = close_variances(late_mult=late_mult)
    rng = np.random.default_rng(seed)
    inc = rng.standard_normal((n_days, MINUTES)) * np.sqrt(v["per_min"])
    jump = rng.standard_normal(n_days) * S_J
    walk = np.hstack([np.full((n_days, 1), S0), S0 + np.cumsum(inc, axis=1)])   # minutes 0..390
    path = np.insert(walk, NEWS, walk[:, T_IMB], axis=1)
    path[:, NEWS:] += (1 - lag_frac) * jump[:, None]
    path[:, -1] += lag_frac * jump
    return path


def problem() -> dict:
    v = close_variances()
    u = close_variances(late_mult=3.0)
    per_min = SIG_DAY**2 / MINUTES
    noon = 150                                  # 12:00 is 150 minutes after 09:30
    # Part III: half of the news at 15:50, the rest at the close
    d1_var = (S_J / 2) ** 2
    d2_var = (S_J / 2) ** 2 + 10 * per_min
    corr = (S_J / 2) ** 2 / math.sqrt(d1_var * d2_var)
    cols = [0, T_IMB, NEWS, MINUTES + 1]        # open, 15:50 before the news, after it, close
    sim = close_paths(20_000, seed=3, lag_frac=0.5)
    reg = revision_regression(sim[:, cols], col=2)
    honest = close_paths(20_000, seed=4)
    shares = variance_shares(honest[:, cols])
    return {
        "var_total": v["total"], "sd_total": math.sqrt(v["total"]),
        "share_noon": noon * per_min / v["total"],
        "share_after": v["share_after"], "share_jump": v["share_jump"],
        "p_move_14c": 2 * (1 - 0.5 * (1 + math.erf(0.14 / S_J / math.sqrt(2)))),
        "edge_per_share": 0.5 * S_J * math.sqrt(2 / math.pi),
        "corr_revisions": corr, "days_for_t2": 4 * (1 - corr**2) / corr**2 + 1,   # t = r sqrt(n-1) / sqrt(1-r^2)
        "sim_slope": reg["slope"], "sim_t": reg["t"],
        "sim_share_after": float(shares[1:].sum()),
        "share_after_ushape": u["share_after"],
    }


# --- optional stopping: take profit at +a, stop loss at -b ------------------------------------
def hit_up_probability(a: int, b: int, p: float = 0.5) -> float:
    """P(a +-1 random walk from 0 reaches +a before -b), up-probability p."""
    if p == 0.5:
        return b / (a + b)
    r = (1 - p) / p                              # (q/p)^{X_n} is a martingale
    return (1 - r**b) / (1 - r ** (a + b))


def simulate_hits(a: int, b: int, p: float, n: int, seed: int = 5) -> tuple[float, float]:
    """Monte Carlo frequency of reaching +a first, and the mean number of steps."""
    rng = np.random.default_rng(seed)
    x = np.zeros(n, dtype=int)
    alive = np.ones(n, dtype=bool)
    steps = np.zeros(n, dtype=int)
    while alive.any():
        idx = np.flatnonzero(alive)
        x[idx] += np.where(rng.random(idx.size) < p, 1, -1)
        steps[idx] += 1
        alive[idx] = (x[idx] < a) & (x[idx] > -b)
    return float(np.mean(x >= a)), float(steps.mean())


def stop_table(a: int = 10, p_values=(0.5, 0.49), n: int = 20_000) -> list[tuple]:
    rows = []
    for b in (2, 4, 6, 8, 10, 12, 14, 16, 18, 20):
        row = [b]
        for i, p in enumerate(p_values):
            row += [hit_up_probability(a, b, p), simulate_hits(a, b, p, n, seed=10 * b + i)[0]]
        rows.append(tuple(row))
    return rows


# --- a change of measure that sees the far tail --------------------------------------------------
def tail_estimates(c: float = 4.0, n: int = 100_000, seed: int = 6) -> dict:
    """P(X > c) for X ~ N(0,1): plain Monte Carlo and under the measure that shifts the mean to c,
    reweighted by the Radon-Nikodym derivative dP/dQ = exp(-c X + c^2 / 2)."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(n)
    plain = (z > c).astype(float)
    y = z + c                                   # a sample from Q, under which X ~ N(c, 1)
    w = np.exp(-c * y + 0.5 * c * c) * (y > c)
    exact = 0.5 * math.erfc(c / math.sqrt(2))
    return {"exact": exact, "plain": plain.mean(), "plain_se": plain.std() / math.sqrt(n),
            "tilted": w.mean(), "tilted_se": w.std() / math.sqrt(n)}
