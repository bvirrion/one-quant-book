"""Multi-asset options (Book 5, Chapter 17): prices against correlation for a three-share note, the implied
correlation of a synthetic 20-stock index built on chapter 9's surface, a local correlation fitted to the
index skew, a dispersion trade, and the quanto adjustment. Zero rates unless stated."""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
for comp in ("bs", "svi", "fwdvar", "multiasset"):
    sys.path.insert(0, str(ROOT / f"code/firm/{comp}"))
from firm_bs import black, implied_vol  # noqa: E402
from firm_fwdvar import log_strip_variance  # noqa: E402
from firm_multiasset import (  # noqa: E402
    basket_moment_match,
    basket_payoff,
    best_of_payoff,
    correlated_paths,
    equicorrelation,
    implied_correlation,
    index_variance,
    local_correlation_paths,
    quanto_forward,
    realised_correlation,
    worst_of_digital,
    worst_of_payoff,
)
from firm_svi import ssvi  # noqa: E402

# ---------------------------------------------------------------- three shares
VOLS3 = np.array([0.25, 0.30, 0.35])
RHOS = (0.0, 0.2, 0.4, 0.6, 0.8, 0.95)


def three_share_prices(t: float = 1.0, rhos=RHOS, n: int = 100_000) -> list[dict]:
    rows = []
    for rho in rhos:
        p = correlated_paths(np.ones(3), VOLS3, equicorrelation(3, rho), [t], n_paths=n, seed=17)
        rows.append({"rho": rho, "worst_digital": float(worst_of_digital(p, 0.7).mean()),
                     "worst_put": float(worst_of_payoff(p, 1.0, "P").mean()),
                     "best_call": float(best_of_payoff(p, 1.0, "C").mean()),
                     "basket_call": float(basket_payoff(p, np.ones(3) / 3, 1.0).mean()),
                     "basket_mm": basket_moment_match(np.ones(3) / 3, np.ones(3), VOLS3, equicorrelation(3, rho),
                                                      t, 1.0)})
    return rows


# ---------------------------------------------------------------- a synthetic 20-stock index on chapter 9's surface
N_STOCKS = 20
WEIGHTS = np.full(N_STOCKS, 1 / N_STOCKS)
MEMBER_VOLS = np.linspace(0.22, 0.36, N_STOCKS)
INDEX_STRIKES = (90.0, 100.0, 110.0)


def index_vol(k: float, t: float = 1.0) -> float:
    """The index's smile: chapter 9's surface (spot 100)."""
    theta = (0.20 - 0.06 * math.exp(-t / 0.5)) ** 2 * t
    return math.sqrt(float(ssvi(math.log(k / 100.0), theta, -0.6, 1.0, 0.45)) / t)


def correlation_by_strike(t: float = 1.0) -> dict[float, float]:
    """Implied correlation at each index strike, the members' smiles being flat."""
    return {k: implied_correlation(index_vol(k, t), WEIGHTS, MEMBER_VOLS) for k in INDEX_STRIKES}


def variance_implied_correlation(t: float = 1.0) -> dict:
    """Implied correlation in variance-swap terms: the index's strip variance against the members'."""
    vs = math.sqrt(log_strip_variance(lambda k: index_vol(100.0 * math.exp(k), t), t))
    own = float(np.sum((WEIGHTS * MEMBER_VOLS) ** 2))
    cross = float(np.sum(WEIGHTS * MEMBER_VOLS)) ** 2 - own
    return {"index_vs": vs, "rho": implied_correlation(vs, WEIGHTS, MEMBER_VOLS), "own": own, "cross": cross}


# ---------------------------------------------------------------- local correlation
def rho_quadratic(a: float, b: float, c: float):
    return lambda t, x: a - b * x + c * x * x


def lc_index_vols(a: float, b: float, c: float = 0.0, n: int = 40_000, seed: int = 17, steps: int = 52) -> np.ndarray:
    """Index implied volatilities at the three strikes under local correlation rho(x) = a - b x + c x^2, with x the
    index's log-moneyness (common random numbers across calls, so the calibration sees a smooth function)."""
    p = local_correlation_paths(np.full(N_STOCKS, 100.0), MEMBER_VOLS, WEIGHTS, rho_quadratic(a, b, c), [1.0],
                                n_paths=n, seed=seed, steps_per_date=steps)
    idx = p[:, -1, :] @ WEIGHTS
    out = []
    for k in INDEX_STRIKES:
        right = "C" if k >= 100 else "P"
        pay = np.maximum(idx - k, 0) if right == "C" else np.maximum(k - idx, 0)
        out.append(implied_vol(float(pay.mean()), float(idx.mean()), k, 1.0, 1.0, right))
    return np.array(out)


def calibrate_local_correlation(iters: int = 8) -> dict:
    """Newton steps on (a, b, c) to match the index volatilities at 90, 100 and 110."""
    target = np.array([index_vol(k) for k in INDEX_STRIKES])
    rc = correlation_by_strike()
    z = np.array([rc[100.0], (rc[90.0] - rc[110.0]) / (2 * math.log(1.1)), 0.0])
    for _ in range(iters):
        base = lc_index_vols(*z)
        err = base - target
        if np.max(np.abs(err)) < 2e-4:
            break
        h = 0.01
        jac = np.column_stack([(lc_index_vols(*(z + h * e)) - base) / h for e in np.eye(3)])
        z = z + np.linalg.solve(jac, -err)
    fitted = lc_index_vols(*z)
    const = lc_index_vols(rc[100.0], 0.0)
    return {"a": float(z[0]), "b": float(z[1]), "c": float(z[2]), "target": target, "fitted": fitted,
            "constant": const}


