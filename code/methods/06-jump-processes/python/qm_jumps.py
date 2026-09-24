"""Chapter 6 of Book 4: jump processes.

The day of the hook in standard deviations; a jump-diffusion calibrated so that a one-day fall of
20% or more is a once-in-fifty-years event at the market's variance; the tail it implies; the
term structure of kurtosis; characteristic functions checked against simulated paths."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/levy"))
from firm_levy import merton_cumulants, psi_merton, simulate_merton

YEAR = 252
SD_DAY = 0.0098                     # daily standard deviation of S&P 500 returns, 1950-2012 (ledger F2)
SIGMAS_1987 = 20.98                 # 19 October 1987 in those standard deviations (ledger F2)
LAM, SIG_J = 0.5, 0.05              # the problem's choices: a jump every two years, jump sd 5%
DROP, EVERY = 0.20, 50              # a fall of 20% or more once in fifty years


def Phi(x: float) -> float:
    return 0.5 * math.erfc(-x / math.sqrt(2))


def log10_normal_tail(z: float) -> float:
    """log10 P(Z > z) for large z, by the asymptotic series of the Mills ratio."""
    ln = -0.5 * z * z - math.log(z * math.sqrt(2 * math.pi)) + math.log(1 - 1 / z**2 + 3 / z**4)
    return ln / math.log(10)


def day_tail(x: float, mu_j: float, sig_c: float, lam: float = LAM, sig_j: float = SIG_J, k_max: int = 8) -> float:
    """P(one day's return <= -x) for the jump-diffusion: a Poisson mixture of normals."""
    lam_d = lam / YEAR
    out = 0.0
    for k in range(k_max + 1):
        pk = math.exp(-lam_d) * lam_d**k / math.factorial(k)
        s = math.sqrt(sig_c**2 / YEAR + k * sig_j**2)
        out += pk * Phi((-x - k * mu_j) / s)
    return out


def calibrate(target_per_day: float = 1 / (EVERY * YEAR)) -> dict:
    """Find the mean jump size mu_j (negative) such that P(day <= -20%) hits the target, with the
    diffusion volatility adjusted so that the daily variance stays SD_DAY^2."""
    def sig_c(mu_j):
        v = SD_DAY**2 - LAM / YEAR * (mu_j**2 + SIG_J**2)
        return math.sqrt(v * YEAR) if v > 0 else float("nan")

    lo, hi = -0.20, 0.0
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        sc = sig_c(mid)
        if math.isnan(sc) or day_tail(DROP, mid, sc) > target_per_day:
            lo = mid
        else:
            hi = mid
    mu_j = 0.5 * (lo + hi)
    return {"mu_j": mu_j, "sig_c": sig_c(mu_j), "tail": day_tail(DROP, mu_j, sig_c(mu_j))}


def kurtosis_term(mu_j: float, sig_c: float, horizons=(1, 2, 5, 10, 21, 63, 126, 252)) -> list[tuple]:
    """Excess kurtosis kappa_4 / kappa_2^2 of the return over h days: theory (1/h decay) and simulation."""
    k = merton_cumulants(0.0, sig_c, LAM, mu_j, SIG_J)
    rows = []
    for i, h in enumerate(horizons):
        t = h / YEAR
        theory = k[3] / (t * k[1] ** 2)
        x = simulate_merton(t, 1, 400_000, seed=50 + i, mu=0.0, sigma=sig_c, lam=LAM, mu_j=mu_j, sigma_j=SIG_J)[:, 1]
        x = x - x.mean()
        sim = float(np.mean(x**4) / np.mean(x**2) ** 2 - 3)
        rows.append((h, theory, sim))
    return rows


def charfn_check(mu_j: float, sig_c: float, t: float = 21 / YEAR, n: int = 200_000, seed: int = 7) -> list[tuple]:
    """Empirical characteristic function of X_t from simulated paths against exp(t psi(u))."""
    x = simulate_merton(t, 1, n, seed, 0.0, sig_c, LAM, mu_j, SIG_J)[:, 1]
    rows = []
    for u in np.linspace(0, 40, 41):
        emp = np.mean(np.exp(1j * u * x))
        th = np.exp(t * psi_merton(u, 0.0, sig_c, LAM, mu_j, SIG_J))
        rows.append((float(u), float(emp.real), float(th.real), float(emp.imag), float(th.imag)))
    return rows


def problem() -> dict:
    c = calibrate()
    k = merton_cumulants(0.0, c["sig_c"], LAM, c["mu_j"], SIG_J)
    t_day, t_month = 1 / YEAR, 21 / YEAR
    return {
        "z_1987": SIGMAS_1987, "drop_1987": SIGMAS_1987 * SD_DAY,
        "log10_p_normal": log10_normal_tail(SIGMAS_1987),
        "log10_p_normal_20": log10_normal_tail(DROP / SD_DAY),
        "mu_j": c["mu_j"], "sig_c": c["sig_c"], "tail_per_day": c["tail"], "years_between": 1 / (c["tail"] * YEAR),
        "jump_var_share": LAM * (c["mu_j"] ** 2 + SIG_J**2) / (YEAR * SD_DAY**2),
        "kurt_day": k[3] / (t_day * k[1] ** 2), "kurt_month": k[3] / (t_month * k[1] ** 2),
        "skew_day": k[2] / (math.sqrt(t_day) * k[1] ** 1.5),
        "p_jump_day": 1 - math.exp(-LAM / YEAR),
        "p_10pct_jd": day_tail(0.10, c["mu_j"], c["sig_c"]), "p_10pct_normal": Phi(-0.10 / SD_DAY),
        "annual_vol": SD_DAY * math.sqrt(YEAR),
        "drift_correction": LAM * (math.exp(c["mu_j"] + 0.5 * SIG_J**2) - 1),
    }


def matched_models() -> dict:
    """Variance gamma and normal inverse Gaussian parameters with the market's daily variance."""
    var_year = SD_DAY**2 * YEAR
    theta, nu = -0.1, 0.013                      # one-day excess kurtosis about 3 nu 252 = 10
    sigma_vg = math.sqrt(var_year - nu * theta**2)
    alpha, beta = 58.0, -11.6                     # one-day excess kurtosis about 11
    gam = math.sqrt(alpha**2 - beta**2)
    delta = var_year * gam**3 / alpha**2
    return {"vg": (theta, sigma_vg, nu), "nig": (alpha, beta, delta)}


def densities(n: int = 2_000_000, seed: int = 9) -> list[tuple]:
    """Histogram densities (per percentage point) of one day's log return under four models."""
    from firm_levy import simulate_nig, simulate_vg

    c = calibrate()
    m = matched_models()
    t = 1 / YEAR
    draws = {
        "gauss": np.random.default_rng(seed).standard_normal(n) * SD_DAY,
        "jd": simulate_merton(t, 1, n, seed + 1, 0.0, c["sig_c"], LAM, c["mu_j"], SIG_J)[:, 1],
        "vg": simulate_vg(t, 1, n, seed + 2, *m["vg"])[:, 1],
        "nig": simulate_nig(t, 1, n, seed + 3, *m["nig"])[:, 1],
    }
    edges = np.arange(-25.25, 8.26, 0.5)
    mids = 0.5 * (edges[1:] + edges[:-1])
    hist = {k: np.histogram(100 * (v - v.mean()), bins=edges)[0] / (n * 0.5) for k, v in draws.items()}
    keys = ("gauss", "jd", "vg", "nig")
    return [(float(mids[i]),) + tuple(float(hist[k][i]) for k in keys) for i in range(mids.size)]
