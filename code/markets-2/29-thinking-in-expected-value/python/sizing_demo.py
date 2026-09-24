"""Chapter 29 of Book 2: thinking in expected value. The 60% coin of Haghani and Dewey (2016) with
Kelly and fractional Kelly stakes, drawdown probabilities checked by simulation, and the multiple of
Kelly that maximises growth when the edge is estimated from 200 trades."""
import math
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/sizing"))
from firm_sizing import drawdown_probability, fraction_for_drawdown, growth, kelly_fraction, shrinkage, simulate

P_COIN, FLIPS, STAKE, CAP = 0.6, 300, 25.0, 10.0          # cap: USD 250 is ten times the stake
MULTIPLES = (0.25, 0.5, 1.0, 2.0)
P_EDGE, N_EST = 0.55, 200                                   # the weekend problem's trade


def growth_curve(step: float = 0.01) -> list[tuple[float, float]]:
    return [(k * step, growth(k * step, P_COIN)) for k in range(int(0.46 / step) + 1)]


def zero_growth_fraction(p: float = P_COIN) -> float:
    lo, hi = kelly_fraction(p), 0.999
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if growth(mid, p) > 0 else (lo, mid)
    return 0.5 * (lo + hi)


def quantile(xs: list[float], q: float) -> float:
    s = sorted(xs)
    return s[min(int(q * len(s)), len(s) - 1)]


def coin_table(paths: int = 4000) -> list[dict[str, float]]:
    """Per multiple of Kelly: quantiles of final wealth after 300 flips (USD), share below the
    stake, share reaching the cap when there is one."""
    f_star, out = kelly_fraction(P_COIN), []
    for c in MULTIPLES:
        free = [w * STAKE for w, _, _ in simulate(c * f_star, P_COIN, FLIPS, paths, seed=int(100 * c))]
        capped = simulate(c * f_star, P_COIN, FLIPS, paths, seed=int(100 * c) + 1, cap=CAP)
        out.append({"c": c, "f": c * f_star, "p10": quantile(free, 0.1), "median": quantile(free, 0.5),
                    "p90": quantile(free, 0.9), "below": sum(w < STAKE for w in free) / paths,
                    "hit_cap": sum(w >= CAP for w, _, _ in capped) / paths,
                    "growth": growth(c * f_star, P_COIN)})
    return out


def drawdown_table(alpha: float = 0.5, paths: int = 1000) -> list[tuple[float, float, float]]:
    """(multiple of Kelly, theory, simulated share of paths that ever fall to alpha of the start)."""
    f_star = kelly_fraction(P_EDGE)
    out = []
    for c in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5):
        sims = simulate(c * f_star, P_EDGE, 4000, paths, seed=int(100 * c))
        out.append((c, drawdown_probability(c, alpha), sum(low <= alpha for _, low, _ in sims) / paths))
    return out


def uncertain_edge(cs: tuple[float, ...] = tuple(k / 10 for k in range(1, 16)), reps: int = 3000,
                   horizon: int = 500, seed: int = 29) -> list[tuple[float, float]]:
    """(multiple c of the estimated Kelly fraction, mean log growth per trade): each repetition
    estimates the win rate from 200 even-money trades, then stakes c times the estimated Kelly
    fraction for `horizon` trades. Same draws for every c."""
    rng = random.Random(seed)
    draws = []
    for _ in range(reps):
        wins = sum(rng.random() < P_EDGE for _ in range(N_EST))
        draws.append((wins / N_EST, sum(rng.random() < P_EDGE for _ in range(horizon))))
    out = []
    for c in cs:
        total = 0.0
        for p_hat, won in draws:
            f = min(c * kelly_fraction(p_hat), 0.99)
            total += (won * math.log1p(f) + (horizon - won) * math.log1p(-f)) / horizon
        out.append((c, total / reps))
    return out


def problem() -> dict[str, float]:
    mu = 2 * P_EDGE - 1
    s = math.sqrt(1 - mu * mu)
    sharpe = mu / s
    curve = uncertain_edge()
    best = max(curve, key=lambda x: x[1])
    return {"kelly": kelly_fraction(P_EDGE), "mu": mu, "s": s, "sharpe": sharpe, "se": s / math.sqrt(N_EST),
            "t": sharpe * math.sqrt(N_EST), "c_star": shrinkage(N_EST, sharpe), "c_sim": best[0],
            "g_full": dict(curve)[1.0], "g_best": best[1], "g_half": dict(curve)[0.5],
            "c_dd": fraction_for_drawdown(0.5, 0.1), "p_dd_full": drawdown_probability(1.0, 0.5),
            "p_dd_c": drawdown_probability(shrinkage(N_EST, sharpe), 0.5)}