# ---------------------------------------------------------------- dispersion
def dispersion(drop: float = 0.15, vega_notional: float = 100_000.0, n: int = 4000, seed: int = 17) -> dict:
    """Short index variance (vega notional 100,000 at the strip's strike), long member variance in the amounts
    that cancel the index's sensitivity to each member's variance at the implied correlation; members realise
    their implied volatilities on average and the correlation realises `drop` below implied. Variance in
    percent squared; one year of daily returns simulated n times."""
    iv = variance_implied_correlation()
    k_idx = 100 * iv["index_vs"]
    n_var = vega_notional / (2 * k_idx)
    rho_i = iv["rho"]
    s = 100 * MEMBER_VOLS
    w = WEIGHTS
    # d(index var)/d(member var_i) at fixed correlation: w_i^2 (1 - rho) + rho w_i sum_j w_j s_j / s_i
    sens = w * w * (1 - rho_i) + rho_i * w * float(w @ s) / s
    member_notional = n_var * sens
    k_i2 = s * s
    k_idx2 = k_idx * k_idx
    rho_r = rho_i - drop
    theory = n_var * drop * 1e4 * iv["cross"]
    rng = np.random.default_rng(seed)
    low = np.linalg.cholesky(equicorrelation(N_STOCKS, rho_r))
    pnl, corr = np.empty(n), np.empty(n)
    for j in range(n):
        z = rng.standard_normal((252, N_STOCKS)) @ low.T
        r = MEMBER_VOLS * math.sqrt(1 / 252) * z - 0.5 * MEMBER_VOLS ** 2 / 252
        ri = np.log(np.exp(r) @ w)                      # daily index return, weights rebalanced daily
        var_i = 1e4 * 252 * np.mean(r * r, axis=0)
        var_idx = 1e4 * 252 * float(np.mean(ri * ri))
        pnl[j] = n_var * (k_idx2 - var_idx) + float(member_notional @ (var_i - k_i2))
        corr[j] = realised_correlation(r, w)
    return {"k_idx": k_idx, "n_var": n_var, "rho_implied": rho_i, "rho_realised": rho_r, "theory": theory,
            "pnl": pnl, "corr": corr, "member_notional": member_notional}


# ---------------------------------------------------------------- quanto
def quanto_example(sigma_s: float = 0.20, sigma_x: float = 0.10, t: float = 1.0, n: int = 200_000) -> list[dict]:
    """A foreign index forward of 100 paid in domestic currency at a fixed rate: its fair level by correlation,
    analytically and by simulating the index under the domestic measure with the quanto drift."""
    rows = []
    for rho in (-0.6, -0.3, 0.0, 0.3, 0.6):
        p = correlated_paths([100.0], [sigma_s], [[1.0]], [t], n_paths=n, seed=21, quanto=(sigma_x, np.array([rho])))
        rows.append({"rho": rho, "analytic": quanto_forward(100.0, sigma_s, sigma_x, rho, t),
                     "mc": float(p[:, -1, 0].mean()), "se": float(p[:, -1, 0].std() / math.sqrt(n))})
    return rows


def quanto_call(rho: float = -0.3, sigma_s: float = 0.20, sigma_x: float = 0.10, t: float = 1.0) -> dict:
    fq = quanto_forward(100.0, sigma_s, sigma_x, rho, t)
    return {"quanto": black(fq, 100.0, t, 1.0, sigma_s, "C"), "plain": black(100.0, 100.0, t, 1.0, sigma_s, "C"),
            "fwd": fq}


def dispersion_vol_shift(shift_pts: float = 1.0) -> float:
    """Dispersion P&L (hedge amounts at implied) when correlation realises at implied and every member's
    volatility realises shift_pts above its implied level (no noise)."""
    iv = variance_implied_correlation()
    rho = iv["rho"]
    s, w = 100 * MEMBER_VOLS, WEIGHTS
    k_idx = 100 * iv["index_vs"]
    n_var = 100_000.0 / (2 * k_idx)
    member_notional = n_var * (w * w * (1 - rho) + rho * w * float(w @ s) / s)
    s2 = s + shift_pts
    return n_var * (k_idx ** 2 - index_variance(w, s2, rho)) + float(member_notional @ (s2 ** 2 - s ** 2))


def worst_digital_local_corr(coef: tuple[float, float, float], n: int = 100_000) -> float:
    """The three-share worst-of digital (all above 70% in a year) when their common correlation follows the
    synthetic index's fitted local correlation, read from the three shares' own equally weighted basket."""
    p = local_correlation_paths(np.ones(3), VOLS3, np.ones(3) / 3, rho_quadratic(*coef), [1.0], n_paths=n, seed=17,
                                steps_per_date=52)
    return float(worst_of_digital(p, 0.7).mean())
