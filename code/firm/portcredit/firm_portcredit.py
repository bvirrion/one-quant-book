"""Portfolio credit: copulas, loss distributions and tranches (build of One Quant Book 6, chapter 15).

Names i = 1..n with flat hazards lambda_i, equal notionals and one recovery. One-factor Gaussian copula:
name i defaults by t if sqrt(rho) Z + sqrt(1 - rho) eps_i < N^{-1}(1 - Q_i(t)). Conditional on Z the
names are independent; the number of defaults follows by the standard recursion over names, and the
loss distribution by Gauss-Hermite quadrature over Z. Tranches [a, d] are priced from expected tranche
losses on the quarterly premium grid (premium on the outstanding tranche notional, protection at the
period end), at one correlation (compound) or at the two base correlations of [0, a] and [0, d].
A Student-t copula (mixing variable W = nu / chi2_nu) is simulated through the conditional binomial.
Book 2's `firm_tranche` (large homogeneous pool, one period) is the limiting case and is imported.
"""
import math
import pathlib
import sys
from dataclasses import dataclass
from functools import lru_cache
from statistics import NormalDist

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "tranche"))
from firm_tranche import expected_tranche_loss as lhp_expected_tranche_loss  # noqa: E402,F401

ND = NormalDist()
_Z, _W = np.polynomial.hermite_e.hermegauss(64)
_W = _W / math.sqrt(2.0 * math.pi)


def ncdf(x) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    return np.fromiter(map(math.erfc, (-x / math.sqrt(2.0)).ravel()), float, x.size).reshape(x.shape) * 0.5


def conditional_pd(p: np.ndarray, rho: float, z: np.ndarray) -> np.ndarray:
    """P(default by t | Z = z) for unconditional probabilities p (names) at nodes z: shape (len(z), len(p))."""
    c = np.array([ND.inv_cdf(min(max(x, 1e-15), 1 - 1e-15)) for x in np.atleast_1d(p)])
    return ncdf((c[None, :] - math.sqrt(rho) * np.asarray(z)[:, None]) / math.sqrt(1.0 - rho))


def default_count_given_z(pz: np.ndarray) -> np.ndarray:
    """Distribution of the number of defaults for each z row of independent default probabilities."""
    nz, n = pz.shape
    dist = np.zeros((nz, n + 1))
    dist[:, 0] = 1.0
    for i in range(n):
        q = pz[:, i:i + 1]
        dist[:, 1:] = dist[:, 1:] * (1 - q) + dist[:, :-1] * q
        dist[:, 0] *= 1 - q[:, 0]
    return dist


def loss_distribution(p: np.ndarray, rho: float) -> np.ndarray:
    """Unconditional distribution of the number of defaults (Gaussian copula, quadrature over Z)."""
    return _W @ default_count_given_z(conditional_pd(p, rho, _Z))


def tranche_loss_fraction(k: np.ndarray, n: int, recovery: float, a: float, d: float) -> np.ndarray:
    pool = (1.0 - recovery) * k / n
    return np.clip(pool - a, 0.0, d - a) / (d - a)


@dataclass
class Pool:
    hazards: np.ndarray        # flat hazard per name
    recovery: float = 0.40

    @property
    def n(self) -> int:
        return len(self.hazards)

    def pd(self, t: float) -> np.ndarray:
        return 1.0 - np.exp(-self.hazards * t)


@lru_cache(maxsize=4096)
def _count_paths(hazards: tuple, rho: float, maturity: float, freq: int) -> np.ndarray:
    """Distribution of the number of defaults at each premium date (rows), cached per pool and rho."""
    h = np.array(hazards)
    return np.array([loss_distribution(1.0 - np.exp(-h * j / freq), rho)
                     for j in range(1, round(maturity * freq) + 1)])


def expected_tranche_losses(pool: Pool, rho: float, a: float, d: float, maturity: float = 5.0,
                            freq: int = 4) -> np.ndarray:
    """E[tranche loss fraction] at each premium date (0 at t = 0 included)."""
    tl = tranche_loss_fraction(np.arange(pool.n + 1), pool.n, pool.recovery, a, d)
    paths = _count_paths(tuple(pool.hazards.tolist()), float(rho), float(maturity), int(freq))
    return np.concatenate([[0.0], paths @ tl])


