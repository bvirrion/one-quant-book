"""Position sizing by expected log growth: Kelly, fractional Kelly, drawdowns and an uncertain edge
(build of Book 2, Chapter 29).

A bet wins b per unit staked with probability p and loses the stake otherwise. Staking a fraction f
of wealth each time grows wealth at the rate g(f) = p ln(1 + f b) + q ln(1 - f) per bet; the Kelly
fraction maximises it. For small, frequent bets with mean mu and variance s2 per unit staked, g(f) is
close to f mu - f^2 s2 / 2, maximised at mu / s2; staking c times that fraction, wealth ever falls
to a fraction alpha of its starting value with probability alpha ** (2 / c - 1).
"""
import math
import random


def kelly_fraction(p: float, b: float = 1.0) -> float:
    """Fraction of wealth to stake on a bet paying b to 1 that wins with probability p (0 if no edge)."""
    return max(p - (1 - p) / b, 0.0)


def growth(f: float, p: float, b: float = 1.0) -> float:
    """Expected log growth of wealth per bet when staking a fraction f."""
    if f >= 1.0:
        return -math.inf
    return p * math.log1p(f * b) + (1 - p) * math.log1p(-f)


def simulate(f: float, p: float, n: int, paths: int, seed: int, b: float = 1.0,
             cap: float = math.inf) -> list[tuple[float, float, float]]:
    """(final wealth, lowest wealth, largest drawdown from a peak) per path, from wealth 1; betting
    stops if wealth reaches `cap`."""
    rng, out = random.Random(seed), []
    for _ in range(paths):
        w, low, peak, dd = 1.0, 1.0, 1.0, 0.0
        for _ in range(n):
            if w >= cap:
                break
            stake = f * w
            w += stake * b if rng.random() < p else -stake
            low, peak = min(low, w), max(peak, w)
            dd = max(dd, 1 - w / peak)
        out.append((min(w, cap), low, dd))
    return out


def drawdown_probability(c: float, alpha: float) -> float:
    """Probability that wealth ever falls to alpha times its starting value when staking c times
    Kelly (continuous-time approximation)."""
    return alpha ** (2 / c - 1)


def fraction_for_drawdown(alpha: float, delta: float) -> float:
    """Largest multiple of Kelly that keeps the probability of ever falling to alpha of the start
    below delta."""
    return 2 / (1 + math.log(delta) / math.log(alpha))


def shrinkage(n: int, sharpe: float) -> float:
    """Multiple of the estimated Kelly fraction that maximises expected growth when the edge is
    estimated from n trades with per-trade Sharpe ratio `sharpe`."""
    return n * sharpe ** 2 / (n * sharpe ** 2 + 1)


def growth_uncertain(c: float, mu: float, s: float, n: int) -> float:
    """Expected growth per trade (quadratic approximation) when staking c * mu_hat / s^2, mu_hat
    estimated from n trades."""
    se2 = s * s / n
    return c * mu * mu / (s * s) - c * c * (mu * mu + se2) / (2 * s * s)
