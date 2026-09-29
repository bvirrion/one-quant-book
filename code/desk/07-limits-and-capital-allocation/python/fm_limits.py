"""One Quant Book 16, chapter 7: limits and capital allocation (illustrative firm, $ millions a year).

Six strategies with normal annual P&L (means and volatilities below; correlation 0.2 among all but trend, which is
uncorrelated) plus a crash that hits in 5 per cent of years: stat arb, credit carry and volatility selling lose, trend
following gains. 200,000 simulated years; economic capital is the 99 per cent expected shortfall; hurdle rate 15 per
cent.
"""
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/limitalloc"))
import firm_limitalloc as la  # noqa: E402

NAMES = ("stat arb", "trend", "credit carry", "vol selling", "macro", "market making")
MU = np.array([11.0, 12.0, 8.0, 12.0, 6.0, 10.0])
SIGMA = np.array([25.0, 30.0, 20.0, 22.0, 20.0, 8.0])
CRASH = np.array([-40.0, 30.0, -60.0, -110.0, -5.0, -6.0])   # added in a crash year
P_CRASH = 0.05
ALPHA = 0.99
H_K = 0.15
N = 200_000


def corr():
    c = np.full((6, 6), 0.2)
    c[1, :] = c[:, 1] = 0.0
    np.fill_diagonal(c, 1.0)
    return c


def scenarios(n=N, seed=7):
    """Annual P&L scenarios (n, 6); crash years add CRASH and remove its expected value from the mean, so that
    MU stays each strategy's expected P&L."""
    rng = np.random.default_rng(seed)
    cov = np.outer(SIGMA, SIGMA) * corr()
    z = rng.multivariate_normal(np.zeros(6), cov, n)
    crash = rng.random(n) < P_CRASH
    return MU - P_CRASH * CRASH + z + np.outer(crash, CRASH)


def allocation(n=N, seed=7):
    s = scenarios(n, seed)
    a = la.allocate_capital(s, ALPHA)
    mu = s.mean(0)
    out = {"mu": mu, "firm_es": a["firm"], "firm_mu": mu.sum()}
    for k in ("standalone", "euler", "incremental"):
        out[k] = a[k]
        out["raroc_" + k] = la.raroc(mu, a[k])
    return out


def scaled(n=N, seed=7):
    """Best scales in [0, 2] at the hurdle, on a smaller sample for speed."""
    s = scenarios(n, seed)
    w = la.best_scales(s, ALPHA, H_K, 0.0, 2.0)
    before = s.sum(1).mean() - H_K * la.es(s.sum(1), ALPHA)
    after = (s @ w).mean() - H_K * la.es(s @ w, ALPHA)
    return w, before, after


def framework(temp=()):
    """Desk limits: daily VaR soft/hard 6/8 per strategy, firm 25/30."""
    kids = tuple(la.Node(nm, (la.Limit("var", 6.0, 8.0), la.Limit("loss", 15.0, 20.0)),
                         temp=temp if nm == "vol selling" else ()) for nm in NAMES)
    return la.Node("firm", (la.Limit("var", 25.0, 30.0),), kids)


def daily_var_exposures():
    """One day: each strategy's daily 99 per cent VaR from its volatility (2.326 sigma / sqrt(252)), vol selling
    doubled after a volatility spike."""
    v = 2.326 * SIGMA / np.sqrt(252)
    v[3] *= 2.0
    return {nm: {"var": float(x)} for nm, x in zip(NAMES, v, strict=True)}


def value_added(n=N, seed=7):
    """Expected P&L less the capital charge (H_K times allocated capital), by allocation."""
    a = allocation(n, seed)
    return {k: a["mu"] - H_K * a[k] for k in ("standalone", "euler")}


def var_path(days=60):
    """An illustrative 60-day path of the vol-selling strategy's daily VaR: calm at 3.2, a volatility spike from day
    20 that peaks at 7.6 on day 30, then decays; a temporary increase of 4 on the hard limit from day 25 to day 40."""
    t = np.arange(1, days + 1)
    spike = 4.4 * np.exp(-((t - 30) / 6.0) ** 2) * (t >= 20)
    v = 3.2 + spike
    hard = np.where((t >= 25) & (t <= 40), 12.0, 8.0)
    return t, v, hard