def legs_from_el(el: np.ndarray, r: float, freq: int = 4) -> tuple[float, float]:
    """(risky annuity of the tranche, protection leg) per unit tranche notional, flat rate r."""
    ann = prot = 0.0
    for j in range(1, len(el)):
        df = math.exp(-r * j / freq)
        ann += df / freq * (1.0 - 0.5 * (el[j - 1] + el[j]))
        prot += df * (el[j] - el[j - 1])
    return ann, prot


def base_el(pool: Pool, rho_a: float, rho_d: float, a: float, d: float, maturity: float = 5.0) -> np.ndarray:
    """Expected loss path of [a, d] from the base tranches [0, a] at rho_a and [0, d] at rho_d."""
    eld = expected_tranche_losses(pool, rho_d, 0.0, d, maturity) * d
    ela = expected_tranche_losses(pool, rho_a, 0.0, a, maturity) * a if a > 0 else 0.0
    return (eld - ela) / (d - a)


def tranche_price(el: np.ndarray, r: float, running: float) -> dict:
    """Par spread, and upfront (paid by the protection buyer) at a running coupon, per unit notional."""
    ann, prot = legs_from_el(el, r)
    return {"par": prot / ann, "upfront": prot - running * ann, "annuity": ann, "protection": prot}


def compound_correlations(pool: Pool, target: float, a: float, d: float, r: float, running: float,
                          grid: int = 48, quote: str = "par") -> list[float]:
    """All correlations at which the tranche's `quote` ('par' or 'upfront') equals target (may be none or two)."""
    rhos = np.linspace(0.01, 0.95, grid)
    vals = [tranche_price(expected_tranche_losses(pool, float(x), a, d), r, running)[quote] - target for x in rhos]
    roots = []
    for i in range(grid - 1):
        if vals[i] == 0 or vals[i] * vals[i + 1] < 0:
            lo, hi, flo = float(rhos[i]), float(rhos[i + 1]), vals[i]
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                fm = tranche_price(expected_tranche_losses(pool, mid, a, d), r, running)[quote] - target
                lo, hi, flo = (mid, hi, fm) if fm * flo > 0 else (lo, mid, flo)
            roots.append(0.5 * (lo + hi))
    return roots


def t_cdf(x: float, nu: float) -> float:
    """Student-t CDF by Simpson integration of the density (no scipy)."""
    c = math.exp(math.lgamma((nu + 1) / 2) - math.lgamma(nu / 2)) / math.sqrt(nu * math.pi)
    m, h = 2000, abs(x) / 2000
    f = [c * (1 + (k * h) ** 2 / nu) ** (-(nu + 1) / 2) for k in range(m + 1)]
    s = h / 3 * (f[0] + f[-1] + 4 * sum(f[1:-1:2]) + 2 * sum(f[2:-1:2]))
    return 0.5 + math.copysign(s, x)


def t_inv(p: float, nu: float) -> float:
    lo, hi = -60.0, 60.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if t_cdf(mid, nu) < p else (lo, mid)
    return 0.5 * (lo + hi)


def simulate_losses(n: int, p: float, rho: float, recovery: float, trials: int, seed: int = 11,
                    nu: float | None = None) -> np.ndarray:
    """Pool loss fractions of n equal names, Gaussian copula (nu None) or Student-t copula with nu d.o.f."""
    rng = np.random.default_rng(seed)
    z = rng.standard_normal(trials)
    if nu is None:
        c = np.full(trials, ND.inv_cdf(p))
    else:
        w = nu / rng.chisquare(nu, trials)
        c = t_inv(p, nu) / np.sqrt(w)
    pz = ncdf((c - math.sqrt(rho) * z) / math.sqrt(1.0 - rho))
    return (1.0 - recovery) * rng.binomial(n, pz) / n


def default_correlation(p: float, rho: float) -> float:
    """Correlation of two names' default indicators over a horizon (Gaussian copula, equal p)."""
    c = ND.inv_cdf(p)
    joint = float(_W @ (ncdf((c - math.sqrt(rho) * _Z) / math.sqrt(1 - rho)) ** 2))
    return (joint - p * p) / (p * (1 - p))
