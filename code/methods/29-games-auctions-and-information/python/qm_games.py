"""Book 4, chapter 29: games, auctions and information (teaching module).

A zero-sum game solved by multiplicative weights; the first-price auction as a Bayesian game and its best responses;
revenue equivalence across four formats; reserve prices; uniform-price against pay-as-bid multi-unit auctions (the
Treasury's switch); the winner's curse; and Kelly betting on a horse race with a noisy tip, where the growth gain
equals the mutual information.
"""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT / "code" / "firm" / "bidding"))
from firm_bidding import (  # noqa: E402
    common_value,
    expected_revenue_uniform,
    fp_bid,
    fp_bid_general,
    myerson_reserve,
    pab_bid,
    simulate,
    simulate_multiunit,
)

RPS = np.array([[0.0, -1.0, 2.0], [1.0, 0.0, -1.0], [-2.0, 1.0, 0.0]])   # weighted rock-paper-scissors


def multiplicative_weights(A: np.ndarray, T: int = 20_000, eta: float | None = None) -> dict:
    """Both players of the zero-sum game A (row maximises x'Ay) run multiplicative weights; the time-averaged
    strategies approach a saddle point. Returns the averages and the duality gap max_j (x'A)_j - min_i (Ay)_i."""
    m, k = A.shape
    eta = eta or math.sqrt(math.log(max(m, k)) / T)
    wx, wy = np.zeros(m), np.zeros(k)
    sx, sy = np.zeros(m), np.zeros(k)
    for _ in range(T):
        x = np.exp(wx - wx.max())
        x /= x.sum()
        y = np.exp(wy - wy.max())
        y /= y.sum()
        sx += x
        sy += y
        wx += eta * (A @ y)
        wy -= eta * (A.T @ x)
    xb, yb = sx / T, sy / T
    return {"x": xb, "y": yb, "value": float(xb @ A @ yb), "gap": float((A @ yb).max() - (xb @ A).min())}


def best_response_curve(v: float = 0.8, n: int = 5, n_bids: int = 81) -> dict:
    """Expected payoff (v - b) P(win) of a bidder with value v against n - 1 rivals bidding fp_bid: rivals' bids
    are below b with probability (b n/(n-1))^(n-1) for b <= (n-1)/n."""
    b = np.linspace(0.0, 0.8, n_bids)
    p_win = np.minimum(b * n / (n - 1), 1.0) ** (n - 1)
    pay = (v - b) * p_win
    return {"b": b, "payoff": pay, "best": float(b[pay.argmax()]), "eq": float(fp_bid(v, n))}


def equivalence(n: int = 5, n_auctions: int = 1_000_000, seed: int = 29, tick: float = 0.01) -> dict:
    out = {}
    for fmt in ("first", "second", "english", "dutch"):
        r = simulate(fmt, n, n_auctions, seed, increment=tick if fmt in ("english", "dutch") else 0.0)
        out[fmt] = (r["revenue"], r["revenue_se"], r["shading"])
    out["theory"] = (n - 1) / (n + 1)
    return out


def reserve_curve(ns=(2, 5), n_points: int = 51) -> dict:
    r = np.linspace(0.0, 1.0, n_points)
    return {"r": r, **{n: np.array([expected_revenue_uniform(n, x) for x in r]) for n in ns}}


def reserve_gain(n: int, seed: int = 31, n_auctions: int = 1_000_000) -> dict:
    rstar = myerson_reserve(lambda x: x, lambda x: 1.0)
    sim = simulate("second", n, n_auctions, seed, reserve=rstar)
    sim0 = simulate("second", n, n_auctions, seed)
    return {"rstar": rstar, "with": expected_revenue_uniform(n, rstar), "without": expected_revenue_uniform(n, 0.0),
            "sim_with": sim["revenue"], "sim_without": sim0["revenue"], "unsold": 1 - sim["sold"]}


def treasury_switch(n: int = 5, k: int = 2, n_auctions: int = 400_000, seed: int = 1998) -> dict:
    u = simulate_multiunit("uniform", n, k, n_auctions, seed)
    p = simulate_multiunit("payasbid", n, k, n_auctions, seed)
    return {"uniform": u, "payasbid": p, "theory": k * (n - k) / (n + 1),
            "pab_bid_at": {v: float(pab_bid(v, n, k)[0]) for v in (0.5, 0.8, 1.0)}}


def nonuniform_shading(n: int = 5) -> dict:
    """Equilibrium bid for values with cdf F(v) = v^2 (more high values): the general formula against the closed form
    b(v) = v (2n - 2)/(2n - 1)."""
    v = np.array([0.3, 0.6, 0.9])
    return {"numeric": fp_bid_general(v, n, lambda x: np.asarray(x) ** 2), "closed": v * (2 * n - 2) / (2 * n - 1)}


def winners_curse(n: int = 5, noise: float = 0.1, n_auctions: int = 400_000, seed: int = 7) -> dict:
    naive = common_value(n, n_auctions, seed, noise=noise, shade=0.0)
    adjusted = common_value(n, n_auctions, seed, noise=noise, shade=noise * (n - 1) / (n + 1))
    return {"naive": naive, "adjusted": adjusted, "expected_max_error": noise * (n - 1) / (n + 1)}


# --- information and betting -------------------------------------------------------------------------------

P_RACE = np.array([0.4, 0.3, 0.2, 0.1])
ODDS = np.array([2.2, 3.0, 4.5, 9.0])       # decimal odds: a unit stake on the winner returns this amount


def entropy(p) -> float:
    p = np.asarray(p, dtype=float)
    p = p[p > 0]
    return float(-(p * np.log2(p)).sum())


def joint_tip(q: float, p=P_RACE) -> np.ndarray:
    """P(X = x, Y = y): the tip names the winner with probability q, otherwise one of the others at random."""
    m = len(p)
    J = np.zeros((m, m))
    for x in range(m):
        for y in range(m):
            J[x, y] = p[x] * (q if x == y else (1 - q) / (m - 1))
    return J


def mutual_information(J: np.ndarray) -> float:
    px, py = J.sum(axis=1), J.sum(axis=0)
    mask = J > 0
    return float((J[mask] * np.log2(J[mask] / np.outer(px, py)[mask])).sum())


def kelly_growth(q: float, p=P_RACE, odds=ODDS) -> dict:
    """Doubling rates (bits per race) of proportional betting b = p(x) without the tip and b = p(x | y) with it."""
    J = joint_tip(q, p)
    w0 = float((p * np.log2(p * odds)).sum())
    py = J.sum(axis=0)
    w1 = float(sum(J[x, y] * math.log2(J[x, y] / py[y] * odds[x]) for x in range(len(p)) for y in range(len(p))
                   if J[x, y] > 0))
    return {"without": w0, "with": w1, "gain": w1 - w0, "mi": mutual_information(J), "hx": entropy(p)}


def simulate_races(q: float, n_races: int = 200_000, seed: int = 56, p=P_RACE, odds=ODDS) -> dict:
    rng = np.random.default_rng(seed)
    m = len(p)
    X = rng.choice(m, size=n_races, p=p)
    correct = rng.uniform(size=n_races) < q
    other = (X + rng.integers(1, m, size=n_races)) % m
    Y = np.where(correct, X, other)
    J = joint_tip(q, p)
    post = J / J.sum(axis=0)
    g0 = np.log2(p[X] * odds[X])
    g1 = np.log2(post[X, Y] * odds[X])
    return {"without": float(g0.mean()), "with": float(g1.mean()), "gain": float((g1 - g0).mean()),
            "gain_se": float((g1 - g0).std(ddof=1) / math.sqrt(n_races))}
