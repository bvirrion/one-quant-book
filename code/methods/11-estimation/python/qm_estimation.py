"""Chapter 11 of Book 4: estimation.

A strategy whose daily P&L is the average of five overlapping positions (each held five days), so
its P&L is autocorrelated: the naive standard error of its mean understates the truth by the square
root of the long-run variance factor. Maximum likelihood, misspecification and the sandwich on
fat-tailed data; the Sharpe ratio's standard error."""
from __future__ import annotations

import math
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[3] / "firm/estim"))
from firm_estim import long_run_variance, mean_se, mle, nw_lags, sharpe

N_DAYS, HOLD = 1260, 5            # five years; each day's position is held five days
MU_BP, SD_BP = 4.0, 42.0          # mean and standard deviation of daily P&L, basis points


def strategy_pnl(n: int = N_DAYS, seed: int = 1, hold: int = HOLD) -> np.ndarray:
    """Daily P&L (bp) = mean of the last `hold` independent position returns; mean MU_BP, sd SD_BP."""
    rng = np.random.default_rng(seed)
    e = rng.standard_normal(n + hold - 1) * SD_BP * math.sqrt(hold)
    pnl = np.convolve(e, np.ones(hold) / hold, mode="valid")
    return MU_BP + pnl


def lrv_factor(hold: int = HOLD) -> float:
    """Long-run variance over variance for an equal-weight moving average of length `hold`: sum of
    autocorrelations 1 + 2 sum (1 - k / hold) = hold."""
    return 1 + 2 * sum(1 - k / hold for k in range(1, hold))


def coverage(n_rep: int = 2000, seed0: int = 100) -> dict:
    """Share of 95% intervals for the mean daily P&L that contain the true 4 bp: iid SE vs Newey-West."""
    hit_iid = hit_nw = hit_nw_long = 0
    ts = []
    for k in range(n_rep):
        x = strategy_pnl(seed=seed0 + k)
        m = x.mean()
        hit_iid += abs(m - MU_BP) <= 1.96 * mean_se(x, "iid")
        hit_nw += abs(m - MU_BP) <= 1.96 * mean_se(x, "hac")
        hit_nw_long += abs(m - MU_BP) <= 1.96 * mean_se(x, "hac", lags=20)
        ts.append(m / mean_se(x, "iid"))
    return {"iid": int(hit_iid) / n_rep, "nw": int(hit_nw) / n_rep, "nw20": int(hit_nw_long) / n_rep,
            "pct": {k: 100 * int(v) / n_rep for k, v in (("iid", hit_iid), ("nw", hit_nw), ("nw20", hit_nw_long))},
            "t_mean": float(np.mean(ts))}


def student_t_loglik(theta, x):
    """Per-observation log-likelihood of a location-scale Student t with nu degrees of freedom."""
    m, log_s, log_nu = theta
    s, nu = math.exp(log_s), math.exp(log_nu)
    z = (x - m) / s
    c = math.lgamma((nu + 1) / 2) - math.lgamma(nu / 2) - 0.5 * math.log(nu * math.pi) - log_s
    return c - (nu + 1) / 2 * np.log1p(z * z / nu)


def normal_loglik(theta, x):
    m, log_s = theta
    s = math.exp(log_s)
    return -0.5 * math.log(2 * math.pi) - log_s - 0.5 * ((x - m) / s) ** 2


def misspecified_fit(n: int = 2000, seed: int = 3) -> dict:
    """Fit a normal model to Student-t(6) data by maximum likelihood: the Hessian and sandwich
    standard errors of the log-scale disagree; the sandwich is right."""
    rng = np.random.default_rng(seed)
    x = rng.standard_t(6, n)
    fit_n = mle(lambda t: normal_loglik(t, x), [0.0, 0.0])
    fit_t = mle(lambda t: student_t_loglik(t, x), [0.0, 0.0, math.log(5.0)])
    reps = []
    for k in range(400):
        y = np.random.default_rng(1000 + k).standard_t(6, n)
        reps.append(math.log(y.std()))
    return {"logsd_se_hessian": fit_n["se_hessian"][1], "logsd_se_sandwich": fit_n["se_sandwich"][1],
            "logsd_se_true": float(np.std(reps)), "nu_hat": math.exp(fit_t["theta"][2]),
            "scale_hat": math.exp(fit_t["theta"][1])}


def problem(seed: int = 189) -> dict:
    x = strategy_pnl(seed=seed)
    L = nw_lags(x.size)
    r = np.corrcoef(x[1:], x[:-1])[0, 1]
    ac = [float(np.corrcoef(x[k:], x[:-k])[0, 1]) for k in range(1, 7)]
    sh = sharpe(x)
    return {
        "mean": float(x.mean()), "sd": float(x.std(ddof=1)), "se_iid": mean_se(x, "iid"),
        "t_iid": float(x.mean() / mean_se(x, "iid")), "lags": L,
        "se_nw": mean_se(x, "hac"), "t_nw": float(x.mean() / mean_se(x, "hac")),
        "se_nw20": mean_se(x, "hac", lags=20), "rho1": float(r), "ac": ac, "lrv_factor": lrv_factor(),
        "se_true": SD_BP * math.sqrt(lrv_factor() / x.size),
        "t_true_expected": MU_BP / (SD_BP * math.sqrt(lrv_factor() / x.size)),
        "sr": sh["sr"], "sr_se_iid": sh["se_iid"], "sr_se_hac": sh["se_hac"],
        "lrv_ratio_hat": long_run_variance(x) / x.var(),
    }


def years_for_t(sr_annual: float, factor: float = 1.0, t: float = 2.0, periods: int = 252) -> float:
    """Years of data before an annual Sharpe ratio (annualised naively by sqrt(periods)) reaches t.

    With a long-run variance `factor` times the variance, the honest t-statistic after T years is
    SR * sqrt(T) / sqrt(factor * (1 + SR_1^2 / 2)), SR_1 the per-period ratio.
    """
    sr1 = sr_annual / np.sqrt(periods)
    return float(t**2 * factor * (1 + 0.5 * sr1**2) / sr_annual**2)
