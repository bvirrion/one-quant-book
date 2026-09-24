"""Credit indices against their constituents, and tranche losses in a large pool (build of Book 2,
Chapter 24).

An index is an equally weighted basket of single-name CDS with one coupon. Its intrinsic upfront is
the weighted average of the constituents' upfronts at that coupon; the skew is the index quote minus
the intrinsic spread. Tranche losses use the one-factor Gaussian model of a large homogeneous pool:
given the common factor Z, the pool loses (1 - R) N((N^-1(p) - sqrt(rho) Z) / sqrt(1 - rho)) of its
notional, with p the default probability to the horizon and rho the correlation of the names.
"""
import math
import random
from statistics import NormalDist

N = NormalDist()


def intrinsic_upfront(upfronts: list[float], weights: list[float] | None = None) -> float:
    """Upfront of the index implied by its constituents' upfronts at the index coupon."""
    w = weights or [1.0 / len(upfronts)] * len(upfronts)
    return sum(wi * u for wi, u in zip(w, upfronts, strict=True))


def annuity_weighted_spread(spreads: list[float], annuities: list[float]) -> float:
    """First-order intrinsic spread: names that are likelier to default carry smaller annuities."""
    return sum(s * a for s, a in zip(spreads, annuities, strict=True)) / sum(annuities)


def skew_pnl(notional: float, upfront_entry: float, upfront_exit: float) -> float:
    """P&L of buying index protection (upfront paid at entry, received back at exit) when the
    constituents' side of the trade does not move."""
    return notional * (upfront_exit - upfront_entry)


# ---- tranches ------------------------------------------------------------------------------------

def tranche_loss(pool_loss: float, attach: float, detach: float) -> float:
    """Loss of a tranche as a fraction of its own notional, for a pool loss fraction."""
    return min(max(pool_loss - attach, 0.0), detach - attach) / (detach - attach)


def pool_loss_given_z(z: float, p: float, rho: float, recovery: float) -> float:
    return (1.0 - recovery) * N.cdf((N.inv_cdf(p) - math.sqrt(rho) * z) / math.sqrt(1.0 - rho))


def expected_tranche_loss(attach: float, detach: float, p: float, rho: float, recovery: float = 0.40,
                          n: int = 2001) -> float:
    """E[tranche loss] / tranche notional in the large pool, by the trapezoid rule over z in [-8, 8]."""
    h, total = 16.0 / (n - 1), 0.0
    for k in range(n):
        z = -8.0 + k * h
        f = tranche_loss(pool_loss_given_z(z, p, rho, recovery), attach, detach) * N.pdf(z)
        total += f * (0.5 if k in (0, n - 1) else 1.0)
    return total * h


def base_correlation(detach: float, target: float, p: float, recovery: float = 0.40) -> float:
    """Correlation at which the base tranche [0, detach] has expected loss `target` (decreasing in rho)."""
    lo, hi = 1e-4, 0.999
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if expected_tranche_loss(0.0, detach, p, mid, recovery) > target else (lo, mid)
    return 0.5 * (lo + hi)


def simulate_pool(names: int, p: float, rho: float, recovery: float, trials: int, seed: int) -> list[float]:
    """Pool loss fractions of a finite pool of equal names in the same one-factor model."""
    rng, c, out = random.Random(seed), N.inv_cdf(p), []
    a, b = math.sqrt(rho), math.sqrt(1.0 - rho)
    for _ in range(trials):
        z = rng.gauss(0.0, 1.0)
        defaults = sum(1 for _ in range(names) if a * z + b * rng.gauss(0.0, 1.0) < c)
        out.append((1.0 - recovery) * defaults / names)
    return out
