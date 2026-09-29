"""firm.bonuspool -- sizing a bonus pool, allocating it, and deferring it (build of One Quant Book 16, chapter 10).

Pool. A pool is a share of revenue, or of net profit after costs and a capital charge (chapter 7), floored at zero.
Allocation. Three rules share a year's pool among traders:
  formulaic       each trader's positive P&L times a rate (the pool is then whatever the rate produces);
  risk-adjusted   positive P&L less a capital charge on the trader's capital, times a rate;
  discretionary   in proportion to a shrunk estimate of each trader's skill: cumulative P&L per year pulled towards the
                  desk average by the weight a normal prior on skill gives it (a James--Stein style estimate), which is
                  what a disciplined judgement of "who is good" approximates.
Deferral. A deferral plan pays a share in cash now and vests the rest pro rata over some years; unvested awards can be
reduced (malus) or, once paid, recovered (clawback); a competitor that hires a trader pays the unvested balance (a
deferral buyout). NumPy only.

API (stable):
    pool_from_profit(revenue, costs, capital_charge, share) ; pool_from_revenue(revenue, share)
    formulaic(pnl, rate) ; risk_adjusted(pnl, capital, h_k, rate)
    shrunk_skill(pnl_history, sigma, prior_mean, prior_sd)
    discretionary(pnl_history, pool, sigma, prior_mean, prior_sd)
    DeferralPlan(cash_share, years) ; schedule(award, plan) -> payments by year (index 0 = award year)
    unvested(awards_by_year, plan, now) ; malus(awards_by_year, plan, now, share)
    luck_share_linear(skill_sd, noise_sd, years) ; years_for_correlation(skill_sd, noise_sd, rho)
"""
from dataclasses import dataclass

import numpy as np


def pool_from_profit(revenue: float, costs: float, capital_charge: float, share: float) -> float:
    return share * max(revenue - costs - capital_charge, 0.0)


def pool_from_revenue(revenue: float, share: float) -> float:
    return share * max(revenue, 0.0)


def formulaic(pnl, rate: float):
    return rate * np.maximum(np.asarray(pnl, float), 0.0)


def risk_adjusted(pnl, capital, h_k: float, rate: float):
    return rate * np.maximum(np.asarray(pnl, float) - h_k * np.asarray(capital, float), 0.0)


def shrunk_skill(pnl_history, sigma: float, prior_mean: float, prior_sd: float):
    """pnl_history (years, traders), annual P&L in units where each trader's annual noise has sd `sigma`.
    Posterior mean of each trader's expected annual P&L under a normal prior N(prior_mean, prior_sd^2)."""
    h = np.atleast_2d(np.asarray(pnl_history, float))
    n = h.shape[0]
    w = prior_sd ** 2 / (prior_sd ** 2 + sigma ** 2 / n)
    return prior_mean + w * (h.mean(0) - prior_mean)


def discretionary(pnl_history, pool: float, sigma: float, prior_mean: float, prior_sd: float):
    s = np.maximum(shrunk_skill(pnl_history, sigma, prior_mean, prior_sd), 0.0)
    tot = s.sum()
    return pool * s / tot if tot > 0 else np.zeros_like(s)


@dataclass(frozen=True)
class DeferralPlan:
    cash_share: float = 0.6
    years: int = 4


def schedule(award: float, plan: DeferralPlan) -> np.ndarray:
    """Payments of one award: the cash share at once, the rest in equal parts in each of the next `years` years."""
    out = np.zeros(plan.years + 1)
    out[0] = plan.cash_share * award
    out[1:] = (1 - plan.cash_share) * award / plan.years
    return out


def unvested(awards_by_year, plan: DeferralPlan, now: int) -> float:
    """Unvested balance at the end of year `now` (after that year's vesting), awards_by_year[t] granted in year t."""
    bal = 0.0
    for t, a in enumerate(awards_by_year[: now + 1]):
        s = schedule(a, plan)
        bal += s[now - t + 1:].sum() if now - t + 1 <= plan.years else 0.0
    return bal


def malus(awards_by_year, plan: DeferralPlan, now: int, share: float) -> float:
    """Amount forfeited when `share` of the unvested balance is cancelled at the end of year `now`."""
    return share * unvested(awards_by_year, plan, now)


def luck_share_linear(skill_sd: float, noise_sd: float, years: int = 1) -> float:
    """Share of the cross-sectional variance of average P&L over `years` that comes from luck, not skill."""
    v_luck = noise_sd ** 2 / years
    return v_luck / (skill_sd ** 2 + v_luck)


def years_for_correlation(skill_sd: float, noise_sd: float, rho: float) -> float:
    """Years of P&L after which average P&L correlates with skill at rho: rho^2 = s^2 / (s^2 + n^2 / T)."""
    return noise_sd ** 2 / (skill_sd ** 2 * (1 / rho ** 2 - 1))
