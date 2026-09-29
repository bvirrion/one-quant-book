"""One Quant Book 16, chapter 10: paying for skill, not luck (illustrative desk, $ millions).

Twenty traders, each running risk with an annual P&L volatility of 10; each has a true Sharpe ratio drawn from a
normal with mean 0.8 and standard deviation 0.4, so true expected P&L is 8 on average with a spread of 4 between
traders. Five years, 2,000 simulated desks. Pay rules: 15 per cent of positive P&L (formulaic); 15 per cent of P&L
above a capital charge of 1.95 (risk-adjusted: a 15 per cent hurdle on capital of 13); a pool of 15 per cent of the
desk's positive P&L split by shrunk skill (discretionary).
"""
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "code/firm/bonuspool"))
import firm_bonuspool as bp  # noqa: E402

N_TRADERS, YEARS, SIGMA, S_MEAN, S_SD, RATE = 20, 5, 10.0, 0.8, 0.4, 0.15
CHARGE = 0.15 * 13.0


def desk(rng, years=YEARS):
    s = rng.normal(S_MEAN, S_SD, N_TRADERS)
    pnl = s * SIGMA + SIGMA * rng.standard_normal((years, N_TRADERS))
    return s, pnl


def pay(pnl, rule):
    years = pnl.shape[0]
    if rule == "formulaic":
        return bp.formulaic(pnl, RATE)
    if rule == "risk-adjusted":
        return bp.risk_adjusted(pnl, np.full_like(pnl, 13.0), 0.15, RATE)
    if rule == "discretionary":
        out = np.zeros_like(pnl)
        for t in range(years):
            pool = RATE * max(pnl[t].sum(), 0.0)
            out[t] = bp.discretionary(pnl[: t + 1], pool, SIGMA, S_MEAN * SIGMA, S_SD * SIGMA)
        return out
    raise ValueError(rule)


RULES = ("formulaic", "risk-adjusted", "discretionary")


def correlations(n_desks=2000, seed=10, years=YEARS):
    """Mean cross-trader correlation of total pay over `years` with true Sharpe ratio, and of one year's pay."""
    rng = np.random.default_rng(seed)
    out = {r: [] for r in RULES}
    one = {r: [] for r in RULES}
    for _ in range(n_desks):
        s, pnl = desk(rng, years)
        for r in RULES:
            p = pay(pnl, r)
            with np.errstate(invalid="ignore", divide="ignore"):
                out[r].append(np.corrcoef(p.sum(0), s)[0, 1])
                one[r].append(np.corrcoef(p[0], s)[0, 1])
    return {r: (float(np.nanmean(out[r])), float(np.nanmean(one[r]))) for r in RULES}


def expected_formulaic(s):
    """E[RATE * max(X, 0)], X ~ N(s * SIGMA, SIGMA^2)."""
    mu = s * SIGMA
    z = mu / SIGMA
    phi = math.exp(-z * z / 2) / math.sqrt(2 * math.pi)
    return RATE * (mu * 0.5 * (1 + math.erf(z / math.sqrt(2))) + SIGMA * phi)


def luck_share_formulaic(n=200_000, seed=11):
    """Share of the variance of one year's formulaic pay across traders that is not explained by skill."""
    rng = np.random.default_rng(seed)
    s = rng.normal(S_MEAN, S_SD, n)
    x = s * SIGMA + SIGMA * rng.standard_normal(n)
    p = bp.formulaic(x, RATE)
    e = np.array([expected_formulaic(v) for v in s])
    return float(np.var(p - e) / np.var(p))


def hook():
    """Probabilities, for a trader with the desk's average skill, of a year at +20 or better and at -2 or worse."""
    mu = S_MEAN * SIGMA

    def cdf(v):
        return 0.5 * (1 + math.erf(v / math.sqrt(2)))
    return {"p_20_or_more": 1 - cdf((20 - mu) / SIGMA), "p_minus2_or_less": cdf((-2 - mu) / SIGMA),
            "pay_20": RATE * 20}


def retention(award=1.0, plan=None):
    plan = plan or bp.DeferralPlan(0.6, 4)
    return bp.unvested([award] * 6, plan, 5)


def corr_by_years(max_years=15, n_desks=400, seed=12):
    """Mean correlation of cumulative formulaic pay with skill after 1..max_years, and the linear closed form."""
    rng = np.random.default_rng(seed)
    acc = np.zeros(max_years)
    for _ in range(n_desks):
        s, pnl = desk(rng, max_years)
        p = np.cumsum(pay(pnl, "formulaic"), 0)
        acc += np.array([np.corrcoef(p[t], s)[0, 1] for t in range(max_years)])
    lin = [math.sqrt(S_SD ** 2 / (S_SD ** 2 + 1 / t)) for t in range(1, max_years + 1)]
    return acc / n_desks, np.array(lin)


def one_desk(seed=13):
    rng = np.random.default_rng(seed)
    s, pnl = desk(rng)
    return s, pay(pnl, "formulaic").sum(0)
