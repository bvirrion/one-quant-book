"""firm.payoffer -- a pay package as data, valued from the employee's side (build of One Quant Book 17, chapter 13).

A package is a base salary, a variable award each year, and the terms that decide what the award is worth: the share
deferred, the vesting schedule of the deferred part and the instrument it is held in, what is forfeited on leaving
and whether the leaver is a good leaver, a sign-on bonus that is repaid if the employee leaves early, a guaranteed
minimum for the first award, and for a formulaic package a payout share of a book's profit and loss instead of a
discretionary award. The module simulates years of employment with a leaving hazard, and reports for each package the
distribution of the present value received, the expected value forfeited when leaving in each year, the certainty
equivalent under constant relative risk aversion (Book 4, chapter 9), and the buyout another employer must pay to make
a move in a given year neutral. Every parameter is the caller's: the chapter labels its offers illustrative. NumPy only.

Variable award in year t (paid at the end of the year):
    discretionary: B_t = median * exp(sigma * Z_t - 0)  (lognormal, median `median`), floored by the guarantee in year 1
    formulaic:     B_t = share * max(PnL_t, 0), PnL_t ~ Normal(pnl_mean, pnl_sd); a cut ends employment when
                   PnL_t < cut (the book is closed), with no award for that year
The deferred part (deferral * B_t) is held in an instrument with zero drift and volatility `inst_vol` and vests in equal
tranches over `vest_years` years after the award; on leaving, unvested tranches are forfeited unless `good_leaver`.

API (stable):
    Package(name, base, median=0, sigma=0, deferral=0, vest_years=0, inst_vol=0, good_leaver=False,
            sign_on=0, sign_on_years=0, guarantee=0, share=0, pnl_mean=0, pnl_sd=0, cut=None)
    simulate(pkg, years, hazard, rate, n, rng, leave_year=None) -> dict of arrays
        pv (present value received), leave (year of leaving, years+1 if stayed), forfeited (value forfeited at leaving,
        present value), unvested (value of unvested awards at the end of each year, n x years)
    summary(sim) -> mean, p10, p50, p90 of pv, and the mean forfeiture
    certainty_equivalent(pv, rra, wealth) -> the sure amount with the same expected CRRA utility of wealth + pv
    buyout(pkg, year, n, rng, rate) -> expected present value of the awards unvested at the end of `year`
"""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Package:
    name: str
    base: float
    median: float = 0.0          # discretionary award: median of the lognormal
    sigma: float = 0.0           # its log standard deviation
    deferral: float = 0.0        # share of each award deferred
    vest_years: int = 0          # deferred part vests in equal tranches over this many years
    inst_vol: float = 0.0        # volatility of the instrument the deferred part is held in
    good_leaver: bool = False    # True: unvested awards keep vesting after a voluntary move
    sign_on: float = 0.0         # paid at the start, repaid in full if leaving within sign_on_years
    sign_on_years: int = 0
    guarantee: float = 0.0       # floor on the first year's award
    share: float = 0.0           # formulaic payout share of a book's profit and loss
    pnl_mean: float = 0.0
    pnl_sd: float = 0.0
    cut: float | None = None     # a year's loss beyond which the book is closed and employment ends


def _awards(pkg, years, n, rng):
    """Awards (n x years) and involuntary end year (years+1 when never cut)."""
    end = np.full(n, years + 1)
    if pkg.share:
        pnl = rng.normal(pkg.pnl_mean, pkg.pnl_sd, (n, years))
        aw = pkg.share * np.maximum(pnl, 0.0)
        if pkg.cut is not None:
            hit = pnl < pkg.cut
            first = np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, years + 1)
            end = first
    else:
        aw = pkg.median * np.exp(pkg.sigma * rng.standard_normal((n, years)))
    if pkg.guarantee:
        aw[:, 0] = np.maximum(aw[:, 0], pkg.guarantee)
    return aw, end


def simulate(pkg: Package, years: int, hazard: float, rate: float, n: int, rng, leave_year=None):
    aw, cut_end = _awards(pkg, years, n, rng)
    if leave_year is None:
        vol_leave = np.where(rng.random((n, years)) < hazard, 1, 0)
        vl = np.where(vol_leave.any(axis=1), vol_leave.argmax(axis=1) + 1, years + 1)
    else:
        vl = np.full(n, leave_year)
    leave = np.minimum(vl, cut_end)          # employment ends at the end of year `leave` (years+1: stayed)
    cut = (cut_end <= vl) & (cut_end <= years)  # involuntary end by a cut (no award that year)
    disc = (1.0 + rate) ** -np.arange(1, years + 1)
    horizon = years + pkg.vest_years
    ddisc = (1.0 + rate) ** -np.arange(1, horizon + 1)
    pv = np.full(n, pkg.sign_on, dtype=float)
    early = leave <= pkg.sign_on_years
    pv -= np.where(early, pkg.sign_on * (1.0 + rate) ** -np.minimum(leave, years).astype(float), 0.0)
    forfeited = np.zeros(n)
    unvested = np.zeros((n, years))
    for t in range(1, years + 1):
        working = leave >= t
        paid_award = working & ~((leave == t) & cut)
        pv += np.where(working, pkg.base * disc[t - 1], 0.0)
        a = np.where(paid_award, aw[:, t - 1], 0.0)
        pv += (1.0 - pkg.deferral) * a * disc[t - 1]
        if pkg.deferral and pkg.vest_years:
            tranche = pkg.deferral * a / pkg.vest_years
            for k in range(1, pkg.vest_years + 1):
                s = t + k                       # vests at the end of year s
                ret = np.exp(pkg.inst_vol * np.sqrt(k) * rng.standard_normal(n) - 0.5 * pkg.inst_vol ** 2 * k)
                value = tranche * ret
                kept = (leave >= s) | (pkg.good_leaver & ~cut) | (leave == years + 1)
                pv += np.where(kept, value * ddisc[s - 1], 0.0)
                forfeited += np.where(kept, 0.0, value * ddisc[s - 1])
                for e in range(t, min(s, years + 1)):
                    unvested[:, e - 1] += tranche     # at grant value, still unvested at the end of year e
    return dict(pv=pv, leave=leave, forfeited=forfeited, unvested=unvested, cut=cut)


def summary(sim):
    pv = sim["pv"]
    return dict(mean=float(pv.mean()), p10=float(np.percentile(pv, 10)), p50=float(np.percentile(pv, 50)),
                p90=float(np.percentile(pv, 90)), forfeited=float(sim["forfeited"].mean()),
                left=float((sim["leave"] <= sim["unvested"].shape[1]).mean()))


def certainty_equivalent(pv, rra: float, wealth: float) -> float:
    w = wealth + np.asarray(pv, dtype=float)
    if np.any(w <= 0):
        raise ValueError("wealth plus outcome must be positive")
    if abs(rra - 1.0) < 1e-12:
        return float(np.exp(np.log(w).mean()) - wealth)
    eu = np.mean(w ** (1.0 - rra))
    return float(eu ** (1.0 / (1.0 - rra)) - wealth)


def buyout(pkg: Package, year: int, n: int, rng, rate: float = 0.0) -> float:
    """Expected value, at grant value, of the awards still unvested at the end of `year` for someone who stayed."""
    sim = simulate(pkg, year, 0.0, rate, n, rng, leave_year=year + 1)
    return float(sim["unvested"][:, year - 1].mean())
