"""One-period markets: state prices, price bounds, arbitrage portfolios (Book 5, Chapter 1).

A market is a payoff matrix D (states x assets) and a price vector p. State prices q >= 0 solve
D^T q = p; they exist and can be taken strictly positive exactly when there is no arbitrage. In an
incomplete market the set of state-price vectors is a polytope whose vertices give the bounds of
the no-arbitrage price interval of any claim.
"""
import itertools
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/arbcheck"))
sys.path.insert(0, str(ROOT / "code/firm/parity"))
from firm_arbcheck import Quote, box_cost, box_rate, check_box, lp_max  # noqa: E402
from firm_parity import price as black  # noqa: E402

# The chapter's markets: a bond paying 1 (price 0.98) and a share at 100.
BOND = 0.98
BINOMIAL = np.array([[1.0, 120.0], [1.0, 90.0]])                 # rows: states up, down
TRINOMIAL = np.array([[1.0, 120.0], [1.0, 100.0], [1.0, 80.0]])   # rows: states up, middle, down
PRICES = np.array([BOND, 100.0])


def state_prices(d: np.ndarray, p: np.ndarray) -> np.ndarray:
    """Complete market (square, invertible D): the unique state-price vector."""
    return np.linalg.solve(d.T, p)


def state_price_vertices(d: np.ndarray, p: np.ndarray, tol: float = 1e-12) -> list[np.ndarray]:
    """Vertices of {q >= 0 : D^T q = p}: basic solutions with at most (number of assets) non-zeros."""
    n_states, n_assets = d.shape
    out = []
    for support in itertools.combinations(range(n_states), n_assets):
        sub = d[list(support)].T
        if abs(np.linalg.det(sub)) < 1e-12:
            continue
        qs = np.linalg.solve(sub, p)
        if np.all(qs >= -tol):
            q = np.zeros(n_states)
            q[list(support)] = qs
            out.append(q)
    return out


def price_bounds(d: np.ndarray, p: np.ndarray, g: np.ndarray) -> tuple[float, float]:
    """No-arbitrage bounds of a claim with payoff g: min and max of q.g over state-price vectors."""
    vals = [float(q @ g) for q in state_price_vertices(d, p)]
    return min(vals), max(vals)


def superreplication(d: np.ndarray, p: np.ndarray, g: np.ndarray, box: float = 1e4):
    """Cheapest portfolio theta with D theta >= g: (cost, theta). Its cost is the upper bound."""
    n = d.shape[1]
    a = np.vstack([-d, np.eye(n), -np.eye(n)])
    b = np.concatenate([-g, box * np.ones(n), box * np.ones(n)])
    val, theta = lp_max(-p, a, b)
    return -val, theta


def find_arbitrage(d: np.ndarray, p: np.ndarray, bounds, eps: float = 1e-6):
    """Maximise the cash received today, -p.theta (plus eps times the total payoff, which picks up
    zero-cost arbitrages), over portfolios with D theta >= 0 and |theta_i| <= bounds[i].

    The optimum is positive exactly when an arbitrage exists; theta is then an arbitrage portfolio."""
    n = d.shape[1]
    c = -p + eps * d.sum(axis=0)
    a = np.vstack([-d, np.eye(n), -np.eye(n)])
    b = np.concatenate([np.zeros(d.shape[0]), bounds, bounds])
    val, theta = lp_max(c, a, b)
    return float(-p @ theta), theta


def call_payoff(strikes_states: np.ndarray, k: float) -> np.ndarray:
    return np.maximum(strikes_states - k, 0.0)


# ---------------------------------------------------------------- the box-spread problem
YEARS, FWD, RATE = 1.0, 5850.0, 0.0420       # illustrative index level and rate
K1, K2 = 5000.0, 6000.0
TICK, HALF_WIDTH = 0.10, 0.80                # quotes 1.60 wide, on a 0.10 grid (illustrative)
OVERNIGHT = 0.0400                           # the problem's compounded overnight rate over the year


def _vol(k: float) -> float:
    return 0.18 - 0.25 * math.log(k / FWD)


def box_chain() -> dict[tuple[str, float], Quote]:
    """Four quotes built from a smile and Black's formula, rounded to the tick, 1.60 wide."""
    out = {}
    for k in (K1, K2):
        for right in ("C", "P"):
            mid = round(black(FWD, k, YEARS, RATE, _vol(k), right) / TICK) * TICK
            out[(right, k)] = Quote(k, right, round(mid - HALF_WIDTH, 2), round(mid + HALF_WIDTH, 2))
    return out


def box_results() -> dict[str, float]:
    q = box_chain()
    width = K2 - K1
    buy, sell = box_cost(q, K1, K2, True), box_cost(q, K1, K2, False)
    mid = 0.5 * (buy + sell)
    r_lend, r_borrow, r_mid = box_rate(buy, width, YEARS), box_rate(sell, width, YEARS), box_rate(mid, width, YEARS)
    return {"buy": buy, "sell": sell, "mid": mid, "r_lend": r_lend, "r_borrow": r_borrow, "r_mid": r_mid,
            "lend_spread_bp": (r_lend - OVERNIGHT) * 1e4, "borrow_spread_bp": (r_borrow - OVERNIGHT) * 1e4,
            "notional_usd": width * 100.0, "interest_usd_lend": (width - buy) * 100.0,
            "violations_fair": len(check_box(q, K1, K2, math.exp(-OVERNIGHT * YEARS)))}
