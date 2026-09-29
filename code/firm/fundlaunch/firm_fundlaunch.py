"""firm.fundlaunch -- the economics of launching a fund: costs, fees net of a seeder's revenue share, the break-even
size, a track-record-driven inflow model, the probability of reaching a target size, and the seed deal's value to
both sides (build of One Quant Book 16, chapter 25).

Fees per year come from firm.fees (Book 1): a management fee on opening assets and a performance fee above the
high-water mark. The seeder takes a share of the manager's gross fee revenue. Inflows each month are a rate on the
assets times a logistic function of the track record's t-statistic (the Sharpe ratio times the square root of its
length in years); investors redeem a share of assets after a drawdown beyond a limit.

API (stable):
    Launch(...) ; annual_fees(aum, gross, terms) ; breakeven_aum(launch, gross)
    tstat(sharpe, years) ; years_for_t(sharpe, t)
    simulate(launch, seed, n_paths, months) -> (aum paths, fee paths) ; prob_reach(aum, target, months)
    first_month(aum, target) ; manager_value(aum, fees, launch, rate) ; seed_value(fee_paths, share, rate)
"""
import math
import pathlib
import sys
from dataclasses import dataclass

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "fees"))
import firm_fees as ff  # noqa: E402


@dataclass(frozen=True)
class Launch:
    fixed_costs: float = 2.2        # $ million a year: people, administrator, audit, legal, data, technology
    variable_bp: float = 5.0        # costs in basis points of assets
    mgmt: float = 0.015
    perf: float = 0.20
    revenue_share: float = 0.20     # the seeder's share of gross fee revenue
    seed: float = 50.0              # $ million at launch
    true_sharpe: float = 1.0
    vol: float = 0.10               # annual volatility of gross returns
    inflow_rate: float = 0.04       # monthly inflow as a share of assets at full investor confidence
    t_mid: float = 2.0              # t-statistic at which investor confidence is one half
    dd_limit: float = 0.10          # drawdown beyond which investors redeem
    dd_redeem: float = 0.10         # share of assets redeemed in a month past the limit


def annual_fees(aum, gross, terms):
    """Management and performance fees on `aum` over a year with gross return `gross` (firm.fees, one period)."""
    _, m, p = ff.accrue(terms, ff.InvestorState(1.0, 1.0), gross)
    return aum * (m + p)


def breakeven_aum(launch, gross):
    """Assets at which fees net of the revenue share cover fixed and variable costs, for an expected gross return."""
    terms = ff.FeeTerms(mgmt=launch.mgmt, perf=launch.perf)
    per_dollar = annual_fees(1.0, gross, terms) * (1 - launch.revenue_share) - launch.variable_bp * 1e-4
    return launch.fixed_costs / per_dollar if per_dollar > 0 else math.inf


def tstat(sharpe, years):
    return sharpe * math.sqrt(years)


def years_for_t(sharpe, t=2.0):
    return (t / sharpe) ** 2


def simulate(launch, seed=0, n_paths=2000, months=60):
    """Monthly assets and the manager's net fee revenue (after the revenue share) on each path."""
    rng = np.random.default_rng(seed)
    mu = launch.true_sharpe * launch.vol / 12
    sd = launch.vol / math.sqrt(12)
    aum = np.full(n_paths, launch.seed)
    peak = np.ones(n_paths)
    nav = np.ones(n_paths)
    sum_r = np.zeros(n_paths)
    sum_r2 = np.zeros(n_paths)
    out_a, out_f = np.zeros((n_paths, months)), np.zeros((n_paths, months))
    for m in range(months):
        r = mu + sd * rng.standard_normal(n_paths)
        sum_r += r
        sum_r2 += r * r
        k = m + 1
        mean = sum_r / k
        var = np.maximum(sum_r2 / k - mean ** 2, 1e-12) if k > 1 else np.full(n_paths, sd ** 2)
        sr = mean / np.sqrt(var) * math.sqrt(12)
        t = sr * math.sqrt(k / 12)
        conf = 1 / (1 + np.exp(-np.clip((t - launch.t_mid) * 2, -50, 50))) if k >= 6 else np.zeros(n_paths)
        fee = aum * (launch.mgmt / 12 + launch.perf * np.maximum(r, 0.0)) * (1 - launch.revenue_share)
        nav *= 1 + r
        peak = np.maximum(peak, nav)
        dd = 1 - nav / peak
        flow = aum * (launch.inflow_rate * conf - launch.dd_redeem * (dd > launch.dd_limit))
        aum = np.maximum(aum * (1 + r) + flow, 0.0)
        out_a[:, m], out_f[:, m] = aum, fee
    return out_a, out_f


def prob_reach(aum_paths, target, months):
    return float((aum_paths[:, :months].max(axis=1) >= target).mean())


def first_month(aum_paths, target):
    """Month (1-based) each path first reaches the target, or 0 if it never does."""
    hit = aum_paths >= target
    return np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, 0)


def manager_value(aum_paths, fee_paths, launch, rate=0.08):
    """Present value to the manager of net fees less fixed and variable costs, averaged over paths."""
    months = fee_paths.shape[1]
    disc = (1 + rate) ** (-np.arange(1, months + 1) / 12)
    profit = fee_paths - launch.fixed_costs / 12 - aum_paths * launch.variable_bp * 1e-4 / 12
    return float((profit * disc).sum(axis=1).mean())


def seed_value(fee_paths, share, rate=0.08):
    """Present value of the revenue share the seeder receives: share/(1-share) times the manager's net fees."""
    months = fee_paths.shape[1]
    disc = (1 + rate) ** (-np.arange(1, months + 1) / 12)
    return float((fee_paths * share / (1 - share) * disc).sum(axis=1).mean())
