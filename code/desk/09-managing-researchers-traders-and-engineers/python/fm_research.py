"""One Quant Book 16, chapter 9: choosing research projects and attributing credit (illustrative).

Credit: three researchers' daily signals over ten years. A's and B's are correlated at 0.8 (two routes to the same
effect); C's is independent. The target is next-day return; the combined forecast is the least-squares fit, and its
P&L is scaled so that the three together made $30 million.

Projects: twelve candidate projects with costs ($ million), probabilities of success and values; three overlap the
firm's existing book. A budget of $10 million.
"""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/projsel"))
sys.path.insert(0, str(ROOT / "code/firm/multitest"))
import firm_multitest as mt  # noqa: E402
import firm_projsel as ps  # noqa: E402

TOTAL = 30.0
NAMES = ("A", "B", "C")


def signals(days=2520, seed=10):
    rng = np.random.default_rng(seed)
    z = rng.standard_normal((days, 3))
    a = z[:, 0]
    b = 0.8 * a + 0.6 * z[:, 1]
    c = z[:, 2]
    s = np.c_[a, b, c]
    y = 0.05 * a + 0.05 * b + 0.06 * c + rng.standard_normal(days)
    return s, y


def credit(days=2520, seed=10):
    s, y = signals(days, seed)
    v0 = ps.game(s, y)
    scale = TOTAL / v0(frozenset(range(3)))

    def v(S):
        return scale * v0(S)
    loo = ps.leave_one_out(v, 3)
    sh = ps.shapley(v, 3)
    orders = {"".join(NAMES[i] for i in o): ps.ordered(v, o) for o in ((0, 1, 2), (1, 0, 2), (2, 0, 1))}
    alone = np.array([v({i}) for i in range(3)])
    rho = float(np.corrcoef(s[:, 0], s[:, 1])[0, 1])
    return {"loo": loo, "shapley": sh, "orders": orders, "alone": alone, "corr_ab": rho}


PROJECTS = [
    ps.Project("new futures signal", 1.5, 0.30, 12.0),
    ps.Project("options flow features", 2.0, 0.20, 15.0),
    ps.Project("execution model v2", 1.0, 0.60, 4.0),
    ps.Project("alternative data trial", 2.5, 0.10, 20.0),
    ps.Project("second momentum variant", 1.0, 0.40, 6.0, 0.7),
    ps.Project("risk model upgrade", 1.5, 0.70, 3.0),
    ps.Project("crypto basis book", 3.0, 0.25, 18.0),
    ps.Project("cross-asset carry", 2.0, 0.35, 9.0, 0.5),
    ps.Project("intraday reversal refit", 0.5, 0.50, 2.0, 0.4),
    ps.Project("news text model", 3.0, 0.15, 16.0),
    ps.Project("borrow-cost signal", 1.0, 0.30, 5.0),
    ps.Project("auction imbalance model", 1.5, 0.45, 7.0),
]
BUDGET = 10.0


def portfolio(n=20_000, seed=19):
    rng = np.random.default_rng(seed)
    greedy = ps.select(PROJECTS, BUDGET)
    g = np.array([ps.simulate_year(greedy, rng) for _ in range(n)])
    r = np.array([ps.simulate_year(ps.select_random(PROJECTS, BUDGET, rng), rng) for _ in range(n)])
    return {"chosen": [x.name for x in greedy], "cost": sum(x.cost for x in greedy),
            "expected": sum(ps.expected_net(x) for x in greedy), "greedy_mean": float(g.mean()),
            "greedy_p_loss": float((g < 0).mean()), "random_mean": float(r.mean()),
            "random_p_loss": float((r < 0).mean())}


def deflated(sr_annual=1.2, years=5, trials=40, sr_var_annual=0.25):
    """Probability that the true Sharpe ratio exceeds zero (one trial) and exceeds the expected best of `trials`
    unrelated trials (deflated), for a five-year daily backtest with annual Sharpe ratio sr_annual."""
    n = years * 252
    sr = sr_annual / math.sqrt(252)
    v = sr_var_annual / 252
    return {"psr": mt.deflated_sharpe(sr, n), "dsr": mt.deflated_sharpe(sr, n, sr0=mt.expected_max_sr(trials, v)),
            "sr0_annual": mt.expected_max_sr(trials, v) * math.sqrt(252)}


def pool_split(pool=6.0):
    """A bonus pool of 6 ($ million, 20 per cent of the 30) split by each rule, normalised to the pool."""
    c = credit()
    out = {}
    for k, x in (("leave-one-out", c["loo"]), ("Shapley", c["shapley"]), ("order ABC", c["orders"]["ABC"])):
        out[k] = pool * x / x.sum()
    return out


def portfolio_samples(n=20_000, seed=19):
    rng = np.random.default_rng(seed)
    greedy = ps.select(PROJECTS, BUDGET)
    g = np.array([ps.simulate_year(greedy, rng) for _ in range(n)])
    r = np.array([ps.simulate_year(ps.select_random(PROJECTS, BUDGET, rng), rng) for _ in range(n)])
    return g, r


def dsr_curve(trials=(1, 2, 5, 10, 20, 40, 100, 200, 500)):
    return [(t, deflated(trials=t)["dsr"]) for t in trials]
